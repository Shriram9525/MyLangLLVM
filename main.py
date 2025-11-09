import sys
from lexer import tokenize
from parser import parse
from codegen import CodeGen

def compile_and_run(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        src = f.read()
    tokens = tokenize(src)
    ast_root = parse(tokens)

    cg = CodeGen()
    llvm_ir = cg.generate(ast_root)
    print("===== ✅ GENERATED LLVM IR =====")
    print(llvm_ir)

    print("\n===== 🎯 PROGRAM OUTPUT =====")
    cg.execute(llvm_ir)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py samples/test.mylang")
        sys.exit(1)
    compile_and_run(sys.argv[1])
