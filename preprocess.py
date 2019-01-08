import os
import pickle

import pytext
import conllu

from .parser_state import State
from .sentence import ConllSent
from .transition_system import TransitionSystemBase, ArcStandard, ArcHybrid, ArcEagerReduce, ArcEagerShift, ArcStandardSwap

def build_vocab(fp, vp, columns=['form', 'xpos', 'deprel', 'transition'], encoding='utf-8', verbose=True):
    """
    A utility function to build vocabularies from conllu corpus. It is
    constrained only to build vocab for some specific fields, and no 
    oracles are generated.
    """
    if verbose:
        print("Selected rows are {}".format(columns))
    fields = [(column, pytext.data.Field(tokenize=list)) for column in columns]
    with open(fp, 'rb') as f:
        sentences = pickle.load(f)
        examples = [pytext.data.Example.fromlist(
            [sent.__getattribute__(column) for column in columns], fields) 
            for sent in sentences]
        data = pytext.data.Dataset(examples, fields)
        for column, field in fields:
            field.build_vocab(data)
        with open(vp, 'wb') as g:
            pickle.dump(fields, g)
            if verbose:
                print("vocabulary is saved at {}".format(vp))
                
def gen_oracle(fp, op, transition_system, control='normal', verbose=True, encoding='utf-8'):
    if verbose:
        print("Selected transition system is {}".format(transition_system))
    with open(fp, 'rt', encoding=encoding) as f:
        sentences = [ConllSent.from_conllu(sent) for sent in conllu.parse_incr(f)]
        selected_sents = []
        if transition_system == "ArcStandard":
            trans = ArcStandard()
        elif transition_system == "ArcHybrid":
            trans = ArcHybrid()
        elif transition_system == "ArcEagerReduce":
            trans = ArcEagerReduce()
        elif transition_system == "ArcEagerShift":
            trans = ArcEagerShift()
        elif transition_system == "ArcStandardSwap":
            trans = ArcStandardSwap()
            
        for sent in sentences:
            try:
                oracle = []
                state = State.init_from_sent(sent)
                while not state.is_final():
                    action_g = trans.gold_action(state)
                    oracle.append(trans.action_to_str(action_g, control=control))
                    state = trans.step(state, action_g)
                sent.transition = oracle
                selected_sents.append(sent)
            except:
                pass
        if not transition_system == "ArcStandardSwap":
            skipped = len(sentences) - len(selected_sents)
            print("Skipped {} non-projective sentences!".format(skipped))
        with open(op, 'wb') as g:
            pickle.dump(selected_sents, g)
            if verbose:
                print("corpus is saved at {}".format(op))
