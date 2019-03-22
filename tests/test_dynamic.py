import conllu
import treebank_toolkit as tbtk
from treebank_toolkit.dynamic import ArcEager, ArcHybrid, ArcStandard
import random

f = open("/home/clementine/projects/treebanks/ctb51_zpar/train.conll", 'rt')
sentences = [tbtk.ConllSent.from_conllu(sent) for sent in conllu.parse(f.read())]


# gold tree recovery test, though ambiguity in transitions, the gold tree constructed is the same
eager = ArcEager()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		valid = eager._valid_transitions(state)
		oracle = eager.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Eager::oracle: ", oracle)
		g = random.choice(oracle)
		state = eager.step(state, g)
	assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])

hybrid = ArcHybrid()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		valid = hybrid._valid_transitions(state)
		oracle = hybrid.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Hybrid::oracle: ", oracle)
		g = random.choice(oracle)
		state = hybrid.step(state, g)
	assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])

	
std = ArcStandard()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		#print(state.sent.children)
		#print(state.stack, list(reversed(state.buf)))
		valid = std._valid_transitions(state)
		oracle = std.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Standard::oracle: ", oracle)
		g = random.choice(oracle)
		state = std.step(state, g)
	assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])

# when not in gold path, may be there is more than one oracle
# when deviated from the gold path, dynamic oracle is still available to guide the parser
# to generate a sub-optimal tree
eager = ArcEager()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		valid = eager._valid_transitions(state)
		oracle = eager.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Eager::oracle: ", oracle)
		g = random.choice(valid)
		state = eager.step(state, g)
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])

hybrid = ArcHybrid()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		valid = hybrid._valid_transitions(state)
		oracle = hybrid.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Hybrid::oracle: ", oracle)
		g = random.choice(valid)
		state = hybrid.step(state, g)
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])
	
std = ArcStandard() 
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		valid = std._valid_transitions(state)
		oracle = std.dynamic_oracle(state)
		if (len(oracle) > 1):
			print("Standard::oracle: ", oracle)
		g = random.choice(valid)
		state = std.step(state, g)
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])


