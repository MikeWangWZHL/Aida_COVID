import os
import json
import pprint

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
    "TransferOwnership":"Transaction"
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
            trigger_id = parsed_line[1].split(' ')[0].split(':')[1]
            ev_trigger = {'offests':entities[trigger_id]['offsets'], 'text':entities[trigger_id]['text']}
            # get args
            args = []
            for arg_str in parsed_line[1].split(' ')[1:]:
                arg_str = arg_str.strip()
                if arg_str == '':
                    continue
                arg_type = arg_str.split(':')[0]
                arg_entity = entities[arg_str.split(':')[1]]
                args.append({'role_type':arg_type,'entity_id':arg_entity['id']})
            event_dict[parsed_line[0]] = {'id':ev_id,'type':ev_type,'trigger':ev_trigger,'arguments':args}
    return event_dict

def get_attributes(doc_id, lines, events):
    attr_dict = {}
    for line in lines:
        if line.startswith('A'):
            parsed_line = line.split('\t')
            # get attribute id
            attr_index = int(parsed_line[0][1:])
            attr_id = f'AT{doc_id}.{attr_index:06d}'
            # get attr type
            attr_type, ev_ann_id, value = parsed_line[1].split(' ')
            value = value.strip()
            attr_dict[parsed_line[0]] = {'id':attr_id,'type':attr_type,'event_id':events[ev_ann_id]['id'],'value':value, 'event_ann_id':ev_ann_id}

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
            relations[parsed_line[0]] = {'id':rel_id, 'type': rel_type, 'args':{'arg1':arg1,'arg2':arg2}}
    return relations

def load_ann(ann_path):
    lines = []
    with open(ann_path) as f:
        for line in f:
            lines.append(line)
    return lines

def generate_LDC_tabs(tab_name, child_id, entities, events, relations, arguments, output_dir = '.', root_id = NA_FILLER):
    def write_lines(lines):
        with open(os.path.join(output_dir,tab_name), 'w') as out:
            for l in lines:
                out.write(l)
        print(f'write to {os.path.join(output_dir,tab_name)}')
    
    if tab_name == 'events.tab':
        first_line = 'root_uid\teventmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tattribute\tstart_date_type\tstart_date\tend_date_type\tend_date\n'
        lines = []
        lines.append(first_line)
        for ev in events.values():
            ev_id = ev['id']
            off_start = ev['trigger']['offests'][0]
            off_end = ev['trigger']['offests'][1]
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


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    
    ann_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_example/L0C04958T.rsd.ann'
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
    
    print('attrubutes:')
    attributes = get_attributes(doc_id,lines,events)
    pp.pprint(attributes['A1']) # print attr
    print('===================================')
    
    print('relations:')
    relations = get_relations(doc_id,lines,entities)
    pp.pprint(relations['R1'])
    print('===================================')

    generate_LDC_tabs('events.tab', doc_id, entities, events, relations, attributes, output_dir = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_out_tabs', root_id = NA_FILLER)
    generate_LDC_tabs('relations.tab', doc_id, entities, events, relations, attributes, output_dir = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_out_tabs', root_id = NA_FILLER)
    generate_LDC_tabs('slots.tab', doc_id, entities, events, relations, attributes, output_dir = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/src/L0C04958T_out_tabs', root_id = NA_FILLER)