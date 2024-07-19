'''  This package provides a way to turn an iterable of strings
into a tree. Folowing the SpecTcl/Rustogramer naming convention,
the period ('.') represents a level separator.  Therefore e.g.
a.b.c  is reprented as :

  a
    -> b
        -> c

in the tree.  A tree consists of two types of nodes. 
   - Parent nodes have children 
   - Terminal nodes have on children.

In the figure above, for example, a and b are parent nodes and
c is a terminal node.  The root tree node is a dict as are all nodes.
The parent nodes have values that are, themselves dicts with children
the keys.  Terminal nodes have an empty dict as their value.  Thus,
The tree shown in the figure is represented by:

{'a': {'b' : {'c':{}}}}

if one were to add e.g. a.1 and a.b.d to the tree, the result would be:

{'a': 
   {'1': {}, 'b': 
       {'c': {}, 'd': {}}}}

Note that while name pairs like a.b, a.b.c are not supported.  The result, would
be as if there were only the name a.b.c
'''


def make_tree(names):
    result = {}
    for name in names:
        path = name.split('.')
        level = result
        for element in path:
            if element not in level:
                level[element] = {}
            if not isinstance(level[element], str):
                level = level[element]
            
    return result

