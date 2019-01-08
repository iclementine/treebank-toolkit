import conllu 
import random
import treebank_toolkit as tbtk

f = open("/home/clementine/projects/treebanks/ptb/train.dep", 'rt')                                                                       
content = f.read()                                                                              
sentences = conllu.parse(content)                                                               
sents = [tbtk.ConllSent.from_conllu(sent) for sent in sentences]                                               

asw = tbtk.ArcStandardSwap()                                                                    
#for sent in sents:
    #state = tbtk.State.init_from_sent(sent)
    #while not (len(state.stack) == 1 and len(state.buf) == 0): 
        #g = asw.gold_action(state) 
        #print(asw.action_to_str(g)) 
        #state = asw.step(state, g)
        
for sent in sents:
    state = tbtk.State.init_from_sent(sent)
    while not (len(state.stack) == 1 and len(state.buf) == 0): 
        actions = asw._valid_transitions(state)
        g = random.choice(actions)
        print(asw.action_to_str(g)) 
        state = asw.step(state, g)
