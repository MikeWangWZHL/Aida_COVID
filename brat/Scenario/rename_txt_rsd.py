import os
from glob import glob

txt_path = '/shared/nas/data/m1/wangz3/brat/Aida_COVID/brat/Scenario/es/rsd_untokenized'

for fp in glob(os.path.join(txt_path,'*')):
    basename = os.path.basename(fp).replace('.txt','')
    os.rename(fp, f'{txt_path}/{basename}.rsd.txt')