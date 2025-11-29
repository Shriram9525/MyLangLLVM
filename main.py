#!/usr/bin/env python3
"""
Xlang Compiler - A Custom Programming Language with LLVM Backend

Compilation Pipeline:
=====================
1. SOURCE CODE (Xlang)
   |
   v
2. LEXER (lexer.py)
   - Reads source code character by character
   - Produces stream of tokens (keywords, operators, literals)
   - Handles indentation for block detection
   |
   v
3. PARSER (parser.py)
   - Consumes token stream
   - Builds Abstract Syntax Tree (AST)
   - Validates syntax rules
   |
   v
4. CODE GENERATOR (codegen.py)
   - Traverses AST
   - Generates LLVM Intermediate Representation (IR)
   - Allocates variables in entry block (SSA form)
   |
   v
5. LLVM JIT COMPILER
   - Verifies IR correctness
   - Optimizes code
   - Compiles to native machine code
   |
   v
6. CPU EXECUTION
   - Runs compiled machine code directly
   - Returns exit code

Xlang Syntax Summary:
====================
- Variables: make x = 10
- Output: show x, show "text"
- Arithmetic: + - * /
- Comparison: < ==
- Loop: loop x < 5: ... stop
- Conditional: if x == 5: ... else: ... stop
- Comments: // comment
- Blocks end with 'stop' keyword
"""

from lexer import Lexer
from parser import Parser
from codegen import CodeGenerator


def compile_and_run(source_code: str):
    print("=" * 50)
    print("XLANG COMPILER")
    print("=" * 50)
    
    print("\n[1] Lexical Analysis...")
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print(f"    Generated {len(tokens)} tokens")
    
    print("\n[2] Parsing...")
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"    Generated AST with {len(ast.statements)} top-level statements")
    
    print("\n[3] Code Generation...")
    codegen = CodeGenerator()
    module = codegen.generate(ast)
    print("    Generated LLVM IR")
    
    print("\n[4] Verification...")
    codegen.verify()
    print("    Module verified successfully!")
    
    print("\n[5] JIT Compilation & Execution...")
    print("-" * 50)
    print("OUTPUT:")
    print("-" * 50)
    
    exit_code = codegen.compile_and_run()
    
    print("-" * 50)
    print(f"\nProgram exited with code: {exit_code}")
    print("=" * 50)
    
    return exit_code


TEST_PROGRAM = '''
// Xlang Test Program
// This demonstrates loops, conditionals, and variables

make x = 0

loop x < 5:
    show x
    make x = x + 1
stop

if x == 5:
    show "Completed"
else:
    show "Error"
stop
'''


if __name__ == "__main__":
    print("\nXlang Source Code:")
    print("-" * 50)
    print(TEST_PROGRAM)
    print("-" * 50)
    print()
    
    compile_and_run(TEST_PROGRAM)
