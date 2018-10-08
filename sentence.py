from collections import defaultdict
class ConllSent(object):
    """
    an alternative format for representing conll-u sentences
    where each type of annotations is separately stored in its own list
    instead of a list of ConllTokens.
    """
    def __init__(self, form, upos, xpos, head, deprel):
        # prepend virtual <root>
        self.form = ['<root>'] + form
        self.upos = ['ROOT'] + upos
        self.xpos = ['ROOT'] + xpos
        self.head = [-1] + head
        self.deprel = ['ROOT'] + deprel
        self.children = self._derive_children()
        self.transitions = None
    
    @classmethod
    def from_conllu(cls, sent):
        '''
        used to convert a list(OrderedDict) from conllu.parse() to this form
        '''
        form = [x['form'] for x in sent]
        upos = [x['upostag'] for x in sent]
        xpos = [x['xpostag'] for x in sent]
        head = [x['head'] for x in sent]
        deprel = [x['deprel'] for x in sent]
        return cls(form, upos, xpos, head, deprel)
    
    def _derive_children(self):
        "derive every node's children, once for all"
        deps = defaultdict(list)
        for idx, h in enumerate(self.head[1:], 1): # exclude virtual <root>
            deps[h].append(idx)
        return deps
    
    def __len__(self):
        return len(self.form) - 1

    def __repr__(self):
        return "ConllSent({},\n{},\n{},\n{})".format(
            repr(self.form), 
            repr(self.upos), 
            repr(self.xpos), 
            repr(self.head), 
            repr(self.deprel))
    
    def __str__(self):
        return "Sentence with {} tokens and <root>.\nform: {}\nupos: {}\nxpos: {}\nhead: {}\ndeprel: {}".format(
            len(self),
            str(self.form), 
            str(self.upos), 
            str(self.xpos), 
            str(self.head), 
            str(self.deprel))
