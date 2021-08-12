import os
import json
import pprint
from collections import defaultdict
from ontology import Ontology
from ltf_util import LTF_util
from glob import glob
from shutil import copyfile

if __name__ == '__main__':
    input_brat_dir = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/annotated_innerframe/scenario_ldc-7-20/covid19_scenario_en'
    ann_files = glob(os.path.join(input_brat_dir,'**/*.rsd.ann'), recursive = True)
    print(f'[INFO]globed {len(ann_files)} files')
    
    event_dict = {}

    for ann_path in ann_files:
        for line in open(ann_path):
            if line.startswith('E'):
                parsed_line = line.split('\t')
                event_type = parsed_line[1].split(' ')[0].split(':')[0]
                args = [arg.strip().split(':')[0] for arg in parsed_line[1].split(' ')[1:]]
                if event_type not in event_dict:
                    event_dict[event_type] = {'mapped_type_name':event_type,'args':{key:key for key in args if key!=''}}
                else:
                    for key in args:
                        if (key not in event_dict[event_type]['args']) and (key != ''):
                            event_dict[event_type]['args'][key] = key
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(event_dict)

    with open('/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/ontology/event_mapping_7-21.json', 'w') as out:
        json.dump(event_dict, out, indent = 4)