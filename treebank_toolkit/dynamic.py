from treebank_toolkit.sentence import ConllSent
from treebank_toolkit.parser_state import State 


class TransitionSystemBase(object):
    _actions_list = None
    @classmethod
    def _valid_transitions(cls, parserstate):
        """ Prepares the set of gold transitions given a parser state """
        raise NotImplementedError()
    
    @classmethod
    def step(cls, parserstate, action):
        """ Move a step to a new parser state given an action """
        raise NotImplementedError()

    @classmethod
    def dynamic_oracle(cls, parserstate):
        """ Returns the next gold transition given the set of gold arcs """
        raise NotImplementedError()
    
    @classmethod
    def action_to_str(cls, action, control):
        raise NotImplementedError()

    @classmethod
    def str_to_action(cls, string, control):
        raise NotImplementedError()

    @classmethod
    def actions_list(cls):
        return cls._actions_list
     
class ArcHybrid(TransitionSystemBase):
    _actions_list = ["Shift", "LeftReduce", "RightReduce"]
    @classmethod
    def _valid_transitions(cls, parser_state):
        SHIFT, LEFT, RIGHT = cls._actions_list
        
        stack, buf, arcs = parser_state.stack, parser_state.buf, parser_state.arcs
        
        valid_transitions = []
        
        if len(buf) > 0:
            valid_transitions.append(SHIFT)
        if len(buf) > 0 and len(stack) > 1:
            valid_transitions.append(LEFT)
        if len(stack) > 2:
            valid_transitions.append(RIGHT)
        if len(stack) == 2 and len(buf) == 0:
            valid_transitions = [RIGHT]
        
        return valid_transitions
    
    @classmethod
    def step(cls, parser_state, action):
        SHIFT, LEFT, RIGHT = cls._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = cls._valid_transitions(state)
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
            if len(buf) == 0:
                state.seen_the_end = False
        elif tsn == LEFT:
            arcs[stack[-1]] = (buf[-1], lbl)
            stack.pop()
        elif tsn == RIGHT:
            arcs[stack[-1]] = (stack[-2], lbl)
            stack.pop()
        
        return state
    
    @classmethod
    def dynamic_oracle(cls, parser_state):
        SHIFT, LEFT, RIGHT = cls._actions_list
        valid = cls._valid_transitions(parser_state)
        oracle = []
        
        # state
        stack = parser_state.stack
        buf = parser_state.buf
        # reference
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        children = parser_state.sent.children
        deprels = parser_state.sent.deprel
        
        if SHIFT in valid:
            buffer_top_head = heads[buf[-1]]
            buffer_top_children = children[buf[-1]]
            if not (buffer_top_head in stack[:-1] or any([x in stack for x in buffer_top_children])):
                oracle.append(SHIFT)
            
        if LEFT in valid:
            stack_top_head = heads[stack[-1]]
            stack_top_children = children[stack[-1]]
            if not (stack_top_head in stack[:-1] or stack_top_head in buf[:-1] or any(x in buf for x in stack_top_children)):
                oracle.append(LEFT)
        
        if RIGHT in valid:
            stack_top_head = heads[stack[-1]]
            stack_top_children = children[stack[-1]]
            if not (stack_top_head in buf or any(x in buf for x in stack_top_children)):
                oracle.append(RIGHT)
        return oracle
        
    @classmethod
    def action_to_str(cls, action, control="normal"):
        SHIFT, LEFT, RIGHT = cls._actions_list
        
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        if control == "normal":
            if tsn == SHIFT:
                return tsn
            else:
                return "{}-{}".format(tsn, lbl)
        elif control == "backbone":
            return tsn
    
    @classmethod
    def str_to_action(cls, string, control="normal"):
        SHIFT, LEFT, RIGHT = cls._actions_list
        if control == "normal":
            if string.startswith(SHIFT):
                tsn, lbl = string, "_"
            else:
                tsn, lbl = string.split("-", 1)
        elif control == "backbone":
            tsn, lbl = string, "_"
        return (tsn, lbl)
    

class ArcEager(TransitionSystemBase):
    """
    Modified as Nivre and Fernandex-Gonzalez (2014) `Arc-Eager Parsing with the Tree Constraint`, adding a new transition Unshift and adding a new member in parser state, and the modification to the parser state in extended to all the parser states, even those used with Arc Standard, though it is not needed.
    ref: http://www.aclweb.org/anthology/J14-2002
    """
    _actions_list = ["Shift", "LeftArc", "RightArc", "Reduce", "Unshift"]
    
    @classmethod
    def _valid_transitions(cls, parser_state):
        SHIFT, LEFT, RIGHT, REDUCE, UNSHIFT = cls._actions_list
        
        stack, buf, tags, arcs = parser_state.stack, parser_state.buf, parser_state.tags, parser_state.arcs
        
        valid_transitions = []

        if len(buf) > 1 and not parser_state.seen_the_end: # before we have seen the end
            valid_transitions.append(SHIFT)
            
        if len(buf) == 0 and parser_state.seen_the_end and stack[-1] not in arcs:
            valid_transitions.append(UNSHIFT)
                
        if (len(stack) > 2 or len(stack) == 2 and len(buf) == 0) and stack[-1] in arcs: 
            valid_transitions.append(REDUCE)
            
        if len(buf) > 0 and len(stack) > 1 and stack[-1] not in arcs:
            valid_transitions.append(LEFT)
            
        if len(buf) > 0 and (len(stack) > 1 or (len(stack) == 1 and not any([arcs[x][0] == 0 for x in arcs]))):
            valid_transitions.append(RIGHT)

        return valid_transitions
    
    @classmethod
    def step(cls, parser_state, action):
        SHIFT, LEFT, RIGHT, REDUCE, UNSHIFT = cls._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, "_"
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = cls._valid_transitions(state)
        assert tsn in cand
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
            if len(buf) == 0:
                state.seen_the_end = True
        elif tsn == LEFT:
            arcs[stack[-1]] = (buf[-1], lbl)
            stack.pop()
        elif tsn == RIGHT:
            #tags[buf[-1]] = lbl # it is safe to do so, only tag when reduce
            arcs[buf[-1]] = (stack[-1], lbl)
            stack.append(buf.pop())
            if len(buf) == 0:
                state.seen_the_end = True
        elif tsn == UNSHIFT:
            buf.append(stack.pop())
        else: #reduce
            tags[stack[-1]] = lbl
            stack.pop()
        
        return state
    
    @classmethod
    def dynamic_oracle(cls, parser_state):
        SHIFT, LEFT, RIGHT, REDUCE, UNSHIFT = cls._actions_list
        valid = cls._valid_transitions(parser_state)
        oracle = []
        
        # state
        stack = parser_state.stack
        buf = parser_state.buf
        arcs = parser_state.arcs
        
        # reference
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        deprels = parser_state.sent.deprel
        children = parser_state.sent.children
        
        if LEFT in valid:
            stack_top_children = children[stack[-1]]
            stack_top_done = True
            for x in buf:
                if x in stack_top_children:
                    stack_top_done = False
                    break
            stack_top_head = heads[stack[-1]]
            if not ((not stack_top_done) or (stack_top_head in buf[:-1])):
                oracle.append(LEFT)
        
        if REDUCE in valid:
            stack_top_children = children[stack[-1]]
            stack_top_done = True
            for x in buf:
                if x in stack_top_children:
                    stack_top_done = False
                    break
            if stack_top_done:
                oracle.append(REDUCE)
        
        if SHIFT in valid:
            buffer_top_children = children[buf[-1]]
            buffer_top_head = heads[buf[-1]]
            if not (buffer_top_head in stack or any(x in stack for x in buffer_top_children)):
                oracle.append(SHIFT)
                
        if RIGHT in valid:
            buffer_top_children = children[buf[-1]]
            buffer_top_head = heads[buf[-1]]
            if not (buffer_top_head in stack[:-1] or buffer_top_head in buf[:-1] or any(x in stack for x in buffer_top_children)):
                oracle.append(RIGHT)
        
        if UNSHIFT in valid:
            oracle = [UNSHIFT]
        return oracle
    
    @classmethod
    def action_to_str(cls, action, control="normal"):
        SHIFT, LEFT, RIGHT, REDUCE, UNSHIFT = cls._actions_list
        
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        if control == "normal":
            if tsn == SHIFT or tsn == REDUCE or tsn == UNSHIFT:
                return tsn
            else:
                return "{}-{}".format(tsn, lbl)
        elif control == "backbone":
            return tsn
        
    @classmethod
    def str_to_action(cls, string, control="normal"):
        """
        Note that if you expect Shift-POS to cover the whole sentence, it is impossible
        """
        SHIFT, LEFT, RIGHT, REDUCE, UNSHIFT = cls._actions_list
        if control == "normal":
            if string.startswith(SHIFT) or string.startswith(REDUCE) or string.startswith(UNSHIFT):
                tsn, lbl = string, "_"
            else:
                tsn, lbl = string.split("-", 1)
        elif control == "backbone":
            tsn, lbl = string, "_"
        return (tsn, lbl)

    
class ArcStandard(TransitionSystemBase):
    _actions_list = ["Shift", "LeftReduce", "RightReduce"]
    
    @classmethod
    def _valid_transitions(cls, parser_state):
        SHIFT, LEFT, RIGHT = cls._actions_list
        
        stack, buf = parser_state.stack, parser_state.buf
        
        valid_transitions = []
        
        if len(buf) > 0:
            valid_transitions.append(SHIFT)
        if len(stack) > 2:
            valid_transitions.extend([LEFT, RIGHT])
        elif len(stack) == 2 and len(buf) == 0:
            valid_transitions = [RIGHT]
        
        return valid_transitions
    
    @classmethod
    def step(cls, parser_state, action):
        """
        action is a tuple of str 
        """
        SHIFT, LEFT, RIGHT = cls._actions_list
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, "_"
        
        state = State.copy(parser_state)
        stack = state.stack
        buf = state.buf
        tags = state.tags
        arcs = state.arcs
        
        cand = cls._valid_transitions(state)
        assert tsn in cand
        
        if tsn == SHIFT:
            tags[buf[-1]] = lbl
            stack.append(buf.pop())
            if len(buf) == 0:
                state.seen_the_end = True
        elif tsn == LEFT:
            arcs[stack[-2]] = (stack[-1],  lbl) 
            stack.pop(-2)
        elif tsn == RIGHT:
            arcs[stack[-1]] = (stack[-2], lbl)
            stack.pop()
        
        return state
    
    @classmethod
    def gold_action(cls, parser_state):
        """
        derive next gold action from reference, which in included in the parser_state.
        """
        SHIFT, LEFT, RIGHT = cls._actions_list
        
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
    
    @classmethod
    def dynamic_oracle(cls, parser_state):
        SHIFT, LEFT, RIGHT = cls._actions_list
        valid = cls._valid_transitions(parser_state)
        oracle = []
        
        # state
        stack = parser_state.stack
        buf = parser_state.buf
        # reference
        upos = parser_state.sent.upos
        heads = parser_state.sent.head
        children = parser_state.sent.children
        deprels = parser_state.sent.deprel
        
        if SHIFT in valid:
            buffer_top_head = heads[buf[-1]]
            stack_top_head = heads[stack[-1]]
            stack_top_children = children[stack[-1]]
            # 1. if s0 has collected all its right children and s0 has left head [then there is no chance to expose s0 on the top of the stack, so no chance to reduce it (or collect its uncollected left children)]
            # 2. if s0 has collected all its right children but not all its left children and s0 has a right head [then there is no chance to expose s0 on the top of the stack, and to collect its left children before reduce it to its head]
            # then shift is not an dynamic oracle
            if not (not any(x in buf for x in stack_top_children) and (stack_top_head < stack[-1] or (stack_top_head > stack[-1] and any(x in stack for x in stack_top_children)))):
                oracle.append(SHIFT)
            
        if RIGHT in valid:
            stack_top_head = heads[stack[-1]]
            stack_top_children = children[stack[-1]]
            if not ((stack_top_head != stack[-2]) or any(x in buf for x in stack_top_children)):
                oracle.append(RIGHT)
        
        if LEFT in valid:
            stack_2_head = heads[stack[-2]]
            stack_2_children = children[stack[-2]]
            if not ((stack_2_head != stack[-1]) or any(x in stack for x in stack_2_children)):
                oracle.append(LEFT)
        return oracle
        
    @classmethod
    def action_to_str(cls, action, control="normal"):
        SHIFT, LEFT, RIGHT = cls._actions_list
        
        if isinstance(action, tuple):
            tsn, lbl = action
        else:
            tsn, lbl = action, '_'
        
        if control == "normal":
            if tsn == SHIFT:
                return tsn
            else:
                return "{}-{}".format(tsn, lbl)
        elif control == "backbone":
            return tsn
    
    @classmethod
    def str_to_action(cls, string, control="normal"):
        SHIFT, LEFT, RIGHT = cls._actions_list
        if control == "normal":
            if string.startswith(SHIFT):
                tsn, lbl = string, "_"
            else:
                tsn, lbl = string.split("-", 1)
        elif control == "backbone":
            tsn, lbl = string, "_"
        return (tsn, lbl)
