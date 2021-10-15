import json
import os
import requests
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import torch
from Levenshtein import ratio, seqratio

def check_topic_subtopic(claim1, claim2):
    if claim1['claim_frame']['topic'] == claim2['claim_frame']['topic'] and \
        claim1['claim_frame']['subtopic'] == claim2['claim_frame']['subtopic']:
        return True
    else:
        return False

def check_epistemic(claim1, claim2):
    # only look at true/false, ignore certain/uncertain
    if claim1['claim_frame']['epistemic'].split('-')[0].strip() == \
        claim2['claim_frame']['epistemic'].split('-')[0].strip():
        return True
    else:
        return False

class QnodeSim:
    def __init__(self, mode = None):
        """
            mode choose from [complex, transe, text, class]
        """
        if mode is None:
            mode = 'complex'
        self.mode = mode

    def __call__(self, q1,q2):
        filled_request = f'https://kgtk.isi.edu/similarity_api?q1={q1}&q2={q2}&embedding_type={self.mode}'
        r = requests.get(filled_request)
        r_dict = json.loads(r.text)
        if 'error' in r_dict:
            # Qnode may not be found
            error_msg = r_dict['error']
            print(f'INFO: {error_msg}, return 0 score')
            return 0
        else:
            return r_dict['similarity']

class StringSim:
    def __init__(self, mode = None, device = 'cuda:3'):
        """
            mode:
                'exact': exact match return 1, otherwise return 0
                'bert': return cosine similarity of bert embedding between two strings
                'lev': return similarity score calculated by Levenshtein (edit) distance
        """
        if mode is None:
            mode = 'exact'
        self.mode = mode
        
        if self.mode == 'bert':
            if torch.cuda.is_available():  
                dev = device 
            else:  
                dev = "cpu"
            # CUDA_VISIBLE_DEVICES=0,1,2,3  
            self.device = torch.device(dev)
            
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            self.model = BertModel.from_pretrained('bert-base-uncased').to(self.device)


    def __call__(self, s1, s2):
        if self.mode == 'exact':
            if s1 == s2:
                return 1
            else:
                return 0
        
        if self.mode == 'bert':
            inputs_1 = self.tokenizer(s1,return_tensors="pt").to(self.device)
            inputs_2 = self.tokenizer(s2,return_tensors="pt").to(self.device)
            pooler_output_1 = self.model(**inputs_1).pooler_output
            pooler_output_2 = self.model(**inputs_2).pooler_output
            # print(pooler_output_1.size())
            # print(pooler_output_2.size())
            return cosine_similarity(
                pooler_output_1.detach().cpu().numpy(),
                pooler_output_2.detach().cpu().numpy() 
                )[0][0]
        
        if self.mode == 'lev':
            return ratio(s1, s2)


        
class KE_Sim:
    def __init__(self, level = None, merge = True, weights = None, string_match_mode = 'exact'):
        if level is None:
            level = 3
        # if weights is None:
        #     weights = 
        self.level = level
        self.merge = merge
        self.weights = weights
        self.stringmatcher = StringSim(mode=string_match_mode)
    
    def pairwise_ke_compare(self, ke1, ke2):
        
        if 'eventmention_id' in ke1:
            assert 'eventmention_id' in ke2, "ke1 is an event but ke2 is not an event"
            trigger_match_score = self.stringmatcher(ke1['text_string'],ke2['text_string'])
            arg_match_count = 0
            for arg1 in ke1['arguments']:
                for arg2 in ke2['arguments']:
                    if arg1['arg_id'] == arg2['arg_id'] and arg1['slot_type'] == arg2['slot_type']:
                        arg_match_count += 1
            arg_match_score = arg_match_count / max(len(arg1['arguments']),len(arg2['arguments']))

        elif 'relationmention_id' in ke1:
            assert 'relationmention_id' in ke2, "ke1 is a relation but ke2 is not a relation"
            trigger_match_score = None
            arg_match_count = 0
            if ke1['arguments']['arg1']['arg_id'] == ke2['arguments']['arg1']['arg_id']:
                arg_match_score += 1
            if ke1['arguments']['arg2']['arg_id'] == ke2['arguments']['arg2']['arg_id']:
                arg_match_score += 1
            arg_match_score = arg_match_count / 2          

        type_match = (ke1['type'] == ke2['type'])
        subtype_match = (ke1['subtype'] == ke2['subtype'])
        subsubtype_match = (ke1['subsubtype'] == ke2['subsubtype'])

        return type_match, subtype_match, subsubtype_match, trigger_match_score, arg_match_score


    def __call__(self, claim1, claim2):
        
        CF1 = claim1['claim_frame']
        CF2 = claim2['claim_frame']
        KEs1 = claim1['KEs']
        KEs2 = claim2['KEs']
        events1 = KEs1['events']
        events2 = KEs2['events']
        relations1 = KEs1['relations']
        relations2 = KEs2['relations']
        
        claim_semantics_1 = []
        claim_semantics_2 = []
        
        for c_s_id in CF1['claim_semantics']:
            if c_s_id in events1:
                claim_semantics_1.append(events1[c_s_id])
            else:
                claim_semantics_1.append(relations1[c_s_id])
        
        for c_s_id in CF2['claim_semantics']:
            if c_s_id in events2:
                claim_semantics_2.append(events2[c_s_id])
            else:
                claim_semantics_2.append(relations2[c_s_id])

        

        

class ClaimEquiv:
    def __init__(self, 
        claimer_metric = None, 
        claimer_threshold = 0.5,
        x_varible_metric = None,
        x_varible_threshold = 0.5,
        NL_description_metric = None,
        NL_description_threshold = 0.5,
        KE_metric = None,
        KE_metric_threshold = 0.5
    ):
        if claimer_metric is None:
            claimer_metric = {'type':'qnode', 'func':QnodeSim(mode='complex')}
        if x_varible_metric is None:
            x_varible_metric = {'type':'qnode', 'func':QnodeSim(mode='complex')}
        if NL_description_metric is None:
            NL_description_metric = StringSim(mode='bert')
        if KE_metric is None:
            KE_metric = KE_Sim(level = 1, merge = True, weights = None)
        
        self.claimer_metric = claimer_metric
        self.claimer_threshold = claimer_threshold
        self.x_varible_metric = x_varible_metric
        self.x_varible_threshold = x_varible_threshold
        self.NL_description_metric = NL_description_metric
        self.NL_description_threshold = NL_description_threshold
        self.KE_metric = KE_metric
        self.KE_metric_threshold = KE_metric_threshold


    def __call__(self, claim1, claim2):
        """ Rules:
        - claim topic and subtopic should be same
        - Epistemic should be the same (true/false)
        - claimer should be the same (i.e., link to the same Qnode)
        - claim natural language description similarity higher than a thershold
        - claim semantic KE similarity (multiple levels: type similarity, trigger similarity, argument similarity)
        """

        '''check topic and subtopic'''
        if not check_topic_subtopic(claim1, claim2):
            print('Topic/Subtopic does not match, return False')
            return False

        '''check epistemic'''
            print('Epistemic does not match, return False')
        if not check_epistemic(claim1, claim2):
            return False

        CF1 = claim1['claim_frame']
        CF2 = claim2['claim_frame']

        '''check claimer'''
        if self.claimer_metric['type'] == 'qnode':
            claimer_sim_score = self.claimer_metric['func'](CF1['claimer_qnode'], CF2['claimer_qnode'])
        elif self.claimer_metric['type'] == 'string':
            claimer_sim_score = self.claimer_metric['func'](CF1['claimer'], CF2['claimer'])
        print('claimer sim score:', claimer_sim_score)
        '''check x_varible'''
        if self.x_varible_metric['type'] == 'qnode':
            x_varible_sim_score = self.x_varible_metric['func'](CF1['x_qnode'], CF2['x_qnode'])
        elif self.x_varible_metric['type'] == 'string':
            x_varible_sim_score = self.x_varible_metric['func'](CF1['x_varible'], CF2['x_varible'])
        print('x varible sim score:', x_varible_sim_score)

        '''check NL description'''
        NL_description_sim_score = self.NL_description_metric(CF1['NL_description'], CF2['NL_description'])
        print('NL description sim score:', NL_description_sim_score)
        
        '''check KEs'''

def main():
    document_output_json = './L0C049DQW.json'
    output_dict = json.load(open(document_output_json))
    doc_id = output_dict['doc_id']
    claims = output_dict['claims']

    claim1 = claims[0]
    claim2 = claims[1]

    print(claim1['claim_frame']['claim_id'])
    print(claim2['claim_frame']['claim_id'])

    # check equivalence
    checker = ClaimEquiv()
    checker(claim1, claim2)

if __name__=="__main__":
    main()

    ###################################
    '''unit test: QnodeSim'''
    # qnode_sim_checker = QnodeSim()
    # q1 = 'Q144'
    # q2 = 'Q146'
    # qnode_sim = qnode_sim_checker(q1,q2)
    # print(qnode_sim)

    '''unit test: StringSim, bert'''
    # string_sim_checker = StringSim(mode='bert')
    # s1 = 'You are awesome!'
    # s2 = 'Compute cosine similarity between samples in X and Y'
    # # s1 = 'You are awesome!'
    # # s2 = 'You are mean!'
    # print(string_sim_checker(s1,s2))