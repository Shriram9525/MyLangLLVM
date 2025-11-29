#!/usr/bin/env python3
from lexer import Lexer
from parser import Parser
from codegen import CodeGenerator


def run_xlang(source_code: str):
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        codegen = CodeGenerator()
        codegen.generate(ast)
        codegen.verify()
        
        return codegen.compile_and_run()
    except Exception as e:
        print(f"Error: {e}")
        return 1


def interactive_mode():
    print("=" * 50)
    print("XLANG INTERACTIVE IDE")
    print("=" * 50)
    print("Commands:")
    print("  run    - Execute the code you entered")
    print("  clear  - Clear current code buffer")
    print("  show   - Show current code buffer")
    print("  help   - Show Xlang syntax help")
    print("  exit   - Exit the IDE")
    print("=" * 50)
    print()
    
    code_buffer = []
    
    while True:
        try:
            line = input("xlang> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
            continue
        
        cmd = line.strip().lower()
        
        if cmd == "exit" or cmd == "quit":
            print("Goodbye!")
            break
        
        elif cmd == "run":
            if code_buffer:
                print("\n" + "-" * 40)
                print("OUTPUT:")
                print("-" * 40)
                source = "\n".join(code_buffer)
                run_xlang(source)
                print("-" * 40 + "\n")
            else:
                print("No code to run. Enter some Xlang code first.")
        
        elif cmd == "clear":
            code_buffer = []
            print("Code buffer cleared.")
        
        elif cmd == "show":
            if code_buffer:
                print("\n--- Current Code ---")
                for i, line in enumerate(code_buffer, 1):
                    print(f"{i:3}: {line}")
                print("--- End ---\n")
            else:
                print("Code buffer is empty.")
        
        elif cmd == "help":
            print("""
Xlang Syntax:
-------------
Variables:    make x = 10
Output:       show x  OR  show "text"
Arithmetic:   +  -  *  /
Comparison:   <  ==
Comments:     // this is a comment

Loop:
  loop x < 5:
      show x
      make x = x + 1
  stop

Conditional:
  if x == 10:
      show "yes"
  else:
      show "no"
  stop
""")
        
        elif line.strip():
            code_buffer.append(line)


def file_mode(filename: str):
    try:
        with open(filename, 'r') as f:
            source = f.read()
        
        print(f"Running: {filename}")
        print("-" * 40)
        run_xlang(source)
        print("-" * 40)
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_mode(sys.argv[1])
    else:
        interactive_mode()
