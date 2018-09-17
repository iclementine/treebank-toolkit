"""
Parser state of transition-based parsers.
Note
"""

from copy import copy

class State(object):
    def __init__(self, sent, transys=None, stack=None, buf=None, tags=None, arcs=None):
        self.sent = sent
        self.transys= transys
        self.stack = copy(stack)
        self.buf = copy(buf)
        self.tags = tags
        self.arcs = copy(arcs)
        
    @classmethod
    def init_from_sent(cls, sent, transys=None):
        stack = [0]
        buf = list(reversed(range(1, len(sent) + 1))) # mind that len doesn't include <root>
        tags = {}
        arcs = {}
        return cls(sent, transys, stack, buf, tags, arcs)
   
    @classmethod
    def copy(cls, state):
        res = cls(state.sent, state.transys, state.stack, state.buf, state.tags, state.arcs)
        return res
    
    def __repr__(self):
        return "State({},\ntransys={},\nstack={},\nbuf={},\ntags={},\narcs={})".format(
            repr(self.sent),
            repr(self.transys),
            repr(self.stack),
            repr(self.buf),
            repr(self.tags),
            repr(self.arcs))
    
    def __str__(self):
        return "State\nsent_form: {}\nstack: {}\nbuffer: {}\ntags: {}\narcs: {}".format(
            str(self.sent.form),
            str([self.sent.form[idx] for idx in self.stack]),
            str([self.sent.form[idx] for idx in self.buf]),
            str(self.tags),
            str(self.arcs))
