import os
import json
import pprint
from collections import defaultdict
from ontology import Ontology
from ltf_util import LTF_util
from glob import glob

NA_FILLER = 'EMPTY_TBD'
Subtype_Type_Mapping = {
    "Create":"Create",
    "Diagnosis":"Medical",
    "Intervention":"Medical",
    "Vaccinate":"Medical",
    "Consume":"Life",
    "Die":"Life",
    "Illness":"Life",
    "Infect":"Life",
    "Injure":"Life",
    "ArtifactFailure":"ArtifactExistence",
    "DamageDestroy":"ArtifactExistence",
    "Shortage":"ArtifactExistence",
    "Collaborate":"Contact",
    "CommandOrder":"Contact",
    "CommitmentPromiseExpressIntent":"Contact",
    "Discussion":"Contact",
    "FuneralVigil":"Contact",
    "MediaStatement":"Contact",
    "Negotiate":"Contact",
    "Prevarication":"Contact",
    "PublicStatementInPerson":"Contact",
    "RequestAdvise":"Contact",
    "ThreatenCoerce":"Contact",
    "DiseaseOutbreak":"Disaster",
    "Artifact":"Manufacture",
    "TransportArtifact":"Movement",
    "TransportPerson":"Movement",
    "Transaction":"Transaction",
    "TransferMoney":"Transaction",
    "TransferOwnership":"Transaction",
    "ArrestJailDetain":"Justice",
    "InitiateJudicialProcess":"Justice",
    "Investigate":"Justice",
    "JudicialConsequences":"Justice",
}
def get_entities(doc_id, lines):
    entity_dict = {}
    for line in lines:
        if line.startswith('T'):
            parsed_line = line.split('\t')
            # get entity id
            en_index = int(parsed_line[0][1:])
            en_id = f'EN{doc_id}.{en_index:06d}'
            # get type, offsets
            en_type, offset_start, offset_end = parsed_line[1].split(' ')
            offset_start = int(offset_start)
            offset_end = int(offset_end)
            # get text
            en_text = parsed_line[2].strip()
            # add to dict using ann id, i.e. T1
            entity_dict[parsed_line[0]] = {'id':en_id,'type':en_type,'offsets':(offset_start,offset_end),'text':en_text}
    return entity_dict

def get_events(doc_id, lines, entities):
    event_dict = {}
    for line in lines:
        if line.startswith('E'):
            parsed_line = line.split('\t')
            # get evnet id
            ev_index = int(parsed_line[0][1:])
            ev_id = f'EV{doc_id}.{ev_index:06d}'
            # get type
            ev_type = parsed_line[1].split(' ')[0].split(':')[0]
            # get full type str
            subsubtype = 'Unspecified'
            if len(ev_type.split('_')) == 2:
                subtype, subsubtype = ev_type.split('_')
            elif len(ev_type.split('_')) == 3:
                type_, subtype, subsubtype = ev_type.split('_')
            else:
                subtype = ev_type
            type_ = Subtype_Type_Mapping[subtype]
            ev_type_str = '.'.join([type_,subtype,subsubtype]) 

            trigger_id = parsed_line[1].split(' ')[0].split(':')[1]
            ev_trigger = {'offsets':entities[trigger_id]['offsets'], 'text':entities[trigger_id]['text']}
            # get args
            args = []
            for arg_str in parsed_line[1].split(' ')[1:]:
                arg_str = arg_str.strip()
                if arg_str == '':
                    continue
                arg_type = arg_str.split(':')[0]
                arg_entity = entities[arg_str.split(':')[1]]
                args.append({'role_type':arg_type,'entity_id':arg_entity['id'], 'entity_ann_id':arg_str.split(':')[1]})
            event_dict[parsed_line[0]] = {'id':ev_id,'type':ev_type_str,'trigger':ev_trigger,'arguments':args}
    return event_dict

def get_attributes(doc_id, lines, events, entities):
    attr_dict = {}
    for line in lines:
        if line.startswith('A'):
            parsed_line = line.split('\t')
            # get attribute id
            attr_index = int(parsed_line[0][1:])
            attr_id = f'AT{doc_id}.{attr_index:06d}'
            # get attr type
            attr_type, arg_ann_id, value = parsed_line[1].split(' ')
            value = value.strip()
            if arg_ann_id in events:
                attr_dict[parsed_line[0]] = {'id':attr_id,'type':attr_type,'arg_id':events[arg_ann_id]['id'],'value':value, 'arg_ann_id':arg_ann_id}
            elif arg_ann_id in entities:
                attr_dict[parsed_line[0]] = {'id':attr_id,'type':attr_type,'arg_id':entities[arg_ann_id]['id'],'value':value, 'arg_ann_id':arg_ann_id}

    return attr_dict

def get_relations(doc_id, lines, entities):
    relations = {}
    for line in lines:
        if line.startswith('R'):
            parsed_line = line.split('\t')
            # get relation id
            rel_index = int(parsed_line[0][1:])
            rel_id = f'RE{doc_id}.{rel_index:06d}'
            # get type, args
            rel_type, arg1_str, arg2_str = parsed_line[1].split(' ')
            arg2_str = arg2_str.strip()
            arg1 = {'arg1_name':arg1_str.split(':')[0],'entity_id':entities[arg1_str.split(':')[1]]['id'], 'entity_ann_id':arg1_str.split(':')[1]}
            arg2 = {'arg2_name':arg2_str.split(':')[0],'entity_id':entities[arg2_str.split(':')[1]]['id'], 'entity_ann_id':arg2_str.split(':')[1]}
            relations[parsed_line[0]] = {'id':rel_id, 'type': rel_type.replace('_','.'), 'args':{'arg1':arg1,'arg2':arg2}}
    return relations

def load_ann(ann_path):
    lines = []
    with open(ann_path) as f:
        for line in f:
            lines.append(line)
    return lines

def generate_LDC_tabs(tab_name, child_id, entities, events, relations, output_dir = '.', root_id = NA_FILLER):
    def write_lines(lines):
        with open(os.path.join(output_dir,tab_name), 'w') as out:
            for l in lines:
                out.write(l)
        print(f'write tab file to {os.path.join(output_dir,tab_name)}')
    
    if tab_name == 'events.tab':
        first_line = 'root_uid\teventmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tattribute\tstart_date_type\tstart_date\tend_date_type\tend_date\n'
        lines = []
        lines.append(first_line)
        for ev in events.values():
            ev_id = ev['id']
            off_start = ev['trigger']['offsets'][0]
            off_end = ev['trigger']['offsets'][1]
            text_string = ev['trigger']['text']
            subsubtype = 'Unspecified'
            if len(ev['type'].split('_')) == 2:
                subtype, subsubtype = ev['type'].split('_')
            elif len(ev['type'].split('_')) == 3:
                type_, subtype, subsubtype = ev['type'].split('_')
            else:
                subtype = ev['type']
            type_ = Subtype_Type_Mapping[subtype]
            line = f'{root_id}\t{ev_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{type_}\t{subtype}\t{subsubtype}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)

    elif tab_name == 'relations.tab':
        first_line = 'root_uid\trelationmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tattribute\tstart_date_type\tstart_date\tend_date_type\tend_date\n'
        lines = []
        lines.append(first_line)
        for re in relations.values():
            re_id = re['id']
            type_, subtype, subsubtype = re['type'].split('_')
            arg1 = entities[re['args']['arg1']['entity_ann_id']]
            arg2 = entities[re['args']['arg2']['entity_ann_id']]
            off_start = min(arg1['offsets'][0], arg2['offsets'][0])
            off_end = max(arg1['offsets'][1], arg2['offsets'][1])
            text_string = NA_FILLER
            line = f'{root_id}\t{re_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{type_}\t{subtype}\t{subsubtype}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)
    
    elif tab_name == 'arguments.tab':
        first_line = 'root_uid\targmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\targ_status\tlevel\n'
        lines = []
        lines.append(first_line)

        argument_ids = [] # could be entity or events; (ann_id, id) pairs
        # event arguments:
        for ev in events.values():
            for arg in ev['arguments']:
                en_id = arg['entity_id']
                en_ann_id = arg['entity_ann_id']
                argument_ids.append((en_ann_id,en_id))
        # relation argumens:
        for re in relations.values():
            arg1 = re['args']['arg1']
            arg1_en_id = arg1['entity_id']
            arg1_en_ann_id = arg1['entity_ann_id']

            arg2 = re['args']['arg2']
            arg2_en_id = arg2['entity_id']
            arg2_en_ann_id = arg2['entity_ann_id']
            argument_ids.append((arg1_en_ann_id,arg1_en_id))
            argument_ids.append((arg2_en_ann_id,arg2_en_id))

        for arg in argument_ids:
            arg_ann_id = arg[0]
            arg_id = arg[1]
            if arg_ann_id in events:
                # it is a event type argument
                arg_ev = events[arg_ann_id]
                off_start = arg_ev['trigger']['offsets'][0]
                off_end = arg_ev['trigger']['offsets'][1]
                text_string = arg_ev['trigger']['text']

                subsubtype = 'Unspecified'
                if len(ev['type'].split('_')) == 2:
                    subtype, subsubtype = ev['type'].split('_')
                elif len(ev['type'].split('_')) == 3:
                    type_, subtype, subsubtype = ev['type'].split('_')
                else:
                    subtype = ev['type']
                type_ = Subtype_Type_Mapping[subtype]
            
            elif arg_ann_id in entities:
                # it is a entity type argument
                arg_en = entities[arg_ann_id]
                off_start = arg_en['offsets'][0]
                off_end = arg_en['offsets'][1]
                text_string = arg_en['text']
                type_,subtype, subsubtype = arg_en['type'],'Unspecified','Unspecified'

            line = f'{root_id}\t{arg_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{type_}\t{subtype}\t{subsubtype}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)

    elif tab_name == 'slots.tab':
        first_line = 'root_uid\teventmention_id\tslot_type\targmention_id\tattribute\n'
        lines = []
        lines.append(first_line)
        for ev in events.values():
            ev_id = ev['id']
            for arg in ev['arguments']:
                en_id = arg['entity_id']
                slot_type = arg['role_type']
                line = f'{root_id}\t{ev_id}\t{slot_type}\t{en_id}\t{NA_FILLER}\n'
                lines.append(line)
        
        for re in relations.values():
            re_id = re['id']
            
            arg1 = re['args']['arg1']
            arg1_type = arg1['arg1_name']
            arg1_en_id = arg1['entity_id']

            arg2 = re['args']['arg2']
            arg2_type = arg2['arg2_name']
            arg2_en_id = arg2['entity_id']

            line1 = f'{root_id}\t{re_id}\t{arg1_type}\t{arg1_en_id}\t{NA_FILLER}\n'
            line2 = f'{root_id}\t{re_id}\t{arg2_type}\t{arg2_en_id}\t{NA_FILLER}\n'
            lines.append(line1)
            lines.append(line2)
        
        write_lines(lines)

def get_claim_event_relation_mapping(attributes, relations, output_dir = '.'):
    # get relation first arg entity to relation id mapping:
    re_arg1_to_reid = defaultdict(list)
    for re in relations.values():    
        arg1_id = re['args']['arg1']['entity_id']
        re_arg1_to_reid[arg1_id].append(re['id'])
    
    claim_dict = defaultdict(list)
    for attr in attributes.values():
        if attr['type'] == 'CliamID':
            # propagate to relations if it is an entity
            if attr['arg_id'] in re_arg1_to_reid: 
                for re_id in re_arg1_to_reid[attr['arg_id']]:
                    claim_dict[attr['value']].append(re_id)
            else:
                claim_dict[attr['value']].append(attr['arg_id']) # add event
    # write to json
    # with open(os.path.join(output_dir,"inner_outer_mapping.json"), 'w') as out:
    #     json.dump(claim_dict, out, indent = 4)
    # print(f'write mapping json to {output_dir}')
    return claim_dict

def process_ann(ann_path):
    pp = pprint.PrettyPrinter(indent=4)
    
    doc_id = os.path.basename(ann_path)[:-8]
    
    lines = load_ann(ann_path)
    
    entities = get_entities(doc_id,lines)
    print('entity:')
    pp.pprint(entities['T1']) # print entity
    print('===================================')
    
    events = get_events(doc_id,lines,entities) 
    print('event:')
    pp.pprint(events['E3']) # print event
    print('===================================')
    
    attributes = get_attributes(doc_id,lines,events, entities)
    print('attrubutes:')
    pp.pprint(attributes['A1']) # print attr
    print('===================================')
    
    relations = get_relations(doc_id,lines,entities)
    print('relations:')
    pp.pprint(relations['R1'])
    print('===================================')

    print(f'processed ann path: {ann_path}')
    print('=====================================')

    return entities, events, attributes, relations

def main():

    # ann_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C0495BR_in/L0C0495BR.rsd.ann'
    # out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C0495BR_out'
    ann_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_in/L0C04958T.rsd.ann'
    out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_out'
    
    entities, events, attributes, relations = process_ann(ann_path)

    # write tabs:
    generate_LDC_tabs('events.tab', doc_id, entities, events, relations, output_dir = out_dir_path, root_id = NA_FILLER)
    generate_LDC_tabs('relations.tab', doc_id, entities, events, relations, output_dir = out_dir_path, root_id = NA_FILLER)
    generate_LDC_tabs('arguments.tab', doc_id, entities, events, relations, output_dir = out_dir_path, root_id = NA_FILLER)
    generate_LDC_tabs('slots.tab', doc_id, entities, events, relations, output_dir = out_dir_path, root_id = NA_FILLER)

    # write mapping json:
    get_claim_event_relation_mapping(attributes,relations, output_dir = out_dir_path )


def gen_mention_template(ann_dir, ltf_dir, aida_ont, kairos_ont, output_dir = None):
    
    def gen_event_argument_line(arg):
        arg_en = entities[arg['entity_ann_id']]
        arg_en_type = arg_en['type']
        arg_provenance = arg_en['text']
        arg_off_start = arg_en['offsets'][0]
        arg_off_end = arg_en['offsets'][1] - 1
        arg_en_id = arg['entity_id']
        arg_role_type = arg['role_type']
        arg_offset_str = f'{doc_id}:{arg_off_start}-{arg_off_end}'
        arg_nlp_description = ltf_util.get_original_text(arg_offset_str)
        arg_attribute = NA_FILLER

        if arg_role_type in argrole_to_argnum:
            arg_num = argrole_to_argnum[arg_role_type]
        else:
            arg_num = argrole_to_argnum[arg_role_type[:-1]]

        return f'{arg_en_id}\t{arg_nlp_description}\t{arg_provenance}\t{arg_attribute}\t{arg_en_type}\t{NA_FILLER}\t{arg_num}\t{arg_role_type}\n'

    '''load ltf class'''
    ltf_util = LTF_util(ltf_dir)
    # usage: ltf_util.get_original_text('K0C047Z59:477-493'))
    
    for ann_path in glob(os.path.join(ann_dir,'*.ann')):
        entities, events, attributes, relations = process_ann(ann_path)
        # check inner outer mapping
        inner_outer_mapping = get_claim_event_relation_mapping(attributes,relations)
        
        doc_id = os.path.basename(ann_path)[:-8]
        
        lines_dict = {}

        # get event mention lines:
        for ev in events.values():
            ev_lines = []
            
            ev_id = ev['id']
            trigger_provenance = ev['trigger']['text']
            off_start = ev['trigger']['offsets'][0]
            off_end = ev['trigger']['offsets'][1] - 1
            trigger_offset_str = f'{doc_id}:{off_start}-{off_end}'
            nlp_description = ltf_util.get_original_text(trigger_offset_str)
            ev_attribute = NA_FILLER
            ev_type = ev['type']

            if ev_type.split('.')[0] in ['Life','Medical']:
                using_ontology = kairos_ont
            else:
                using_ontology = aida_ont
            
            # get populated template
            ev_ont = using_ontology.events[ev_type]
            argrole_to_argnum = ev_ont['args']
            
            ev_template = ev_ont['template']
            ev_args = ev['arguments']

            arg_lines = []
            for arg in ev_args:
                # get arg lines:
                arg_lines.append(gen_event_argument_line(arg))

                arg_en = entities[arg['entity_ann_id']]
                arg_role = arg['role_type']
                if arg_role in argrole_to_argnum:
                    arg_num = argrole_to_argnum[arg_role]
                    ev_template = ev_template.replace(arg_num,arg_en['text'])
                else:
                    # TODO: handle multiple args like: Victim2,Victim3
                    print('cannot find arg role:', arg_role, 'for event:', ev_type)

            ev_line = f'{ev_id}\t{nlp_description}\t{trigger_provenance}\t{ev_attribute}\t{ev_type}\t{NA_FILLER}\tn/a\tn/a\t{ev_template}\n'
            ev_lines.append(ev_line)
            for a_l in arg_lines:
                ev_lines.append(a_l)
            # add lines for one event item to dict
            lines_dict[ev_id] = ev_lines

        # get relation mention lines:
        for re in relations.values():
            re_lines = []
            re_id = re['id']
            
            arg1 = re['args']['arg1']
            arg1_en = entities[arg1['entity_ann_id']]
            arg1_off_start = arg1_en['offsets'][0]
            arg1_off_end = arg1_en['offsets'][1]-1
            arg1_offset_str = f'{doc_id}:{arg1_off_start}-{arg1_off_end}'
            arg1_nlp_description = ltf_util.get_original_text(arg1_offset_str)
            arg1_en_id = arg1['entity_id']
            arg1_text = arg1_en['text']
            arg1_en_type = arg1_en['type']

            arg2 = re['args']['arg2']
            arg2_en = entities[arg2['entity_ann_id']]
            arg2_off_start = arg2_en['offsets'][0]
            arg2_off_end = arg2_en['offsets'][1]-1
            arg2_offset_str = f'{doc_id}:{arg2_off_start}-{arg2_off_end}'
            arg2_nlp_description = ltf_util.get_original_text(arg2_offset_str)
            arg2_en_id = arg2['entity_id']
            arg2_text = arg2_en['text']
            arg2_en_type = arg2_en['type']
            
            re_off_start = min(arg1_off_start, arg2_off_start)
            re_off_end = max(arg1_off_end, arg2_off_end)-1
            re_offset_str = f'{doc_id}:{re_off_start}-{re_off_end}'

            re_nlp_description = ltf_util.get_original_text(re_offset_str)
            re_provenance = re_nlp_description
            re_attribute = NA_FILLER
            re_type = re['type']
            # using kairos relation ontology
            using_ontology = kairos_ont
            re_ont = using_ontology.relations[re_type]

            arg1_role_type = re_ont['args']['Arg1']
            arg2_role_type = re_ont['args']['Arg2']

            re_template = re_ont['template']
            re_template = re_template.replace('arg1',arg1_en['text'])
            re_template = re_template.replace('arg2',arg2_en['text'])
            
            # add relation mention line
            re_lines.append(f'{re_id}\t{re_nlp_description}\t{re_provenance}\t{re_attribute}\t{re_type}\t{NA_FILLER}\tn/a\tn/a\t{re_template}\n')

            # add relation arg line
            re_lines.append(f'{arg1_en_id}\t{arg1_nlp_description}\t{arg1_text}\t{NA_FILLER}\t{arg1_en_type}\t{NA_FILLER}\targ1\t{arg1_role_type}\n')
            re_lines.append(f'{arg2_en_id}\t{arg2_nlp_description}\t{arg2_text}\t{NA_FILLER}\t{arg2_en_type}\t{NA_FILLER}\targ2\t{arg2_role_type}\n')
            
            # add lines for one relation item to dict
            lines_dict[re_id] = re_lines

        if output_dir:
            with open(os.path.join(output_dir,f'{doc_id}_mention_template.txt'), 'w') as out:
                for claimid, inner_ids in inner_outer_mapping.items():
                    out.write(f'==========Claimid: {claimid}==========\n')
                    for inner_id in inner_ids:
                        # if it is Relationid or Eventid
                        if not inner_id.startswith('EN'):
                            for line in lines_dict[inner_id]:
                                out.write(line)
            print('done writing:',os.path.join(output_dir,'mention_template.txt'))
        else:
            return lines_dict
        

if __name__ == '__main__':
    # main()

    '''config'''
    ann_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/hw2_inner/ann'
    ltf_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/hw2_inner/ltf'
    out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/hw2_inner/out'

    '''load ontology'''
    aida_ontology_xlsx_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/ontology/AIDA_Annotation_Ontology_Phase2_V1.1.xlsx'
    kairos_ontology_xlsx_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/ontology/KAIROS_Annotation_Tagset_Phase_1_V3.0.xlsx'
    aida_ont = Ontology(aida_ontology_xlsx_path, 'aida')    
    kairos_ont = Ontology(kairos_ontology_xlsx_path, 'kairos')    
    
    '''generate ldc homework 2 mention template'''
    gen_mention_template(ann_dir_path, ltf_dir_path, aida_ont, kairos_ont, output_dir = out_dir_path)