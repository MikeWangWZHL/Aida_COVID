import os
import json
import pprint
from collections import defaultdict
from ltf_util import LTF_util
from glob import glob
from shutil import copyfile
# from fuzzy_match import algorithims
import re
from ltf_util import LTF_util

"""Macro"""
NA_FILLER = 'EMPTY_NA'

def generate_LDC_tabs_TA3(tab_name, child_id, entities, events, relations, output_dir = '.', root_id = NA_FILLER, ltf_dir = None):
    def write_lines(lines):
        with open(os.path.join(output_dir,tab_name), 'w', encoding = 'utf-8') as out:
            for l in lines:
                out.write(l)
        print(f'write tab file to {os.path.join(output_dir,tab_name)}')
    if ltf_dir:
        ltf_util = LTF_util(ltf_dir)
    
    if tab_name == 'TA3_evt_KEs.tab':
        first_line = 'root_uid\teventmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tqnode_type_id\tattribute\tqnode_attribute_id\tstart_date_type\tstart_date\tend_date_type\tend_date\n'
        lines = []
        lines.append(first_line)
        for ev in events.values():
            ev_id = ev['id']
            off_start = ev['trigger']['offsets'][0]
            off_end = ev['trigger']['offsets'][1]-1
            text_string = ev['trigger']['text']
            full_type = ev['type']
            type_, subtype, subsubtype = full_type.split('.') 
            type_qnode = ev['event_type_qnode']
            if ltf_dir:
                # add LTF description
                trigger_offset_str = f'{child_id}:{off_start}-{off_end}'
                description = ltf_util.get_original_text(trigger_offset_str)
            else:
                description = NA_FILLER 
            line = f'{root_id}\t{ev_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{description}\t{type_}\t{subtype}\t{subsubtype}\t{type_qnode}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)

    elif tab_name == 'TA3_rel_KEs.tab':
        first_line = 'root_uid\trelationmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tqnode_type_id\tattribute\tqnode_attribute_id\tstart_date_type\tstart_date\tend_date_type\tend_date\n'
        lines = []
        lines.append(first_line)
        for re in relations.values():
            re_id = re['id']
            if len(re['type'].split('.')) != 3:
                continue
            type_, subtype, subsubtype = re['type'].split('.')
            if re['args']['arg1']['arg_ann_id'].startswith('T'):
                arg1 = entities[re['args']['arg1']['arg_ann_id']]
                arg1_offset = arg1['offsets']
            else:
                arg1 = events[re['args']['arg1']['arg_ann_id']]
                arg1_offset = arg1['trigger']['offsets']
            if re['args']['arg2']['arg_ann_id'].startswith('T'):
                arg2 = entities[re['args']['arg2']['arg_ann_id']]
                arg2_offset = arg2['offsets']
            else:
                arg2 = events[re['args']['arg2']['arg_ann_id']]
                arg2_offset = arg2['trigger']['offsets']

            off_start = min(arg1_offset[0], arg2_offset[0])
            off_end = max(arg1_offset[1]-1, arg2_offset[1]-1)
            if ltf_dir:
                # add LTF description
                arg1_off_start = arg1_offset[0]
                arg1_off_end = arg1_offset[1]-1
                offset_str = f'{child_id}:{arg1_off_start}-{arg1_off_end}'
                description = ltf_util.get_original_text(offset_str)
            else:
                description = NA_FILLER
            type_qnode = NA_FILLER # TODO
            text_string = NA_FILLER
            line = f'{root_id}\t{re_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{description}\t{type_}\t{subtype}\t{subsubtype}\t{type_qnode}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)
    
    elif tab_name == 'TA3_arg_KEs.tab':
        # TODO:
        first_line = 'root_uid\targmention_id\tchild_uid\ttextoffset_startchar\ttextoffset_endchar\ttext_string\tmediamention_signaltype\tmediamention_starttime\tmediamention_endtime\tkeyframe_id\tmediamention_coordinates\tdescription\ttype\tsubtype\tsubsubtype\tqnode_type_id\targ_status\tlevel\n'
        lines = []
        lines.append(first_line)

        argument_ids = [] # could be entity or events; (ann_id, id) pairs
        # event arguments:
        for ev in events.values():
            for arg in ev['arguments']:
                en_id = arg['arg_id']
                en_ann_id = arg['arg_ann_id']
                argument_ids.append((en_ann_id,en_id,arg['arg_type_qnode']))
        # relation argumens:
        for re in relations.values():
            arg1 = re['args']['arg1']
            arg1_en_id = arg1['arg_id']
            arg1_en_ann_id = arg1['arg_ann_id']

            arg2 = re['args']['arg2']
            arg2_en_id = arg2['arg_id']
            arg2_en_ann_id = arg2['arg_ann_id']
            argument_ids.append((arg1_en_ann_id, arg1_en_id, NA_FILLER))
            argument_ids.append((arg2_en_ann_id, arg2_en_id, NA_FILLER))

        for arg in argument_ids:
            arg_ann_id = arg[0]
            arg_id = arg[1]
            type_qnode = arg[2]
            if arg_ann_id in events:
                # it is a event type argument
                arg_ev = events[arg_ann_id]
                off_start = arg_ev['trigger']['offsets'][0]
                off_end = arg_ev['trigger']['offsets'][1]-1
                text_string = arg_ev['trigger']['text']
                # print(arg_ev['type'])
                type_, subtype, subsubtype = arg_ev['type'].split('.')
            
            elif arg_ann_id in entities:
                # it is a entity type argument
                arg_en = entities[arg_ann_id]
                off_start = arg_en['offsets'][0]
                off_end = arg_en['offsets'][1]-1
                text_string = arg_en['text']
                type_, subtype, subsubtype = arg_en['type'],'Unspecified','Unspecified'

            description = text_string
            line = f'{root_id}\t{arg_id}\t{child_id}\t{off_start}\t{off_end}\t{text_string}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{NA_FILLER}\t{description}\t{type_}\t{subtype}\t{subsubtype}\t{type_qnode}\t{NA_FILLER}\t{NA_FILLER}\n'
            lines.append(line)
        
        write_lines(lines)

    elif tab_name == 'TA3_evt_slots.tab':
        first_line = 'root_uid\teventmention_id\tslot_type\tgeneral_slot_type\targmention_id\tattribute\tqnode_attribute_id\n'
        lines = []
        lines.append(first_line)
        for ev in events.values():
            ev_id = ev['id']
            for arg in ev['arguments']:
                en_id = arg['arg_id']
                slot_type = arg['role_type']
                general_role_type = arg['general_role_type']
                line = f'{root_id}\t{ev_id}\t{slot_type}\t{general_role_type}\t{en_id}\t{NA_FILLER}\t{NA_FILLER}\n'
                lines.append(line)
        
        write_lines(lines)
    
    elif tab_name == 'TA3_rel_slots.tab':
        first_line = 'root_uid\trelationmention_id\tslot_type\tgeneral_slot_type\targmention_id\n'
        lines = []
        lines.append(first_line)
        for re in relations.values():
            re_id = re['id']
            
            arg1 = re['args']['arg1']
            arg1_type = arg1['arg1_name']
            arg1_general_type = NA_FILLER # TODO
            arg1_en_id = arg1['arg_id']


            arg2 = re['args']['arg2']
            arg2_type = arg2['arg2_name']
            arg2_general_type = NA_FILLER # TODO
            arg2_en_id = arg2['arg_id']

            line1 = f'{root_id}\t{re_id}\t{arg1_type}\t{arg1_general_type}\t{arg1_en_id}\n'
            line2 = f'{root_id}\t{re_id}\t{arg2_type}\t{arg2_general_type}\t{arg2_en_id}\n'
            lines.append(line1)
            lines.append(line2)
        
        write_lines(lines)









###################################################################################################################

def generate_LDC_tabs_old(tab_name, child_id, entities, events, relations, output_dir = '.', root_id = NA_FILLER):
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
            arg1 = entities[re['args']['arg1']['arg_ann_id']]
            arg2 = entities[re['args']['arg2']['arg_ann_id']]
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
                en_id = arg['arg_id']
                en_ann_id = arg['arg_ann_id']
                argument_ids.append((en_ann_id,en_id))
        # relation argumens:
        for re in relations.values():
            arg1 = re['args']['arg1']
            arg1_en_id = arg1['arg_id']
            arg1_en_ann_id = arg1['arg_ann_id']

            arg2 = re['args']['arg2']
            arg2_en_id = arg2['arg_id']
            arg2_en_ann_id = arg2['arg_ann_id']
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
                en_id = arg['arg_id']
                slot_type = arg['role_type']
                line = f'{root_id}\t{ev_id}\t{slot_type}\t{en_id}\t{NA_FILLER}\n'
                lines.append(line)
        
        for re in relations.values():
            re_id = re['id']
            
            arg1 = re['args']['arg1']
            arg1_type = arg1['arg1_name']
            arg1_en_id = arg1['arg_id']

            arg2 = re['args']['arg2']
            arg2_type = arg2['arg2_name']
            arg2_en_id = arg2['arg_id']

            line1 = f'{root_id}\t{re_id}\t{arg1_type}\t{arg1_en_id}\t{NA_FILLER}\n'
            line2 = f'{root_id}\t{re_id}\t{arg2_type}\t{arg2_en_id}\t{NA_FILLER}\n'
            lines.append(line1)
            lines.append(line2)
        
        write_lines(lines)