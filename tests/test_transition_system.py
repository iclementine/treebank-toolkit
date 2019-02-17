import conllu
import treebank_toolkit as tbtk
from treebank_toolkit import ArcStandard, ArcHybrid, ArcEagerReduce, ArcEagerShift, ArcStandardSwap
import random

f = open("/home/clementine/projects/treebanks/ctb51_zpar/test.conll", 'rt')
sentences = [tbtk.ConllSent.from_conllu(sent) for sent in conllu.parse(f.read())]


def test_transition_system(trans):
	for sent in sentences:
		state = tbtk.State.init_from_sent(sent)
		transitions = []
		
		# test for static oracle - gen
		while not state.is_final():
			g = trans.gold_action(state)
			transitions.append(g)
			state = trans.step(state, g)
		
		# test for static oracle - recover tree
		state = tbtk.State.init_from_sent(sent)
		transitions_iter = iter(transitions)
		while not state.is_final():
			state = trans.step(state, next(transitions_iter))
		assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
		
		# test for tree constraint - random
		state = tbtk.State.init_from_sent(sent)
		while not state.is_final():
			valid = trans._valid_transitions(state)
			ac = random.choice(valid)
			state = trans.step(state, ac)
		assert len([x for x in state.arcs.items() if x[1][0] == 0]) == 1
			
test_transition_system(ArcStandard())
test_transition_system(ArcStandardSwap())
test_transition_system(ArcHybrid())
test_transition_system(ArcEagerReduce())
test_transition_system(ArcEagerShift())


