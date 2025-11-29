#!/usr/bin/env python3
from lexer import Lexer
from parser import Parser
from codegen import CodeGenerator

CODE = '''
show "Hello World!"

make x = 42
show x

make a = 10 + 5
show a

make b = 20 - 8
show b

make c = 6 * 7
show c

make d = 100 / 4
show d

make i = 0
loop i < 5:
    show i
    make i = i + 1
stop

make num = 10
if num == 10:
    show "Yes"
else:
    show "No"
stop

show "Done!"
'''

print("Xlang Code:")
print("-" * 30)
print(CODE)
print("-" * 30)
print("Output:")
print("-" * 30)

lexer = Lexer(CODE)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()
codegen = CodeGenerator()
codegen.generate(ast)
codegen.verify()
codegen.compile_and_run()
