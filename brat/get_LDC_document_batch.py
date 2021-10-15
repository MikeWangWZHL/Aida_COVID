import os
import json
from collections import defaultdict
from shutil import copyfile


if __name__ == '__main__':
    assignment_file_path = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/brat/Aida_hackathon/aida_hackathon_hw_9-21/assignment.txt'
    parent_child_tab = '/shared/nas/data/m1/AIDA_Data/LDC_raw_data/LDC2021E11_AIDA_Phase_3_Practice_Topic_Source_Data_V2.0/docs/parent_children.tab'
    ltf_dir = '/shared/nas/data/m1/AIDA_Data/LDC_raw_data/LDC2021E11_AIDA_Phase_3_Practice_Topic_Source_Data_V2.0/data/ltf/ltf'
    output_root = '/shared/nas/data/m1/wangz3/brat/Aida_Kairos_COVID/brat/Aida_hackathon/aida_hackathon_hw_9-21'
    output_en = f'{output_root}/ltf/en'
    output_es = f'{output_root}/ltf/es'
    if not os.path.exists(output_en):
        os.makedirs(output_en)
    if not os.path.exists(output_es):
        os.makedirs(output_es)
    
    text_doc_ids = defaultdict(list)
    en_parent_ids = []
    es_parent_ids = []
    with open(assignment_file_path) as f:
        for line in f:
            if line.startswith('topic_id'):
                continue
            else:
                topic_id, lang, parent_id = [i.strip() for i in line.split('\t')]
                if lang == 'English':
                    en_parent_ids.append(parent_id)
                elif lang == 'Spanish':
                    es_parent_ids.append(parent_id)
    print('en:',en_parent_ids)
    print('es:',es_parent_ids)
    

    with open(parent_child_tab) as f:
        for line in f:
            if line.startswith('catalog_id'):
                continue
            else:
                parsed_line = line.split('\t')
                parent_id = parsed_line[2]
                child_id = parsed_line[3]
                data_type = parsed_line[5]
                topic = parsed_line[6]
                if data_type == '.ltf.xml':
                    if parent_id in en_parent_ids:
                        text_doc_ids['en'].append((child_id,topic))
                    elif parent_id in es_parent_ids:
                        text_doc_ids['es'].append((child_id,topic))
    print(text_doc_ids)
    with open(f'{output_root}/child_topic_list.txt','w') as child_topic_f:
        child_topic_f.write(f'child_id\ttopic_id\n')
        for pair in text_doc_ids['en']:
            en_child_id,topic = pair
            src = os.path.join(ltf_dir,f'{en_child_id}.ltf.xml')
            dst = os.path.join(output_en,f'{en_child_id}.ltf.xml')
            copyfile(src, dst)
            
            child_topic_f.write(f'{en_child_id}\t{topic}\n')
        for pair in text_doc_ids['es']:
            es_child_id,topic = pair
            src = os.path.join(ltf_dir,f'{es_child_id}.ltf.xml')
            dst = os.path.join(output_es,f'{es_child_id}.ltf.xml')
            copyfile(src, dst)
            
            child_topic_f.write(f'{es_child_id}\t{topic}\n')


