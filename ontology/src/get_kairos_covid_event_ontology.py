import os
from glob import glob
import json

def get_events_LDC(tsv_path):
    events = {}
    with open(tsv_path) as f:
        for line in f:
            if line.startswith('LDC'):
                parsed_line = line.split('\t')
                event_type,event_subtype,event_subsubtype = parsed_line[1].strip().split('.')
                # capitalize
                # event_type.capitalize()
                # event_subtype.capitalize()
                # event_subsubtype.capitalize()

                # get args
                args = []
                for arg_i in range(3,7):
                    slot = parsed_line[arg_i]
                    if slot == '':
                        continue
                    if '=' not in slot:
                        role = slot.strip() 
                        constraints = ['<ALL>']
                    else:
                        role = slot.split('=')[0].strip()
                        constraints = [c.strip().upper() for c in slot.split('=')[1].split(',')]
                    args.append({'role':role,'constraints':constraints})

                if event_type not in events:
                    events[event_type] = {}
                if event_subtype not in events[event_type]:
                    events[event_type][event_subtype] = {}
                if event_subsubtype not in events[event_type][event_subtype]:
                    events[event_type][event_subtype][event_subsubtype] = args
    return events

def get_events_LDC_xpo(tsv_path):
    events = {}
    xpo_events = {}
    with open(tsv_path) as f:
        for line in f:
            if line.startswith('LDC'):
                parsed_line = line.split('\t')
                event_type,event_subtype,event_subsubtype = parsed_line[1].strip().split('.')
                # capitalize                
                # event_type = event_type.capitalize()
                # event_subtype = event_subtype.capitalize()
                # event_subsubtype = event_subsubtype.capitalize()
                
                # get args
                args = []
                for arg_i in range(3,7):
                    slot = parsed_line[arg_i]
                    if slot == '':
                        continue
                    if '=' not in slot:
                        role = slot.strip() 
                        constraints = ['<ALL>']
                    else:
                        role = slot.split('=')[0].strip()
                        constraints = [c.strip().upper() for c in slot.split('=')[1].split(',')]
                    args.append({'role':role,'constraints':constraints})

                if event_type not in events:
                    events[event_type] = {}
                if event_subtype not in events[event_type]:
                    events[event_type][event_subtype] = {}
                if event_subsubtype not in events[event_type][event_subtype]:
                    events[event_type][event_subtype][event_subsubtype] = args
                
                current_LDC_event = '.'.join([event_type, event_subtype, event_subsubtype])

            if line.startswith('xpo'):
                cur_event_type, cur_event_subtype, cur_event_subsubtype = current_LDC_event.split('.')

                parsed_line = line.split('\t')
                WD_Qnode = parsed_line[1].strip()
                args = []
                for arg_i in range(3,7):
                    slot = parsed_line[arg_i]
                    if slot == '':
                        continue
                    if '=' not in slot:
                        role = slot.strip() 
                        constraints = ['<ALL>']
                    else:
                        role = slot.split('=')[0].strip()
                        constraints = [c.strip() for c in slot.split('=')[1].split('|')]
                    ldc_role = events[cur_event_type][cur_event_subtype][cur_event_subsubtype][arg_i-3]['role']
                    args.append({'ldc_role':ldc_role ,'xpo_role':role,'constraints':constraints})
                
                xpo_events[current_LDC_event] = {'WD_Qnode':WD_Qnode,'args':args}

    return events, xpo_events
    
def gen_brat_config(events, file_handle):
    for ev_type,subtypes in events.items():
        file_handle.write(f'!{ev_type}\n')
        for ev_subtype,subsubtypes in subtypes.items():
            file_handle.write(f'\t!{ev_subtype}\n')
            for ev_subsubtype, args in subsubtypes.items():
                # handle e.g.'unspecified - explosion'
                ev_subsubtype = ev_subsubtype.replace(' - ','-')
                ev_subsubtype = ev_subsubtype.replace(' ','-')
                arg_string = ''
                for arg in args:
                    role = arg['role']
                    role = role.replace(' ','_')
                    # handle Participant
                    if role in arg_string:
                        role = role + '1?:'
                    else:
                        role = role + '*:'

                    constraints = arg['constraints']
                    role = role.replace('/','_')
                    arg_string = arg_string + role + '|'.join(constraints) + ', '
                arg_string = arg_string[:-2]
                arg_string = arg_string.replace('EVENT','<EVENT>')
                file_handle.write(f'\t\t{ev_type}_{ev_subtype}_{ev_subsubtype}\t{arg_string}\n') 

if __name__ == '__main__':
    '''convert tsv to json'''
    tsv_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/tsv/Kairos-Events_cheatsheet_v1-merged-7_19.tsv'
    events, xpo_events = get_events_LDC_xpo(tsv_path)
    with open('/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/json/kairos_event_ontology-7_19.json','w') as out:
        json.dump(events, out, indent = 4, sort_keys = True)
    with open('/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/json/kairos_event_ontology_xpo-7_19.json','w') as out:
        json.dump(xpo_events, out, indent = 4, sort_keys = True)
    
    '''gen brat conf'''
    # events_dict = json.load(open('/shared/nas/data/m1/wangz3/brat/Aida_COVID/ontology/kairos_event_ontology-7_19.json'))
    # output_conf_path = './event_config.conf'
    # with open('output_conf_path', 'w') as out_conf:
    #     gen_brat_config(events_dict, out_conf)

