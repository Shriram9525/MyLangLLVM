from tokens import Token, TokenType, KEYWORDS


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.indent_stack = [0]
        self.tokens = []
        self.at_line_start = True
    
    def current_char(self):
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self):
        if self.pos + 1 >= len(self.source):
            return None
        return self.source[self.pos + 1]
    
    def advance(self):
        char = self.current_char()
        self.pos += 1
        if char == '\n':
            self.line += 1
        return char
    
    def skip_comment(self):
        while self.current_char() is not None and self.current_char() != '\n':
            self.advance()
    
    def read_string(self):
        quote = self.advance()
        result = ""
        while self.current_char() is not None and self.current_char() != quote:
            if self.current_char() == '\\' and self.peek_char() == quote:
                self.advance()
                result += self.advance()
            else:
                result += self.advance()
        if self.current_char() == quote:
            self.advance()
        return result
    
    def read_number(self):
        result = ""
        while self.current_char() is not None and self.current_char().isdigit():
            result += self.advance()
        return int(result)
    
    def read_identifier(self):
        result = ""
        while self.current_char() is not None and (self.current_char().isalnum() or self.current_char() == '_'):
            result += self.advance()
        return result
    
    def count_indent(self):
        count = 0
        while self.current_char() == ' ':
            self.advance()
            count += 1
        while self.current_char() == '\t':
            self.advance()
            count += 4
        return count
    
    def handle_indentation(self, indent):
        current_indent = self.indent_stack[-1]
        
        if indent > current_indent:
            self.indent_stack.append(indent)
            self.tokens.append(Token(TokenType.INDENT, indent, self.line))
        elif indent < current_indent:
            while self.indent_stack and self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, indent, self.line))
    
    def tokenize(self):
        while self.current_char() is not None:
            if self.at_line_start:
                if self.current_char() == '\n':
                    self.advance()
                    continue
                if self.current_char() == '/' and self.peek_char() == '/':
                    self.skip_comment()
                    continue
                    
                indent = self.count_indent()
                
                if self.current_char() == '\n':
                    self.advance()
                    continue
                if self.current_char() == '/' and self.peek_char() == '/':
                    self.skip_comment()
                    continue
                if self.current_char() is None:
                    break
                    
                self.handle_indentation(indent)
                self.at_line_start = False
            
            char = self.current_char()
            
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', self.line))
                self.advance()
                self.at_line_start = True
                continue
            
            if char in ' \t':
                self.advance()
                continue
            
            if char == '/' and self.peek_char() == '/':
                self.skip_comment()
                continue
            
            if char == '"' or char == "'":
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, self.line))
                continue
            
            if char.isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, self.line))
                continue
            
            if char.isalpha() or char == '_':
                value = self.read_identifier()
                token_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, value, self.line))
                continue
            
            if char == '+':
                self.tokens.append(Token(TokenType.PLUS, '+', self.line))
                self.advance()
                continue
            
            if char == '-':
                self.tokens.append(Token(TokenType.MINUS, '-', self.line))
                self.advance()
                continue
            
            if char == '*':
                self.tokens.append(Token(TokenType.STAR, '*', self.line))
                self.advance()
                continue
            
            if char == '/':
                self.tokens.append(Token(TokenType.SLASH, '/', self.line))
                self.advance()
                continue
            
            if char == '<':
                self.tokens.append(Token(TokenType.LESS, '<', self.line))
                self.advance()
                continue
            
            if char == '=' and self.peek_char() == '=':
                self.tokens.append(Token(TokenType.EQUAL_EQUAL, '==', self.line))
                self.advance()
                self.advance()
                continue
            
            if char == '=':
                self.tokens.append(Token(TokenType.EQUAL, '=', self.line))
                self.advance()
                continue
            
            if char == ':':
                self.tokens.append(Token(TokenType.COLON, ':', self.line))
                self.advance()
                continue
            
            raise SyntaxError(f"Unexpected character '{char}' at line {self.line}")
        
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, self.line))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line))
        return self.tokens
