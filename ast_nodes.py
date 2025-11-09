# ast_nodes.py

class Node:
    """Base node class."""
    pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements

class Number(Node):
    def __init__(self, value):
        self.value = int(value)

class String(Node):
    def __init__(self, value):
        self.value = value

class VarAccess(Node):
    def __init__(self, name):
        self.name = name

class ArrayLiteral(Node):
    def __init__(self, elements):
        self.elements = elements

class VarAssign(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class ArrayAssign(Node):
    def __init__(self, name, index_expr, expr):
        self.name = name
        self.index_expr = index_expr
        self.expr = expr

class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class IfNode(Node):
    def __init__(self, cond, then_block, else_block=None):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

class WhileNode(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class ForRangeNode(Node):
    def __init__(self, varname, start_expr, end_expr, body):
        self.varname = varname
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.body = body

class ForInNode(Node):
    def __init__(self, varname, iterable_expr, body):
        self.varname = varname
        self.iterable_expr = iterable_expr
        self.body = body

class FuncDef(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class ReturnNode(Node):
    def __init__(self, expr):
        self.expr = expr

class FuncCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr
