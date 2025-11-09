# parser.py
from lexer import tokenize
import ast_nodes as ast

# This parser exposes parse(tokens) -> ast.Program (or list)
# It's a simple recursive-descent parser for the mini grammar.

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None)

    def eat(self, expected_type=None):
        tok = self.peek()
        if expected_type and tok[0] != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {tok}")
        self.i += 1
        return tok

    def parse(self):
        stmts = []
        while self.i < len(self.tokens):
            stmts.append(self.parse_statement())
        return ast.Program(stmts)

    def parse_statement(self):
        t = self.peek()
        if t[0] == 'FUNC':
            return self.parse_func()
        if t[0] == 'IF':
            return self.parse_if()
        if t[0] == 'WHILE':
            return self.parse_while()
        if t[0] == 'FOR':
            return self.parse_for()
        if t[0] == 'RETURN':
            self.eat('RETURN')
            expr = self.parse_expr()
            return ast.ReturnNode(expr)
        if t[0] == 'IDENT':
            # lookahead for assignment or array assign or function call
            if self.tokens[self.i+1][0] == 'ASSIGN':
                name = self.eat('IDENT')[1]
                self.eat('ASSIGN')
                expr = self.parse_expr()
                return ast.VarAssign(name, expr)
            if self.tokens[self.i+1][0] == 'LBRACKET':
                name = self.eat('IDENT')[1]
                self.eat('LBRACKET')
                idx = self.parse_expr()
                self.eat('RBRACKET')
                self.eat('ASSIGN')
                expr = self.parse_expr()
                return ast.ArrayAssign(name, idx, expr)
        # otherwise expression statement
        expr = self.parse_expr()
        return ast.ExprStmt(expr)

    def parse_block(self):
        if self.peek()[0] == 'LBRACE':
            self.eat('LBRACE')
            stmts = []
            while self.peek()[0] != 'RBRACE':
                stmts.append(self.parse_statement())
            self.eat('RBRACE')
            return stmts
        else:
            return [self.parse_statement()]

    def parse_func(self):
        self.eat('FUNC')
        name = self.eat('IDENT')[1]
        self.eat('LPAREN')
        params = []
        if self.peek()[0] != 'RPAREN':
            params.append(self.eat('IDENT')[1])
            while self.peek()[0] == 'COMMA':
                self.eat('COMMA')
                params.append(self.eat('IDENT')[1])
        self.eat('RPAREN')
        body = self.parse_block()
        return ast.FuncDef(name, params, body)

    def parse_if(self):
        self.eat('IF')
        cond = self.parse_expr()
        then_block = self.parse_block()
        else_block = None
        if self.peek()[0] == 'ELSE':
            self.eat('ELSE')
            else_block = self.parse_block()
        return ast.IfNode(cond, then_block, else_block)

    def parse_while(self):
        self.eat('WHILE')
        cond = self.parse_expr()
        body = self.parse_block()
        return ast.WhileNode(cond, body)

    def parse_for(self):
        self.eat('FOR')
        varname = self.eat('IDENT')[1]
        self.eat('IN')
        left = self.parse_expr()
        if self.peek()[0] == 'TO':
            self.eat('TO')
            right = self.parse_expr()
            body = self.parse_block()
            return ast.ForRangeNode(varname, left, right, body)
        else:
            body = self.parse_block()
            return ast.ForInNode(varname, left, body)

    # expression parsing (precedence)
    def parse_expr(self):
        return self.parse_cmp()

    def parse_cmp(self):
        node = self.parse_term()
        while self.peek()[0] in ('EQ','NE','GT','LT','GE','LE'):
            op = self.eat()[0]
            right = self.parse_term()
            node = ast.BinOp(node, op, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek()[0] in ('PLUS','MINUS'):
            op = self.eat()[0]
            right = self.parse_factor()
            node = ast.BinOp(node, op, right)
        return node

    def parse_factor(self):
        node = self.parse_atom()
        while self.peek()[0] in ('MUL','DIV','MOD'):
            op = self.eat()[0]
            right = self.parse_atom()
            node = ast.BinOp(node, op, right)
        return node

    def parse_atom(self):
        t = self.peek()
        if t[0] == 'NUMBER':
            self.eat('NUMBER')
            return ast.Number(t[1])
        if t[0] == 'STRING':
            self.eat('STRING')
            return ast.String(t[1])
        if t[0] == 'IDENT':
            name = self.eat('IDENT')[1]
            if self.peek()[0] == 'LPAREN':
                self.eat('LPAREN')
                args = []
                if self.peek()[0] != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.peek()[0] == 'COMMA':
                        self.eat('COMMA')
                        args.append(self.parse_expr())
                self.eat('RPAREN')
                return ast.FuncCall(name, args)
            if self.peek()[0] == 'LBRACKET':
                self.eat('LBRACKET')
                idx = self.parse_expr()
                self.eat('RBRACKET')
                # represent as runtime get: func __get_elem__(name, idx)
                return ast.FuncCall('__get_elem__', [ast.VarAccess(name), idx])
            return ast.VarAccess(name)
        if t[0] == 'LBRACKET':
            self.eat('LBRACKET')
            elems = []
            if self.peek()[0] != 'RBRACKET':
                elems.append(self.parse_expr())
                while self.peek()[0] == 'COMMA':
                    self.eat('COMMA')
                    elems.append(self.parse_expr())
            self.eat('RBRACKET')
            return ast.ArrayLiteral(elems)
        if t[0] == 'LPAREN':
            self.eat('LPAREN')
            node = self.parse_expr()
            self.eat('RPAREN')
            return node
        raise SyntaxError(f"Unexpected token {t}")

# top-level parse function (used by main.py)
def parse(tokens):
    p = Parser(tokens)
    return p.parse()
