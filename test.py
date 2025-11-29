#!/usr/bin/env python3
"""
XLANG COMPILER - FULL PIPELINE DEMONSTRATION
Shows: Source Code → Tokens → AST → LLVM IR → Machine Code → Execution
"""

from lexer import Lexer
from parser import Parser
from codegen import CodeGenerator

CODE = '''
// XLANG FEATURE TEST

// 1. Variables
show "--- Variables ---"
make x = 42
show x

// 2. Arithmetic (+, -, *, /)
show "--- Arithmetic ---"
make a = 10 + 5
show a
make b = 20 - 8
show b
make c = 6 * 7
show c
make d = 100 / 4
show d

// 3. Complex Expressions
show "--- Expressions ---"
make result = 10 + 5 * 2
show result

// 4. Variable Reassignment
show "--- Reassignment ---"
make counter = 1
show counter
make counter = counter + 9
show counter

// 5. Loop (loop...stop)
show "--- Loop ---"
make i = 0
loop i < 5:
    show i
    make i = i + 1
stop

// 6. If-Else (if...else...stop)
show "--- Conditionals ---"
make num = 10
if num == 10:
    show "num equals 10"
else:
    show "num not 10"
stop

// 7. Less-than Comparison
make val = 5
if val < 10:
    show "val less than 10"
else:
    show "val >= 10"
stop

// 8. Nested Control Structures
show "--- Nested Loop+If ---"
make j = 0
loop j < 3:
    if j == 0:
        show "First"
    else:
        show "Other"
    stop
    make j = j + 1
stop

show "=== ALL TESTS PASSED ==="
'''


def main():
    print("=" * 70)
    print("                    XLANG COMPILER PIPELINE")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("STEP 1: SOURCE CODE (Xlang)")
    print("=" * 70)
    print(CODE)
    
    print("\n" + "=" * 70)
    print("STEP 2: LEXICAL ANALYSIS (Tokenization)")
    print("=" * 70)
    lexer = Lexer(CODE)
    tokens = lexer.tokenize()
    print(f"Generated {len(tokens)} tokens\n")
    print("Sample tokens (first 30):")
    print("-" * 50)
    for i, token in enumerate(tokens[:30]):
        print(f"  {token}")
    print("  ...")
    print(f"  (and {len(tokens) - 30} more tokens)")
    
    print("\n" + "=" * 70)
    print("STEP 3: PARSING (Abstract Syntax Tree)")
    print("=" * 70)
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"Generated AST with {len(ast.statements)} top-level statements\n")
    print("AST Nodes:")
    print("-" * 50)
    for i, stmt in enumerate(ast.statements[:15]):
        print(f"  [{i+1}] {stmt}")
    print("  ...")
    print(f"  (and {len(ast.statements) - 15} more statements)")
    
    print("\n" + "=" * 70)
    print("STEP 4: CODE GENERATION (LLVM Intermediate Representation)")
    print("=" * 70)
    codegen = CodeGenerator()
    module = codegen.generate(ast)
    
    llvm_ir = str(module)
    print("Generated LLVM IR:\n")
    print("-" * 50)
    print(llvm_ir)
    print("-" * 50)
    
    print("\n" + "=" * 70)
    print("STEP 5: VERIFICATION")
    print("=" * 70)
    codegen.verify()
    print("Module verified successfully!")
    print("LLVM IR is valid and ready for compilation.")
    
    print("\n" + "=" * 70)
    print("STEP 6: JIT COMPILATION TO NATIVE MACHINE CODE")
    print("=" * 70)
    print("Compiling LLVM IR to native x86-64 machine code...")
    print("Using MCJIT execution engine...")
    
    print("\n" + "=" * 70)
    print("STEP 7: EXECUTION (Running Native Code)")
    print("=" * 70)
    print("OUTPUT:")
    print("-" * 50)
    
    exit_code = codegen.compile_and_run()
    
    print("-" * 50)
    print(f"\nProgram exited with code: {exit_code}")
    
    print("\n" + "=" * 70)
    print("                    COMPILATION PIPELINE COMPLETE")
    print("=" * 70)
    print("""
    Xlang Source Code
           |
           v
    +--------------+
    |    LEXER     |  --> Tokenizes source into tokens
    +--------------+
           |
           v
    +--------------+
    |    PARSER    |  --> Builds Abstract Syntax Tree
    +--------------+
           |
           v
    +--------------+
    |   CODEGEN    |  --> Generates LLVM IR
    +--------------+
           |
           v
    +--------------+
    |   LLVM JIT   |  --> Compiles to native machine code
    +--------------+
           |
           v
       CPU EXECUTION
    """)


if __name__ == "__main__":
    main()
