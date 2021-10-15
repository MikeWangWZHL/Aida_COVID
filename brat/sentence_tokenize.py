from os import listdir
from os.path import isfile, join
from nltk.tokenize import sent_tokenize, word_tokenize
from tqdm import tqdm


inputpath = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/brat/Scenario/es/rsd_untokenized'
outpath = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/brat/Scenario/es/rsd_tokenized'
files = [f for f in listdir(inputpath) if isfile(join(inputpath, f))]

for f in tqdm(files):    
    lines = []
    with open(join(inputpath,f), 'r',encoding = 'utf-8') as doc:
        for line in doc:
            lines += sent_tokenize(line)
    # new_f = f[:-4] + '.rsd.txt'
    new_f = f
    with open(join(outpath,new_f),'w',encoding = 'utf-8') as outdoc:
        for line in lines:
            outdoc.write(line + '\n')
    
