import conllu
import treebank_toolkit as tbtk
from treebank_toolkit.dynamic import ArcEager, ArcHybrid
import random

eager = ArcEager()
f = open("/home/clementine/projects/treebanks/ctb51_zpar/dev.conll", 'rt')
sentences = [tbtk.ConllSent.from_conllu(sent) for sent in conllu.parse(f.read())]
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		oracle = eager.dynamic_oracle(state)
		#print(oracle)
		g = random.choice(oracle)
		state = eager.step(state, g)
	assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])

hybrid = ArcHybrid()
for sent in sentences:
	state = tbtk.State.init_from_sent(sent)
	while not state.is_final():
		oracle = hybrid.dynamic_oracle(state)
		#print(oracle)
		g = random.choice(oracle)
		state = hybrid.step(state, g)
	assert([state.arcs[x][0] for x in range(1, len(sent) + 1)] == sent.head[1:])
	#print([state.arcs[x][0] for x in range(1, len(sent) + 1)])
	#print(sent.head[1:])
