#from conllu import ConllSent
#from parser_state import State 

"""
Still many bugs, for ArcEager, random action still cannot gurantee it is a tree.
"""

class TransitionSystemBase(object):
    def _valid_transitions(self, parserstate):
        """ Prepares the set of gold transitions given a parser state """
        raise NotImplementedError()

    def step(self, parserstate, action):
        """ Move a step to a new parser state given an action """
        raise NotImplementedError()

    def gold_action(self, parserstate, goldrels):
        """ Returns the next gold transition given the set of gold arcs """
        raise NotImplementedError()

    def action_to_str(self, transition, state, pos, fpos=None):
        raise NotImplementedError()

    @classmethod
    def action_from_line(cls, line):
        raise NotImplementedError()

    @classmethod
    def actions_list(cls):
        return cls._actions_list
    
class ArcStandard(TransitionSystemBase):
    _actions_list = ["Shift", "Left-Reduce", "Right-Reduce"]
    
    def _valid_transitions(self, parser_state):
        SHIFT, LEFT, RIGHT = self._actions_list
        
        stack, buf = parser_state.stack, parser_state.buf
        
        valid_transitions = []
        
        if len(buf) > 0:
            valid_transitions.append(SHIFT)
        if len(stack) > 2:
            valid_transitions.extend([LEFT, RIGHT])
        elif len(stack) == 2 and len(buf) == 0:
            valid_transitions = [RIGHT]
        
        return valid_transitions
    
    def step(self, parser_state, action):
        """
        action is a tuple of str 
        """
        SHIFT, LEFT, RIGHT = self._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, "_"
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = self._valid_transitions(state)
        assert tsn in cand
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
        elif tsn == LEFT:
            arcs[stack[-2]] = (stack[-1],  lbl) 
            stack.pop(-2)
        elif tsn == RIGHT:
            arcs[stack[-1]] = (stack[-2], lbl)
            stack.pop()
        
        return state
    
    def gold_action(self, parser_state):
        """
        derive next gold action from reference, which in included in the parser_state.
        """
        SHIFT, LEFT, RIGHT = self._actions_list
        
        stack = parser_state.stack
        buf = parser_state.buf
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        deprels = parser_state.sent.deprel
        stack_top_children = parser_state.sent.children[stack[-1]]
        
        stack_top_done = True
        for x in buf:
            if x in stack_top_children:
                stack_top_done = False
                break
        
        if len(stack) > 2 and heads[stack[-2]] == stack[-1]:
            lbl = deprels[stack[-2]]
            tsn = LEFT
        elif len(stack) > 1 and heads[stack[-1]] == stack[-2] and stack_top_done:
            lbl = deprels[stack[-1]]
            tsn = RIGHT
        else:
            lbl = upos[buf[-1]]
            tsn = SHIFT
        
        return (tsn, lbl)
    
    def action_to_str(self, action, control="normal"):
        SHIFT, LEFT, RIGHT = self._actions_list
        
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        if control == "normal":
            if tsn == SHIFT:
                return tsn
            else:
                return "{}_{}".format(tsn, lbl)
        elif control == "backbone":
            return tsn
        elif control == "joint":
            return "{}_{}".format(tsn, lbl)

class ArcHybrid(ArcStandard):
    _actions_list = ["Shift", "Left-Reduce", "Right-Reduce"]
    def _valid_transitions(self, parser_state):
        SHIFT, LEFT, RIGHT = self._actions_list
        
        stack, buf, arcs = parser_state.stack, parser_state.buf, parser_state.arcs
        
        valid_transitions = []
        
        if len(buf) > 0:
            valid_transitions.append(SHIFT)
        if len(buf) > 0 and len(stack) > 1:
            valid_transitions.append(LEFT)
        if len(stack) > 2 and stack[-1] not in arcs:
            valid_transitions.append(RIGHT)
        if len(stack) == 2 and len(buf) == 0:
            valid_transitions = [RIGHT]
        
        return valid_transitions
        
    def step(self, parser_state, action):
        SHIFT, LEFT, RIGHT = self._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = self._valid_transitions(state)
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
        elif tsn == LEFT:
            arcs[stack[-1]] = (buf[-1], lbl)
            stack.pop()
        elif tsn == RIGHT:
            arcs[stack[-1]] = (stack[-2], lbl)
            stack.pop()
        
        return state
    
    def gold_action(self, parser_state):
        """
        derive next gold action from reference, which in included in the parser_state.
        """
        SHIFT, LEFT, RIGHT = self._actions_list
        
        stack = parser_state.stack
        buf = parser_state.buf
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        deprels = parser_state.sent.deprel
        
        stack_top_children = parser_state.sent.children[stack[-1]]
        stack_top_done = True
        for x in buf:
            if x in stack_top_children:
                stack_top_done = False
                break
            
        if len(buf) > 0 and heads[stack[-1]] == buf[-1]:
            lbl = deprels[stack[-1]]
            tsn = LEFT
        elif len(stack) > 1 and heads[stack[-1]] == stack[-2] and stack_top_done:
            lbl = deprels[stack[-1]]
            tsn = RIGHT
        else:
            lbl = upos[buf[-1]]
            tsn = SHIFT
        
        return (tsn, lbl)
    
class ArcEagerReduce(TransitionSystemBase):
    _actions_list = ["Shift", "Left-Arc", "Right-Arc", "Reduce"]
    
    def _valid_transitions(self, parser_state):
        SHIFT, LEFT, RIGHT, REDUCE = self._actions_list
        
        stack, buf, tags, arcs = parser_state.stack, parser_state.buf, parser_state.tags, parser_state.arcs
        
        valid_transitions = []
        
        if len(buf) > 1:
            valid_transitions.append(SHIFT)
        if len(buf) > 0 and len(stack) > 1 and stack[-1] in arcs:
            valid_transitions.append(REDUCE)
        
        left_possible = False
        if len(buf) > 0 and len(stack) > 1 and stack[-1] not in arcs:
            valid_transitions.append(LEFT)
            left_possible = True
        
        if (len(buf) > 0) or (len(buf) == 1 and not left_possible): #TODO: future checking
            valid_transitions.append(RIGHT)
            
        return valid_transitions
    
    def step(self, parser_state, action):
        SHIFT, LEFT, RIGHT, REDUCE = self._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, "_"
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = self._valid_transitions(state)
        assert tsn in cand
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
        elif tsn == LEFT:
            arcs[stack[-1]] = (buf[-1], lbl)
            stack.pop()
        elif tsn == RIGHT:
            tags[buf[-1]] = lbl
            arcs[buf[-1]] = (stack[-1], lbl)
            stack.append(buf.pop())
        else:
            tags[stack[-1]] = lbl
            stack.pop()
        
        return state
    
    def gold_action(self, parser_state):
        SHIFT, LEFT, RIGHT, REDUCE = self._actions_list
        
        stack = parser_state.stack
        buf = parser_state.buf
        arcs = parser_state.arcs
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        deprels = parser_state.sent.deprel
        
        stack_top_children = parser_state.sent.children[stack[-1]]
        stack_top_done = True
        for x in buf:
            if x in stack_top_children:
                stack_top_done = False
                break
        
        if heads[stack[-1]] == buf[-1]:
            lbl = deprels[stack[-1]]
            tsn = LEFT
        elif heads[buf[-1]] == stack[-1]:
            lbl = deprels[buf[-1]]
            tsn = RIGHT
        elif stack[-1] in arcs and stack_top_done:
            lbl = upos[stack[-1]]
            tsn = REDUCE
        else:
            lbl = upos[buf[-1]]
            tsn = SHIFT
        
        return (tsn, lbl)
    
    def action_to_str(self, action, control="normal"):
        SHIFT, LEFT, RIGHT, REDUCE = self._actions_list
        
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        if control == "normal":
            if tsn == SHIFT or tsn == REDUCE:
                return tsn
            else:
                return "{}_{}".format(tsn, lbl)
        elif control == "backbone":
            return tsn
        elif control == "joint":
            return "{}_{}".format(tsn, lbl)

