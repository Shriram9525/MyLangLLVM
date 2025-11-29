from enum import Enum, auto

class TokenType(Enum):
    MAKE = auto()
    SHOW = auto()
    LOOP = auto()
    IF = auto()
    ELSE = auto()
    STOP = auto()
    
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    
    LESS = auto()
    EQUAL_EQUAL = auto()
    EQUAL = auto()
    
    COLON = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    
    EOF = auto()


class Token:
    def __init__(self, type: TokenType, value, line: int):
        self.type = type
        self.value = value
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


KEYWORDS = {
    "make": TokenType.MAKE,
    "show": TokenType.SHOW,
    "loop": TokenType.LOOP,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "stop": TokenType.STOP,
}
