import argparse
import conllu
import treebank_toolkit as tbtk

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--trans", type=str, 
                    choices=['arc-standard', 'arc-hybrid', 'arc-eager-reduce', 'arc-eager-shift', 'arc-standard-swap'],
                    help='transition system to use', 
                    default='arc-standard-swap')
parser.add_argument("-p", "--pos", type=str, choices=['upos', 'xpos'], help="pos column to choose", default='upos')
parser.add_argument("-f", "--format", type=str, choices=['normal', 'backbone'], help="format for transitions")
# it is better to use argparse.FileType if the arg represent a file path, it would open it automatically
parser.add_argument("corpus", type=argparse.FileType('rt', encoding='utf-8'), help="conllcorpus to process")


transition_systems = {
  'arc-standard': tbtk.ArcStandard,
  'arc-hybrid': tbtk.ArcHybrid,
  'arc-eager-reduce': tbtk.ArcEagerReduce,
  'arc-eager-shift': tbtk.ArcEagerShift,
  'arc-standard-swap': tbtk.ArcStandardSwap}

def transduce(corpus, trans, control='normal', pos='upos'):
  """
  args:
    corpus: TextIOWrapper, the corpus to process
    trans: tbtk.TransitionSystemBase object
    control: str, format of the transition, backbone or normal
    pos: str, which pos column to choose, upos or xpos
  """
  sentences = [tbtk.ConllSent.from_conllu(sent) for sent in conllu.parse(corpus.read())]
  for s in sentences:
    transitions = []
    state = tbtk.State.init_from_sent(s)
    while not state.is_final():
      g = trans.gold_action(state)
      transitions.append(trans.action_to_str(g))
      state = trans.step(state, g)
    s.transitions = transitions
    print("form:", ' '.join(s.form))
    print("pos:", ' '.join(s.upos if pos == 'upos' else s.xpos))
    print("head:", ' '.join(str(x) for x in s.head))
    print("deprel:", ' '.join(s.deprel))
    print("transitions:", ' '.join(s.transitions))
    print()

if __name__ == "__main__":
  args = parser.parse_args()
  corpus = args.corpus
  format = args.format
  pos = args.pos
  trans = transition_systems[args.trans]()
  transduce(corpus, trans, control=format, pos=pos)

  
