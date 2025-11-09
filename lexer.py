import re

TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('STRING',   r'"([^"\\]|\\.)*"'),
    ('FUNC',     r'\bfunc\b'),
    ('RETURN',   r'\breturn\b'),
    ('IF',       r'\bif\b'),
    ('ELSE',     r'\belse\b'),
    ('WHILE',    r'\bwhile\b'),
    ('FOR',      r'\bfor\b'),
    ('IN',       r'\bin\b'),
    ('TO',       r'\bto\b'),
    ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MUL',      r'\*'),
    ('DIV',      r'/'),
    ('MOD',      r'%'),
    ('EQ',       r'=='),
    ('NE',       r'!='),
    ('GE',       r'>='),
    ('LE',       r'<='),
    ('GT',       r'>'),
    ('LT',       r'<'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('COMMA',    r','),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
    ('MISMATCH', r'.'),
]

master = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC))

def tokenize(code):
    tokens = []
    for m in master.finditer(code):
        kind = m.lastgroup
        value = m.group()
        if kind == 'NUMBER':
            tokens.append(('NUMBER', int(value)))
        elif kind == 'STRING':
            # Unescape any \" and \n in strings, remove quotes
            s = value[1:-1]
            s = s.replace('\\"', '"').replace('\\n', '\n')
            tokens.append(('STRING', s))
        elif kind == 'IDENT':
            tokens.append(('IDENT', value))
        elif kind in ('SKIP', 'NEWLINE'):
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected char: {value}")
        else:
            tokens.append((kind, value))
    return tokens
