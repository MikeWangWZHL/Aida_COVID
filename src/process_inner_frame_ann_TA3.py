import os
import json
import pprint
from collections import defaultdict
from ltf_util import LTF_util
from glob import glob
from shutil import copyfile
from fuzzy_match import algorithims
import re
from generate_LDC_tabs import generate_LDC_tabs_TA3

"""Macro"""
NA_FILLER = 'EMPTY_NA'
ONT_MAPPING = json.load(open('/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/event_mapping_manual_7-21.json'))

"""helper functions"""
def get_event_type_qnode(event_type, xpo_ontology):
    if event_type in xpo_ontology:
        if len(xpo_ontology[event_type]['WD_Qnode'].split('_'))<2:
            return NA_FILLER
        return xpo_ontology[event_type]['WD_Qnode'].split('_')[1].strip()
    else:
        return NA_FILLER

def get_event_argument_type_qnode(event_type, arg_role, xpo_ontology):
    if event_type not in xpo_ontology:
        return NA_FILLER
    args = xpo_ontology[event_type]['args']
    for arg in args:
        key = arg['ldc_role'].replace('/','_').replace(' ','_')
        arg_role = re.sub(r'\d', '', arg_role) # handle number in arg_role: Participant1
        if  key == arg_role:
            if len(arg['constraints']) > 1:
                qnodes_str =  '|'.join([c.split('_')[-1] for c in arg['constraints']])
            else:
                qnodes_str = arg['constraints'][0].split('_')[-1]
            if 'Q' not in qnodes_str:
                return NA_FILLER
            else:
                return qnodes_str
    print(f'ERROR: cannot find matched argument for event:{event_type}, arg_role:{arg_role}')
    return None

def get_event_arg_general_role_type(event_type, arg_role, xpo_ontology):
    if event_type not in xpo_ontology:
        return NA_FILLER
    args = xpo_ontology[event_type]['args']
    for arg in args:
        key = arg['ldc_role'].replace('/','_').replace(' ','_')
        arg_role = re.sub(r'\d', '', arg_role) # handle number in arg_role: Participant1
        if  key == arg_role:
            return arg['xpo_role']
    print(f'ERROR: cannot find matched argument for event:{event_type}, arg_role:{arg_role}')
    return None

def get_relation_arg_general_role_type(event_type, arg_num, xpo_ontology):
    # TODO:
    return NA_FILLER

def get_relation_type_qnode(rel_type, rel_ontology):
    # TODO:
    return NA_FILLER

def get_relation_argument_type_qnode(rel_type, arg_num, rel_ontology):
    # TODO:
    return NA_FILLER

"""process ann"""
def get_entities(doc_id, lines):
    print(doc_id)
    entity_dict = {}
    for line in lines:
        if line.startswith('T'):
            parsed_line = line.split('\t')
            # get entity id
            en_index = int(parsed_line[0][1:])
            en_id = f'EN{doc_id}.{en_index:06d}'
            # get type, offsets
            # print(parsed_line)
            if ';' in parsed_line[1]:
                parsed_line_offset = parsed_line[1].split(';')[0]
            else:
                parsed_line_offset = parsed_line[1]

            en_type, offset_start, offset_end = parsed_line_offset.split(' ')
            offset_start = int(offset_start)
            offset_end = int(offset_end)
            # get text
            en_text = parsed_line[2].strip()
            # add to dict using ann id, i.e. T1
            entity_dict[parsed_line[0]] = {'id':en_id,'type':en_type,'offsets':(offset_start,offset_end),'text':en_text,'arg_ann_id':parsed_line[0]}
    return entity_dict

def get_events(doc_id, lines, entities, xpo_ontology = None):
    event_dict = {}
    for line in lines:
        if line.startswith('E'):
            parsed_line = line.split('\t')
            # get evnet id
            ev_index = int(parsed_line[0][1:])
            ev_id = f'EV{doc_id}.{ev_index:06d}'
            # get full type str
            '''do mapping on old ontology'''
            ann_type_str = parsed_line[1].split(' ')[0].split(':')[0]
            args_mapping = None
            if ann_type_str in ONT_MAPPING:
                args_mapping = ONT_MAPPING[ann_type_str]['args']
                ann_type_str = ONT_MAPPING[ann_type_str]['mapped_type_name']
                print('mapped:',ann_type_str)

            ev_type_str = ann_type_str.replace('_','.')

            trigger_id = parsed_line[1].split(' ')[0].split(':')[1]
            ev_trigger = {'offsets':entities[trigger_id]['offsets'], 'text':entities[trigger_id]['text']}
            # get args
            args = []
            for arg_str in parsed_line[1].split(' ')[1:]:
                arg_str = arg_str.strip()
                if arg_str == '':
                    continue
                arg_type, arg_id = arg_str.split(':')
                # map args for old ontology
                if args_mapping:
                    if arg_type not in  args_mapping:
                        print(ann_type_str)
                    arg_type = args_mapping[arg_type]

                if arg_id.startswith('E'):
                    # print(parsed_line)
                    # assert arg_id in event_dict 
                    args.append(
                        {
                            'role_type':arg_type,
                            'general_role_type':get_event_arg_general_role_type(ev_type_str, arg_type, xpo_ontology),
                            'arg_id':None,
                            'arg_ann_id':arg_id,
                            'arg_type_qnode':get_event_argument_type_qnode(ev_type_str, arg_type, xpo_ontology)
                        }
                    )
                else:
                    arg_object = entities[arg_id]
                    args.append(
                        {
                            'role_type':arg_type,
                            'general_role_type':get_event_arg_general_role_type(ev_type_str, arg_type, xpo_ontology),
                            'arg_id':arg_object['id'],
                            'arg_ann_id':arg_id,
                            'arg_type_qnode':get_event_argument_type_qnode(ev_type_str, arg_type, xpo_ontology)
                        }
                    )
            # brat id
            event_dict[parsed_line[0]] = {
                'id':ev_id,
                'type':ev_type_str,
                'trigger':ev_trigger,
                'arguments':args, 
                'event_ann_id':parsed_line[0],
                'event_type_qnode':get_event_type_qnode(ev_type_str, xpo_ontology)
            }
    for ev,value in event_dict.items():
        for arg in value['arguments']:
            if arg['arg_id'] is None:
                assert arg['arg_ann_id'] in event_dict
                arg['arg_id'] = event_dict[arg['arg_ann_id']]['id']
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

def get_relations(doc_id, lines, entities, events, relation_ontology = None):
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
            if arg1_str.split(':')[1] in entities:
                arg1 = {
                    'arg1_name':arg1_str.split(':')[0],
                    'arg_id':entities[arg1_str.split(':')[1]]['id'], 
                    'arg_ann_id':arg1_str.split(':')[1],
                    'arg_type_qnode':get_relation_argument_type_qnode(rel_type, 'arg1', relation_ontology),
                    'arg_general_role_type':get_relation_arg_general_role_type(rel_type, 'arg1', relation_ontology)
                    }
            elif arg1_str.split(':')[1] in events:
                arg1 = {
                    'arg1_name':arg1_str.split(':')[0],
                    'arg_id':events[arg1_str.split(':')[1]]['id'], 
                    'arg_ann_id':arg1_str.split(':')[1],
                    'arg_type_qnode':get_relation_argument_type_qnode(rel_type, 'arg1', relation_ontology),
                    'arg_general_role_type':get_relation_arg_general_role_type(rel_type, 'arg1', relation_ontology)
                    }
            if arg2_str.split(':')[1] in entities:
                arg2 = {
                    'arg2_name':arg2_str.split(':')[0],
                    'arg_id':entities[arg2_str.split(':')[1]]['id'], 
                    'arg_ann_id':arg2_str.split(':')[1],
                    'arg_type_qnode':get_relation_argument_type_qnode(rel_type, 'arg2', relation_ontology),
                    'arg_general_role_type':get_relation_arg_general_role_type(rel_type, 'arg2', relation_ontology)
                    }
            elif arg2_str.split(':')[1] in events:
                arg2 = {
                    'arg2_name':arg2_str.split(':')[0],
                    'arg_id':events[arg2_str.split(':')[1]]['id'], 
                    'arg_ann_id':arg2_str.split(':')[1],
                    'arg_type_qnode':get_relation_argument_type_qnode(rel_type, 'arg2', relation_ontology),
                    'arg_general_role_type':get_relation_arg_general_role_type(rel_type, 'arg2', relation_ontology)
                    }

            relations[parsed_line[0]] = {
                'id':rel_id, 
                'type': rel_type.replace('_','.'), 
                'args':{'arg1':arg1,'arg2':arg2}, 
                'relation_ann_id':parsed_line[0],
                'relation_type_qnode':get_relation_type_qnode(rel_type, relation_ontology) # TODO: get from relation ontology
                }
    return relations

# def get_qnodes(doc_id, lines):
#     # return a dict where keys are brat ids, i.e E1, T1, R1...; value is a list of Qnodes
#     qnode_dict = {}
#     for line in lines:
#         if line.startswith('#'):
#             parsed_line = line.split('\t')
#             id_ = parsed_line[1].split(' ')[1].strip()
#             value = parsed_line[2].strip()
#             if '|' in value:
#                 values = [q.strip() for q in value.split('|')]
#             else:
#                 values = [value]
#             qnode_dict[id_] = values
#     return qnode_dict

def load_ann(ann_path):
    lines = []
    with open(ann_path) as f:
        for line in f:
            lines.append(line)
    return lines

def process_ann(ann_path, xpo_ontology):
    pp = pprint.PrettyPrinter(indent=4)
    
    doc_id = os.path.basename(ann_path)[:-8]
    
    lines = load_ann(ann_path)

    entities = get_entities(doc_id, lines)
    # print('entity:')
    # pp.pprint(entities['T1']) # print entity
    # print('===================================')
    
    events = get_events(doc_id, lines, entities, xpo_ontology) 
    # print('event:')
    # # pp.pprint(events['E1']) # print event
    # pp.pprint(events) # print event
    # print('===================================')
    
    attributes = get_attributes(doc_id, lines, events, entities)
    # print('attrubutes:')
    # # pp.pprint(attributes['A1']) # print attr
    # pp.pprint(attributes) # print attr
    # print('===================================')
    
    relations = get_relations(doc_id, lines, entities, events, xpo_ontology)
    # print('relations:')
    # # pp.pprint(relations['R1'])
    # pp.pprint(relations)
    # print('===================================')

    # print(f'processed ann path: {ann_path}')
    # print('=====================================')

    return entities, events, attributes, relations

def get_claim_semantic_associate_dict(attributes, relations):
    # get relation first arg entity to relation id mapping:
    re_arg1_to_reid = defaultdict(list)
    for re in relations.values():    
        arg1_id = re['args']['arg1']['arg_id']
        re_arg1_to_reid[arg1_id].append(re['id'])
    
    claim_semantic_dict = defaultdict(list)
    claim_associate_dict = defaultdict(list)

    for attr in attributes.values():
        if 'ClaimID_Semantic' in attr['type']:
            # propagate to relations if it is an entity
            if attr['arg_id'] in re_arg1_to_reid: 
                for re_id in re_arg1_to_reid[attr['arg_id']]:
                    claim_semantic_dict[attr['value']].append(re_id)
                    claim_associate_dict[attr['value']].append(re_id)
            else:
                claim_semantic_dict[attr['value']].append(attr['arg_id']) # add event
                claim_associate_dict[attr['value']].append(attr['arg_id']) # add event
        if 'ClaimID_Associate' in attr['type']:
            # propagate to relations if it is an entity
            if attr['arg_id'] in re_arg1_to_reid: 
                for re_id in re_arg1_to_reid[attr['arg_id']]:
                    if re_id not in claim_associate_dict[attr['value']]:
                        claim_associate_dict[attr['value']].append(re_id)
            else:
                if attr['arg_id'] not in claim_associate_dict[attr['value']]:
                    claim_associate_dict[attr['value']].append(attr['arg_id']) # add event
    return claim_semantic_dict, claim_associate_dict

def main():

    '''config'''
    annotated_innerframe_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-4-dump/annotated_inner_frame/LDC2021E11_TA3_annotation_batch_1_EN'
    ltf_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/brat/Aida_TA3_First_batch/ltf/en'
    out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-4-dump/out/TA3'
    
    xpo_ontology_json = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/json/kairos_event_ontology_xpo-7_19.json'
    
    '''load ontology'''
    xpo_ontology = json.load(open(xpo_ontology_json))
    xpo_ontology_new = {}
    # fix config names
    for key,value in xpo_ontology.items():
        new_key = key.replace(' - ','-')
        new_key = new_key.replace(' ','-')
        xpo_ontology_new[new_key] = value
    xpo_ontology = xpo_ontology_new

    '''get ann file paths'''
    inner_frame_dirs = glob(os.path.join(annotated_innerframe_dir_path,'*'))
    ann_file_paths = [os.path.join(dir_path, os.path.basename(dir_path) + '.rsd.ann') for dir_path in inner_frame_dirs if os.path.isdir(dir_path)]
    
    '''inner frame'''
    for ann_path in ann_file_paths: 
        # make dir for each document
        doc_out_dir = os.path.join(out_dir_path, os.path.basename(ann_path)[:-8])
        if not os.path.exists(doc_out_dir):
            os.makedirs(doc_out_dir)

        entities, events, attributes, relations = process_ann(ann_path, xpo_ontology)
        claim_semantic_dict, claim_associate_dict = get_claim_semantic_associate_dict(attributes, relations)
        
        # output claim semantic, claim associate jsons
        with open(os.path.join(doc_out_dir, 'claim_semantic.json'), 'w') as out:
            json.dump(claim_semantic_dict,out,indent =4)
        with open(os.path.join(doc_out_dir, 'claim_associate.json'), 'w') as out:
            json.dump(claim_associate_dict,out,indent =4)
        
        # output KE tabs
        child_id = os.path.basename(ann_path)[:-8]
        generate_LDC_tabs_TA3('TA3_evt_KEs.tab', child_id, entities, events, relations, output_dir = doc_out_dir, root_id = NA_FILLER, ltf_dir = ltf_dir_path)
        generate_LDC_tabs_TA3('TA3_rel_KEs.tab', child_id, entities, events, relations, output_dir = doc_out_dir, root_id = NA_FILLER, ltf_dir = ltf_dir_path)
        generate_LDC_tabs_TA3('TA3_arg_KEs.tab', child_id, entities, events, relations, output_dir = doc_out_dir, root_id = NA_FILLER, ltf_dir = ltf_dir_path)
        generate_LDC_tabs_TA3('TA3_evt_slots.tab', child_id, entities, events, relations, output_dir = doc_out_dir, root_id = NA_FILLER, ltf_dir = ltf_dir_path)
        generate_LDC_tabs_TA3('TA3_rel_slots.tab', child_id, entities, events, relations, output_dir = doc_out_dir, root_id = NA_FILLER, ltf_dir = ltf_dir_path)

        # output events, entities, relations, attributes
        # change keys to unique ids:
        for key in list(events.keys()):
            new_key = events[key]['id']
            events[new_key] = events.pop(key)
        for key in list(entities.keys()):
            new_key = entities[key]['id']
            entities[new_key] = entities.pop(key)
        for key in list(relations.keys()):
            new_key = relations[key]['id']
            relations[new_key] = relations.pop(key)
        for key in list(attributes.keys()):
            new_key = attributes[key]['id']
            attributes[new_key] = attributes.pop(key)

        with open(os.path.join(doc_out_dir, 'entities.json'), 'w') as out:
            json.dump(entities,out,indent=4)
        with open(os.path.join(doc_out_dir, 'events.json'), 'w') as out:
            json.dump(events,out,indent=4)
        with open(os.path.join(doc_out_dir, 'relations.json'), 'w') as out:
            json.dump(relations,out,indent=4)
        with open(os.path.join(doc_out_dir, 'attributes.json'), 'w') as out:
            json.dump(attributes,out,indent=4)

def get_clean_annotation():
    pp = pprint.PrettyPrinter(indent=4)

    '''config'''
    
    # annotated_innerframe_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-7-dump/rsd_ann/covid19_scenario_en'
    # out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-7-dump/inner_frame_annotation_processed/covid19_scenario_en'
    
    annotated_innerframe_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-7-dump/rsd_ann/LDC2021E11_TA3_annotation_batch_1_EN'
    out_dir_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/results/9-7-dump/inner_frame_annotation_processed/LDC2021E11_TA3_annotation_batch_1_EN'
    
    xpo_ontology_json = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/json/kairos_event_ontology_xpo-7_19.json'
    
    '''load ontology'''
    xpo_ontology = json.load(open(xpo_ontology_json))
    xpo_ontology_new = {}
    # fix config names
    for key,value in xpo_ontology.items():
        new_key = key.replace(' - ','-')
        new_key = new_key.replace(' ','-')
        xpo_ontology_new[new_key] = value
    xpo_ontology = xpo_ontology_new

    '''get ann file paths'''
    inner_frame_dirs = glob(os.path.join(annotated_innerframe_dir_path,'*'))
    ann_file_paths = [os.path.join(dir_path, os.path.basename(dir_path) + '.rsd.ann') for dir_path in inner_frame_dirs if os.path.isdir(dir_path)]
    

    filtered_event_count = 0
    claim_sentence_count = 0
    filtered_relations_count = 0
    event_count_total = 0
    relation_count_total = 0
    document_count_total = 0

    '''inner frame'''
    for ann_path in ann_file_paths: 
        # make dir for each document
        doc_out_dir = os.path.join(out_dir_path, os.path.basename(ann_path)[:-8])
        
        if not os.path.exists(doc_out_dir):
            os.makedirs(doc_out_dir)

        entities, events, attributes, relations = process_ann(ann_path, xpo_ontology)
        # counting
        if events != {}:
            event_count_total += len(events)
            document_count_total += 1
        if relations != {}:
            relation_count_total += len(relations)
        
        # claim_semantic_dict, claim_associate_dict = get_claim_semantic_associate_dict(attributes, relations)
        claim_sentences = []
        claim_sentences_offsets = []
        for en in entities.values():
            if en['type'] == 'Claim_Sentence':
                # Claim_Boundary, Claim_Sentence
                claim_sentences.append(en)
                claim_sentences_offsets.append(en['offsets'])
        # pp.pprint(claim_sentences)
        # pp.pprint(claim_sentences_offsets)
        
        filtered_events = []
        filtered_relations = []

        # filtered events
        for ev in events.values():
            offset_start, offset_end = ev['trigger']['offsets'][0], ev['trigger']['offsets'][1]
            for claim_off in claim_sentences_offsets:
                if offset_start >= claim_off[0] and offset_end <= claim_off[1]:
                    filtered_events.append(ev)
                    break


        # filtered relations
        for re in relations.values():
            # arg1
            arg1 = re['args']['arg1']
            if arg1['arg_ann_id'] in entities:
                arg1_en = entities[arg1['arg_ann_id']]
                arg1_offset_start, arg1_offset_end = arg1_en['offsets']
            elif arg1['arg_ann_id'] in events:
                arg1_ev = events[arg1['arg_ann_id']]
                arg1_offset_start, arg1_offset_end = arg1_ev['trigger']['offsets']
            # arg2
            arg2 = re['args']['arg2']
            if arg2['arg_ann_id'] in entities:
                arg2_en = entities[arg2['arg_ann_id']]
                arg2_offset_start, arg2_offset_end = arg2_en['offsets']
            elif arg2['arg_ann_id'] in events:
                arg2_ev = events[arg2['arg_ann_id']]
                arg2_offset_start, arg2_offset_end = arg2_ev['trigger']['offsets']

            for claim_off in claim_sentences_offsets:
                if (arg1_offset_start >= claim_off[0] and arg1_offset_end <= claim_off[1]) or (arg2_offset_start >= claim_off[0] and arg2_offset_end <= claim_off[1]):
                    filtered_relations.append(re)
                    break
        # print(claim_sentences_offsets)
        # print('filtered events', filtered_events)
        # print('filtered relations', filtered_relations)
        # print('==================================')

        with open(os.path.join(doc_out_dir, 'entities.json'), 'w') as out:
            json.dump(entities,out,indent=4)
        with open(os.path.join(doc_out_dir, 'events.json'), 'w') as out:
            json.dump(events,out,indent=4)
        with open(os.path.join(doc_out_dir, 'relations.json'), 'w') as out:
            json.dump(relations,out,indent=4)
        with open(os.path.join(doc_out_dir, 'attributes.json'), 'w') as out:
            json.dump(attributes,out,indent=4)
        with open(os.path.join(doc_out_dir, 'claim_sentences.json'), 'w') as out:
            json.dump(claim_sentences,out,indent=4)
        with open(os.path.join(doc_out_dir, 'filtered_events.json'), 'w') as out:
            json.dump(filtered_events,out,indent=4)
        with open(os.path.join(doc_out_dir, 'filtered_relations.json'), 'w') as out:
            json.dump(filtered_relations,out,indent=4)
        
        filtered_event_count += len(filtered_events)
        filtered_relations_count += len(filtered_relations)
        claim_sentence_count += len(claim_sentences)
    
    print('filtered_event_count:',filtered_event_count)
    print('claim_sentence_count:',claim_sentence_count)
    print('filtered_relations_count:',filtered_relations_count)
    print('Event count total:',event_count_total)
    print('Relation count total:',relation_count_total)
    print('Document count total:',document_count_total)

if __name__ == '__main__':
    '''process TA3'''
    # main()

    '''get inner frame clean annotation sentences'''
    get_clean_annotation()