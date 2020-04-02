'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 02/04/2020.
'''

import sys

def _repr(obj):
    """
    Get the representation of an object, with dedicated pprint-like format for lists.
    """
    if isinstance(obj, list):
        return '[' + (',\n '.join((_repr(e).replace('\n', '\n ') for e in obj))) + '\n]'
    else:
        return repr(obj) 

#### NODE CLASS - The All Father ####
# It's but a reference to other classes, allowing us to create default
# methods such as children() which can be recursively accessed by it's children.
class Node(object):
    __slots__ = ('coord')

    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-1]:
            result += separator
            result += indent
            result += name + '=' + (_repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result
            
    # NOTE: Imma use this function as a inheritance for leaf classes
    # If a class has children, it will be overriden, else it will use it 
    def children(self):
        """ A sequence of all children that are Nodes. """
        nodelist = []
        return tuple(nodelist)

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=True, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
            attrnames:
                True if you want to see the attribute names in name=value pairs. False to only see the values.
            nodenames:
                True if you want to see the actual node names within their parents.
            showcoord:
                Do you want the coordinates of each Node to be displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if self.coord:
                buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)
            
    # NOTE: it seems to be a list for variables contained in the class (excluding subtrees)
    attr_names = () 

class NodeVisitor(object):
    """ A base NodeVisitor class for visiting uc_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the constant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """

    _method_cache = None

    def visit(self, node):
        """ Visit a node.
        """

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c in node:
            self.visit(c)

# This is the top of the AST, representing a uC program (a
# translation unit in K&R jargon). It contains a list of
# global-declaration's, which is either declarations (Decl),
# or function definitions (FuncDef).
class Program(Node):
    __slots__ = ('gdecls', 'coord')
    
    def __init__(self, gdecls, coord=None):
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.gdecls or []):
            nodelist.append(("gdecls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()

#### AST NODES CLASSES ####

class ArrayDecl(Node):
    __slots__ = ('type', 'dims', 'coord')
    
    def __init__(self, type, dims, coord=None):
        self.type = type
        self.dims = dims
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        if self.dims is not None: nodelist.append(("dims", self.dims))
        return tuple(nodelist)
        
    attr_names = ()

class ArrayRef(Node):
    __slots__ = ('name', 'subsc', 'coord')
    
    def __init__(self, name, subsc, coord):
        self.name = name
        self.subsc = subsc
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(('name', self.name))
        if self.subsc is not None: nodelist.append(('subscript', self.subsc))
        return tuple(nodelist)
    
    attr_names = ()

class Assert(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to assert.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')

    def __init__(self, op, left, right, coord=None):
        self.op = op        # assign_op (TERMINAL EXPR - represents the node)
        self.lvalue = left  # un_expr
        self.rvalue = right # assign_expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op', ) 

class BinaryOp(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
    
    def __init__(self, op, left, right, coord=None):
        self.op = op        # TOKEN (represents the node)
        self.lvalue = left  # bin_expr
        self.rvalue = right # bin_expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op', ) # NOTE: lvalue and rvalue are subtrees, so they dont make the list

class Break(Node):
    __slots__ = ('coord')
    
    def __init__(self, coord=None):
        self.coord = coord
    
    def children(self):
        return ()
        
    attr_names = ()

class Cast(Node):
    __slots__ = ('type', 'expr', 'coord')
    
    def __init__(self, type, expr, coord=None):
        self.type = type
        self.expr = expr
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
        
    attr_names = ()

class Compound(Node):
    __slots__ = ('decls', 'stats', 'coord')
    
    def __init__(self, decls, stats, coord=None):
        self.decls = decls
        self.stats = stats
        self.coord = coord
        
    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            if child is not None: nodelist.append(("decls[%d]" % i, child))
        for i, child in enumerate(self.stats or []):
            if child is not None: nodelist.append(("stats[%d]" % i, child))
        return tuple(nodelist)
        
    attr_names = ()

class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord
    
    def children(self):
        return ()

    attr_names = ('type', 'value', )

class Coord(Node):
    """ Coordinates of a syntactic element. Consists of:
            - Line number
            - (optional) column number, for the Lexer
    """
    __slots__ = ('line', 'column')
    
    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            coord_str = "   @ %s:%s" % (self.line, self.column)
        else:
            coord_str = ""
        return coord_str
    
    attr_names = ()

class Decl(Node):
    __slots__ = ('name', 'type', 'init', 'coord')

    def __init__(self, name, type, init, coord=None):
        self.name = name # TODO: Not sure what's this name variable (I think it will derive from one of the childre or just remain as none)
        self.type = type # Func/Var Type [type_specifier] (int, float... tokens)
        self.init = init # One or more initializers [init_declarator_list_opt]
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        if self.init is not None: nodelist.append(("init", self.init))
        return tuple(nodelist)

    attr_names = ('name', )

class DeclList(Node):
    __slots__ = ('decls', 'coord')
    
    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(("decls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()

class EmptyStatement(Node):
    __slots__ = ('coord')
    
    def __init__(self, coord=None):
        self.coord = coord
        
    def children(self):
        return ()
        
    attr_names = ()

class ExprList(Node):
    __slots__ = ('exprs', 'coord')
    
    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord
        
    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)
        
    attr_names = ()

class For(Node):
    __slots__ = ('init', 'cond', 'next', 'body', 'coord')
    
    def __init__(self, init, cond, next, body, coord=None):
        self.init = init
        self.cond = cond
        self.next = next
        self.body = body
        self.coord = coord
    
    def children(self):
        nodelist = []
        if self.init is not None: nodelist.append(('init', self.init))
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.next is not None: nodelist.append(('next', self.next))
        if self.body is not None: nodelist.append(('body', self.body))
        return tuple(nodelist)
    
    attr_names = ()

class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord')
    
    def __init__ (self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(('name', self.name))
        if self.args is not None: nodelist.append(('args', self.args))
        return tuple(nodelist)
    
    attr_names = ()

class FuncDecl(Node):
    __slots__ = ('type', 'params', 'coord')
    
    def __init__(self, type, params, coord=None):
        self.type = type
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        if self.params is not None: nodelist.append(("params", self.params))
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)
    
    attr_names = ()

class FuncDef(Node):
    __slots__ = ('type', 'decl', 'params', 'body', 'coord')
    
    def __init__(self, type, decl, params, body, coord=None):
        self.type = type
        self.decl = decl
        self.params = params
        self.body = body
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.decl is not None: nodelist.append(('decl', self.decl))
        if self.params is not None: nodelist.append(('params', self.params))
        if self.body is not None: nodelist.append(('body', self.body))
        return tuple(nodelist)
        
    attr_names = ()

class GlobalDecl(Node):
    __slots__ = ('decls', 'coord')
    
    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord
        
    # NOTE: This might not be correct
    def children(self):
        nodelist = []
        for child in self.decls or []:
            if child is not None: nodelist.append(("Decl", child))
        return tuple(nodelist)
    
    attr_names = ()

class ID(Node): # NOTE: Const class is ID's sibiling, not child
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name   # Func/Var name [ID token value]
        self.coord = coord 
        
    def children(self):
        return ()

    attr_names = ('name', )

class If(Node):
    __slots__ = ('cond', 'if_stat', 'else_stat', 'coord')
    
    def __init__(self, cond, if_stat, else_stat, coord=None):
        self.cond = cond
        self.if_stat = if_stat 
        self.else_stat = else_stat
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.if_stat is not None: nodelist.append(('if_stat', self.if_stat))
        if self.else_stat is not None: nodelist.append(('else_stat', self.else_stat))
        return tuple(nodelist)
    
    attr_names = ()

class InitList(Node):
    __slots__ = ('exprs', 'coord')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)
    
    attr_names = ()

class ParamList(Node):
    __slots__ = ('params', 'coord')
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(("params[%d]" % i, child))
        return tuple(nodelist)
    
    attr_names = ()

class Print(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to print.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Read(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to read.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Return(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Type(Node):
    __slots__ = ('name', 'coord')
    
    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord
    
    def children(self):
        return ()
        
    attr_names = ('name',)

class VarDecl(Node):
    __slots__ = ('declname', 'type', 'coord') # NOTE: Not sure it there's

    def __init__(self, declname, type, coord=None):
        self.declname = declname   # Var name [ID token value]
        self.type = type
        self.coord = coord 

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        return tuple(nodelist)
    
    attr_names = ()

class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'coord')
    
    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord
    
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(("expr", self.expr))
        return tuple(nodelist)
    
    attr_names = ('op', )

class While(Node):
    __slots__ = ('cond', 'body', 'coord')
    
    def __init__(self, cond, body, coord=None):
        self.cond = cond   # Conditional expression
        self.body = body   # Statement
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.body is not None: nodelist.append(('body', self.body))
        return tuple(nodelist)
        
    attr_names = ()
