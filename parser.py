from tokens import Token, TokenType


class ASTNode:
    pass


class NumberNode(ASTNode):
    def __init__(self, value: int):
        self.value = value
    
    def __repr__(self):
        return f"Number({self.value})"


class StringNode(ASTNode):
    def __init__(self, value: str):
        self.value = value
    
    def __repr__(self):
        return f"String({self.value!r})"


class IdentifierNode(ASTNode):
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"Identifier({self.name})"


class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right
    
    def __repr__(self):
        return f"BinaryOp({self.left}, {self.op}, {self.right})"


class MakeNode(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f"Make({self.name}, {self.value})"


class ShowNode(ASTNode):
    def __init__(self, value: ASTNode):
        self.value = value
    
    def __repr__(self):
        return f"Show({self.value})"


class LoopNode(ASTNode):
    def __init__(self, condition: ASTNode, body: list):
        self.condition = condition
        self.body = body
    
    def __repr__(self):
        return f"Loop({self.condition}, {self.body})"


class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_body: list, else_body: list = None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body or []
    
    def __repr__(self):
        return f"If({self.condition}, then={self.then_body}, else={self.else_body})"


class ProgramNode(ASTNode):
    def __init__(self, statements: list):
        self.statements = statements
    
    def __repr__(self):
        return f"Program({self.statements})"


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]
    
    def peek_token(self) -> Token:
        if self.pos + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos + 1]
    
    def advance(self) -> Token:
        token = self.current_token()
        self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type} at line {token.line}")
        return self.advance()
    
    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> ProgramNode:
        statements = []
        self.skip_newlines()
        
        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return ProgramNode(statements)
    
    def parse_statement(self):
        token = self.current_token()
        
        if token.type == TokenType.MAKE:
            return self.parse_make()
        elif token.type == TokenType.SHOW:
            return self.parse_show()
        elif token.type == TokenType.LOOP:
            return self.parse_loop()
        elif token.type == TokenType.IF:
            return self.parse_if()
        elif token.type == TokenType.NEWLINE:
            self.advance()
            return None
        else:
            raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")
    
    def parse_make(self) -> MakeNode:
        self.expect(TokenType.MAKE)
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.EQUAL)
        value = self.parse_expression()
        return MakeNode(name_token.value, value)
    
    def parse_show(self) -> ShowNode:
        self.expect(TokenType.SHOW)
        value = self.parse_expression()
        return ShowNode(value)
    
    def parse_loop(self) -> LoopNode:
        self.expect(TokenType.LOOP)
        condition = self.parse_comparison()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        
        body = self.parse_block()
        return LoopNode(condition, body)
    
    def parse_if(self) -> IfNode:
        self.expect(TokenType.IF)
        condition = self.parse_comparison()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        
        then_body = self.parse_block()
        else_body = []
        
        self.skip_newlines()
        
        if self.current_token().type == TokenType.ELSE:
            self.advance()
            self.expect(TokenType.COLON)
            self.skip_newlines()
            
            if self.current_token().type == TokenType.INDENT:
                self.advance()
            
            else_body = self.parse_block()
        
        return IfNode(condition, then_body, else_body)
    
    def parse_block(self) -> list:
        statements = []
        
        while True:
            self.skip_newlines()
            token = self.current_token()
            
            if token.type == TokenType.STOP:
                self.advance()
                break
            elif token.type == TokenType.DEDENT:
                self.advance()
                continue
            elif token.type == TokenType.ELSE:
                break
            elif token.type == TokenType.EOF:
                break
            else:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
        
        return statements
    
    def parse_expression(self) -> ASTNode:
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        
        while self.current_token().type in (TokenType.LESS, TokenType.EQUAL_EQUAL):
            op_token = self.advance()
            right = self.parse_additive()
            left = BinaryOpNode(left, op_token.value, right)
        
        return left
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOpNode(left, op_token.value, right)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_primary()
        
        while self.current_token().type in (TokenType.STAR, TokenType.SLASH):
            op_token = self.advance()
            right = self.parse_primary()
            left = BinaryOpNode(left, op_token.value, right)
        
        return left
    
    def parse_primary(self) -> ASTNode:
        token = self.current_token()
        
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)
        elif token.type == TokenType.STRING:
            self.advance()
            return StringNode(token.value)
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return IdentifierNode(token.name if hasattr(token, 'name') else token.value)
        else:
            raise SyntaxError(f"Unexpected token {token.type} in expression at line {token.line}")
