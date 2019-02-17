# Treebank Toolkit

## Purpose of treebank toolkit

While there are already many toolkits for assisting NLP developments about parsing and treebank processings, like NLTK, scipy, and some auxiliary scripts in ZPar, etc, I still wants to develop a toolkit to make developing transition based dependency parser a bit easier. As those who are interested in dependency parsing, especially transition-based dependency parsing, may be impressed by the simplicity and strictness of of transition systems and their constraints that guarantee that the result must be a valid tree. The most importance achievements in the developemnts of transition system were made by Joakim Nivre. Arc Standard and Arc Eager were Nivre's masterpieces. Then other transition systems were made, like Arc Hybrid, Arc Swift, Arc Standard with swap.

In order to develop a transition-based parser there are 2 prerequisites:

Given a dependency annotated sentence, we shall derive gold transition sequence, the oracle. There are two kinds of oracles, the static and the dynamic. Static oracle assumes that there should only one valid transition sequence to derive a dependency tree. In practice, we would regard the process of deriving an oracle from a dependency tree as a kind of equivalent transformation and perform such a transformation for the whole treebank before we start to train a dependency parser. Though actually, there may be several sequences that construct the same tree unless we rigidly pose some preferance of some actions over others. Dynamic oracle, contrastively, treat all the sequence that can construct the same dependency tree equally. At every time step(parse state), it allows several transitions if they do not lead to worse parse states. As a result, we do not perform the transformation before we train a dependency parser, but instead, integrated into the parser. At each time step, it generate a set of gold actions that can lead to the gold dependency tree and the parser is allowed to choose any one of them.

Constraints for valid transitions at each time step. Being a valid transition is a looser constraint that it does not require a reference dependency tree. It only requires that a valid transition is possible and that it would not make it impossible to construct a tree after taking that transition. So randomly choosing from valid actions at each timestep would result in a valid dependency tree although it may not be the reference dependency tree.

## Abstractions Functionalites

`ConllSent` is a representation of a conll-annotated sentence.

1. `form, upos, xpos, head, deprel` are fields in conll file.
2. `children` is a list of list of int, meaning each node's children.

`State` is a parse state.

1. `sent`, the ConllSent object the state is tied to.
2. `stack`, the stack, a list of int, a init state has only 0 in it.
3. `buf`, the buffer, a list of int, a terminal state has nothing in it.
4. `seen_the_end`, boolean, an identifier whether the parsing process has ever reached a state where the buffer is empty.
5. `tags`, dict(int -> str), POS tags.
6. `arcs`, dict(int -> tuple(int, str)), a word's head idx and deprel.


`TransitionSystemBase`

1. `_actions_list`, list(str), possible transitions for the transition system

2. `_valid_transitions(cls, parser_state)`, get a list of valid transitions given a parser state

3. step(cls, parserstate, action), take a step and return a new parser state given a state and an action

4. gold_action(cls, parser_state), returns the next gold transition given the dependency tree(the sent object in the parser state)

5. action_to_str(cls, action, control), an auxiliary function to transform an action, tuple(transition, label) to a str, which is useful when used with pytext or other toolkits, because mapping from a string to an integer is the standard process for deep learning based NLP developments. But due to different schemes, the representation of an action my be different, sometimes we just need backbone dependency structure, and sometimes labels are considered, and may be tags are integrated into shift or reduce. Modifing a function for deifferent scheme is prone to cause bugs. so we add a layer of abstraction and use the same internal representation for actions.

5. str_to_action(cls, action, control), an auxiliary function to transform a str to action, tuple(transition, label), which is useful when used with pytext or other toolkits, because mapping from a string to an integer is the standard process for deep learning based NLP developments. But due to different schemes, the representation of an action my be different, sometimes we just need backbone dependency structure, and sometimes labels are considered, and may be tags are integrated into shift or reduce. Modifing a function for deifferent scheme is prone to cause bugs. so we add a layer of abstraction and use the same internal representation for actions.

**UPDATE** : due to the difference of transition systems, integrating tags with transition in transition systems other than arc standard is not that straight forward, tagging is an action that can be attached to shifting and reducing and even swappping. So there is not real consistency in integrating tagging and transition. So developers may need to do this mannually.

By the way, their are actually other things I do not consider, prepend / append a virtual `<root>` for every sentence, adding a `</s>` for every sentence or not. I just prepend a `<root>` for every sentence and treat it a standard process for simoplicity.

All are tested. Given a sentence and a dependency tree, it can generate static oracle by rules. And given a sentence, and follow randomly an action from the generated valid_actions, it can always generate a valid tree, and ends with len(stack) = 1 and len(buffer) = 0.

But unfortuantely, I made things too complicated and it seems that too many options made it difficult to maintain and reusability is not that easy. I had planned to eventually use it as a transition system that would generate dynamic oracle, that is why I tried to made State separate from each other except for the sentence in it. But Parsers with dynamic oracles seem to integrate with the transition system tightly, even you have a transition system that derives dynamic oracle, your parser will have to maintain someting like a transition syetem and all its stacks and buffers(for example, in the stackLSTM model), if you just try to separate them, you would have to write two parts of code in parallel, one for the transition system which manipulate states, and a parser which manipulates its own states. Then the parser tells which action to take, and you have to update two states in parallel. That's ugly. So I decided to just use it for static oracle generation.

So if you just use it for before-hand static oracle generation, it is still clean and neat if you don't look into the details.

## Update

Now, ArcStandard, ArcHybrid, ArcStandardSwap, ArcEagerShift and ArcEagerReduce are all added. Only ArcStandardSwap handles non-projective sentences.

Added Dynamic Oracle for ArcHybrid and ArcEager.

Add `transduce_corpus.py` to process a conll treebank directly, and save the result to a text file that is easily parsed by other programming languages.

## Usage

```
import conllu
from sentence import ConllSent
from parser_state import State
from transition_system import *
import dynamic
import random

fname = "path/to/the/conll/file"
with open(fname, 'rt') as f:
    content = f.read()
    sentences = conllu.parse(content)

sent = ConllSent.from_conllu(sentences[10])
state = State.init_from_sent(sent)

std = ArcStandard()

# randomly generate a tree
while not (len(state.stack) == 1 and len(state.buf) == 0):
    actions = std._valid_transitions(state)
    random_act = random.choice(actions)
    print(std.action_to_str(random_act))
    state = std.step(state, random_act)


state = State.init_from_sent(sent)
std = ArcStandard()

# static oracle
while not (len(state.stack) == 1 and len(state.buf) == 0):
    gold_action = std.gold_action(state)
    print(std.action_to_str(gold_action))
    state = std.step(state, gold_action)
    
# dynamic oracle
state = State.init_from_sent(sent)
eager = dynamic.ArcEager()
while not state.is_final():
    oracle = eager.dynamic_oracle(state)
    print(oracle)
    g = random.choice(oracle)
    state = eager.step(state, g)
```

## transduce a corpus

cmdline usage

```bash
python transduce_corpus.py -t arc-standard-swap -p upos -f normal train.conll > train.txt
```

Enjoy the simplicity!



