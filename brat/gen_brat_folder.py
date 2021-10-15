import os
from shutil import copyfile
from glob import glob
import argparse

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='create brat folder for a certain dataset')
    parser.add_argument('-ac', '--annotation_conf', help='annotation conf template', default = './annotation_template.conf')
    parser.add_argument('-vc', '--visual_conf', help='visual conf template', default = './visual_template.conf')
    parser.add_argument('-i', '--input_rsd_dir', help='input rsd with ann dir', required=True)
    parser.add_argument('-o', '--output_dir', help='output folder for brat', required=True)

    args = vars(parser.parse_args())

    print('=== config ===')
    annotation_conf_path = args['annotation_conf']
    visual_conf_path = args['visual_conf']
    # TODO:
    # claimid_dict_path
    print('annotation conf: ', annotation_conf_path)
    print('visual conf: ', visual_conf_path)
    input_rsd_dir = args['input_rsd_dir']
    output_dir = args['output_dir']
    print('==============')

    txt_docs = sorted(glob(os.path.join(input_rsd_dir,'*.txt')))
    ann_docs = sorted(glob(os.path.join(input_rsd_dir,'*.ann')))
    assert len(txt_docs) == len(ann_docs)

    for i in range(len(txt_docs)):
        txt = txt_docs[i]
        ann = ann_docs[i]
        doc_basename_txt = os.path.basename(txt)
        doc_basename_ann = os.path.basename(ann)
        doc_name = doc_basename_txt[:-8]
        assert doc_name == doc_basename_ann[:-8]
        
        dir_path = os.path.join(output_dir,doc_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        copyfile(txt,os.path.join(dir_path,doc_basename_txt))
        copyfile(ann,os.path.join(dir_path,doc_basename_ann))
        #TODO: customize annotation doc
        copyfile(annotation_conf_path, os.path.join(dir_path,'annotation.conf'))
        print('done writing ',doc_name)

    copyfile(visual_conf_path, os.path.join(output_dir,'visual.conf'))
    print('==============')
    print('done creating: ', output_dir)