from llvmlite import ir, binding
import ctypes
import runtime
import ast_nodes as nodes

I64 = ir.IntType(64)

class CodeGen:
    def __init__(self):
        self.module = ir.Module(name="mylang_module")
        # Set native triple if available
        try:
            self.module.triple = binding.get_default_triple()
        except Exception:
            pass

        self.builder = None
        self.current_fn = None
        self.locals = {}           # name -> alloca
        self.func_prototypes = {}  # name -> ir.Function

        self._declare_runtime()

    def _declare_runtime(self):
        fn0 = ir.FunctionType(I64, [])
        fn1 = ir.FunctionType(I64, [I64])
        fn2 = ir.FunctionType(I64, [I64, I64])

        self.rt_new_array = ir.Function(self.module, fn0, name="rt_new_array")
        self.rt_new_string = ir.Function(self.module, fn1, name="rt_new_string")
        self.rt_push = ir.Function(self.module, fn2, name="rt_push")
        self.rt_pop = ir.Function(self.module, fn1, name="rt_pop")
        self.rt_length = ir.Function(self.module, fn1, name="rt_length")
        self.rt_clear = ir.Function(self.module, fn1, name="rt_clear")
        self.rt_contains = ir.Function(self.module, fn2, name="rt_contains")
        self.rt_sort = ir.Function(self.module, fn1, name="rt_sort")
        self.rt_sum = ir.Function(self.module, fn1, name="rt_sum")
        self.rt_get = ir.Function(self.module, fn2, name="rt_get")
        # Only include rt_set if implemented in runtime
        self.rt_set = ir.Function(self.module, ir.FunctionType(I64, [I64, I64, I64]), name="rt_set")
        # String helpers (must exist in runtime, otherwise remove/comment out)
        # self.rt_to_string = ir.Function(self.module, fn1, name="rt_to_string")
        # self.rt_concat = ir.Function(self.module, fn2, name="rt_concat")

        self.rt_isPrime = ir.Function(self.module, fn1, name="rt_isPrime")
        self.rt_print_int = ir.Function(self.module, fn1, name="rt_print_int")
        self.rt_print_str = ir.Function(self.module, fn1, name="rt_print_str")
        self.rt_input = ir.Function(self.module, fn1, name="rt_input")

    def generate(self, ast_root):
        """
        Build LLVM IR module from AST root and return IR as string.
        ast_root: Program node or list of statements
        """
        main_ty = ir.FunctionType(I64, [])
        main_fn = ir.Function(self.module, main_ty, name="main")
        bb = main_fn.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb)
        self.current_fn = main_fn
        self.locals = {}
        self.func_prototypes = {}

        stmts = ast_root.statements if hasattr(ast_root, "statements") else ast_root
        for s in stmts:
            self._emit_statement(s)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(I64, 0))

        return str(self.module)

    def execute(self, llvm_ir):
        """
        JIT compile the llvm_ir and run the 'main' function.
        Maps runtime.EXPORTED Python functions to JIT so IR can call them.
        """
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)

        mod = binding.parse_assembly(llvm_ir)
        mod.verify()
        engine.add_module(mod)

        for f in mod.functions:
            name = f.name
            if name in runtime.EXPORTED:
                cfunc = runtime.EXPORTED[name]
                addr = ctypes.cast(cfunc, ctypes.c_void_p).value
                engine.add_global_mapping(f, addr)

        engine.finalize_object()
        engine.run_static_constructors()

        main_addr = engine.get_function_address("main")
        if main_addr == 0:
            raise RuntimeError("main not found in JIT")

        main_func = ctypes.CFUNCTYPE(ctypes.c_longlong)(main_addr)
        return main_func()

    def _node_has_string_literal(self, node):
        """Recursively check if an AST node contains a string literal anywhere."""
        if isinstance(node, nodes.String):
            return True
        if isinstance(node, nodes.BinOp):
            return self._node_has_string_literal(node.left) or self._node_has_string_literal(node.right)
        if isinstance(node, nodes.UnaryOp):
            return self._node_has_string_literal(node.operand)
        if isinstance(node, nodes.FuncCall):
            return any(self._node_has_string_literal(a) for a in node.args)
        if isinstance(node, nodes.ArrayLiteral):
            return any(self._node_has_string_literal(e) for e in node.elements)
        return False

    def _emit_statement(self, node):
        if isinstance(node, nodes.VarAssign):
            val = self._emit_expr(node.expr)
            ptr = self.builder.alloca(I64, name=node.name)
            self.builder.store(val, ptr)
            self.locals[node.name] = ptr
            return

        if isinstance(node, nodes.ArrayAssign):
            arr_handle = self._emit_expr(nodes.VarAccess(node.name))
            idxv = self._emit_expr(node.index_expr)
            val = self._emit_expr(node.expr)
            length = self.builder.call(self.rt_length, [arr_handle])
            eq = self.builder.icmp_signed('==', idxv, length)
            with self.builder.if_else(eq) as (then, otherwise):
                with then:
                    self.builder.call(self.rt_push, [arr_handle, val])
                with otherwise:
                    tmp = self.builder.call(self.rt_pop, [arr_handle])
                    self.builder.call(self.rt_push, [arr_handle, val])
            return

        if isinstance(node, nodes.ExprStmt):
            self._emit_expr(node.expr)
            return

        if isinstance(node, nodes.IfNode):
            condv = self._emit_expr(node.cond)
            bcond = self.builder.icmp_signed('!=', condv, ir.Constant(I64, 0))
            then_bb = self.current_fn.append_basic_block('if_then')
            else_bb = self.current_fn.append_basic_block('if_else')
            end_bb = self.current_fn.append_basic_block('if_end')
            self.builder.cbranch(bcond, then_bb, else_bb)

            self.builder.position_at_end(then_bb)
            for s in node.then_block:
                self._emit_statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

            self.builder.position_at_end(else_bb)
            if node.else_block:
                for s in node.else_block:
                    self._emit_statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

            self.builder.position_at_end(end_bb)
            return

        if isinstance(node, nodes.WhileNode):
            cond_bb = self.current_fn.append_basic_block('while_cond')
            body_bb = self.current_fn.append_basic_block('while_body')
            end_bb = self.current_fn.append_basic_block('while_end')

            self.builder.branch(cond_bb)
            self.builder.position_at_end(cond_bb)
            condv = self._emit_expr(node.cond)
            bcond = self.builder.icmp_signed('!=', condv, ir.Constant(I64, 0))
            self.builder.cbranch(bcond, body_bb, end_bb)

            self.builder.position_at_end(body_bb)
            for s in node.body:
                self._emit_statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(end_bb)
            return

        if isinstance(node, nodes.ForRangeNode):
            startv = self._emit_expr(node.start_expr)
            endv = self._emit_expr(node.end_expr)
            loop_ptr = self.builder.alloca(I64, name=node.varname)
            self.builder.store(startv, loop_ptr)

            cond_bb = self.current_fn.append_basic_block('for_cond')
            body_bb = self.current_fn.append_basic_block('for_body')
            end_bb = self.current_fn.append_basic_block('for_end')

            self.builder.branch(cond_bb)
            self.builder.position_at_end(cond_bb)
            cur = self.builder.load(loop_ptr)
            cmpv = self.builder.icmp_signed('<=', cur, endv)
            self.builder.cbranch(cmpv, body_bb, end_bb)

            self.builder.position_at_end(body_bb)
            self.locals[node.varname] = loop_ptr
            for s in node.body:
                self._emit_statement(s)
            cur2 = self.builder.load(loop_ptr)
            self.builder.store(self.builder.add(cur2, ir.Constant(I64, 1)), loop_ptr)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)
            self.builder.position_at_end(end_bb)
            return

        if isinstance(node, nodes.ForInNode):
            arr_handle = self._emit_expr(node.iterable_expr)
            length = self.builder.call(self.rt_length, [arr_handle])
            idx_ptr = self.builder.alloca(I64, name=node.varname + "_idx")
            self.builder.store(ir.Constant(I64, 0), idx_ptr)

            cond_bb = self.current_fn.append_basic_block('forin_cond')
            body_bb = self.current_fn.append_basic_block('forin_body')
            end_bb = self.current_fn.append_basic_block('forin_end')

            self.builder.branch(cond_bb)
            self.builder.position_at_end(cond_bb)
            idxv = self.builder.load(idx_ptr)
            cmpv = self.builder.icmp_signed('<', idxv, length)
            self.builder.cbranch(cmpv, body_bb, end_bb)

            self.builder.position_at_end(body_bb)
            elem = self.builder.call(self.rt_pop, [arr_handle])  # destructive read; pushed back later
            ptr = self.builder.alloca(I64, name=node.varname)
            self.builder.store(elem, ptr)
            self.locals[node.varname] = ptr

            for s in node.body:
                self._emit_statement(s)

            self.builder.call(self.rt_push, [arr_handle, elem])
            self.builder.store(self.builder.add(idxv, ir.Constant(I64, 1)), idx_ptr)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)
            self.builder.position_at_end(end_bb)
            return

        if isinstance(node, nodes.FuncDef):
            params = [I64] * len(node.params)
            fnty = ir.FunctionType(I64, params)
            fn = ir.Function(self.module, fnty, name=node.name)
            self.func_prototypes[node.name] = fn

            bb = fn.append_basic_block('entry')
            saved_builder = self.builder
            saved_func = self.current_fn
            saved_locals = dict(self.locals)

            self.builder = ir.IRBuilder(bb)
            self.current_fn = fn
            self.locals = {}

            for i, arg in enumerate(fn.args):
                arg.name = node.params[i]
                ptr = self.builder.alloca(I64, name=arg.name)
                self.builder.store(arg, ptr)
                self.locals[arg.name] = ptr

            returned = False
            for s in node.body:
                if isinstance(s, nodes.ReturnNode):
                    rv = self._emit_expr(s.expr)
                    self.builder.ret(rv)
                    returned = True
                    break
                else:
                    self._emit_statement(s)
            if not returned:
                self.builder.ret(ir.Constant(I64, 0))

            self.builder = saved_builder
            self.current_fn = saved_func
            self.locals = saved_locals
            return

        raise NotImplementedError(f"Statement emit not implemented: {type(node)}")

    def _emit_expr(self, node):
        if isinstance(node, nodes.Number):
            return ir.Constant(I64, node.value)

        if isinstance(node, nodes.String):
            handle = runtime._new_handle(node.value)
            return ir.Constant(I64, handle)

        if isinstance(node, nodes.VarAccess):
            if node.name in self.locals:
                return self.builder.load(self.locals[node.name])
            ptr = self.builder.alloca(I64, name=node.name)
            self.builder.store(ir.Constant(I64, 0), ptr)
            self.locals[node.name] = ptr
            return self.builder.load(ptr)

        if isinstance(node, nodes.ArrayLiteral):
            h = self.builder.call(self.rt_new_array, [])
            for e in node.elements:
                v = self._emit_expr(e)
                self.builder.call(self.rt_push, [h, v])
            return h

        if isinstance(node, nodes.BinOp):
            l = self._emit_expr(node.left)
            r = self._emit_expr(node.right)
            op = node.op
            if op == 'PLUS': return self.builder.add(l, r)
            if op == 'MINUS': return self.builder.sub(l, r)
            if op == 'MUL': return self.builder.mul(l, r)
            if op == 'DIV': return self.builder.sdiv(l, r)
            if op == 'MOD': return self.builder.srem(l, r)
            if op == 'EQ': return self._bool_i64(self.builder.icmp_signed('==', l, r))
            if op == 'NE': return self._bool_i64(self.builder.icmp_signed('!=', l, r))
            if op == 'GT': return self._bool_i64(self.builder.icmp_signed('>', l, r))
            if op == 'LT': return self._bool_i64(self.builder.icmp_signed('<', l, r))
            if op == 'GE': return self._bool_i64(self.builder.icmp_signed('>=', l, r))
            if op == 'LE': return self._bool_i64(self.builder.icmp_signed('<=', l, r))
            raise NotImplementedError(f"BinOp {op}")

        if isinstance(node, nodes.UnaryOp):
            v = self._emit_expr(node.operand)
            if node.op == 'MINUS':
                return self.builder.neg(v)
            raise NotImplementedError(f"Unary {node.op}")

        if isinstance(node, nodes.FuncCall):
            name = node.name
            if name == 'print' and len(node.args) > 0:
                argval = self._emit_expr(node.args[0])
                if self._node_has_string_literal(node.args[0]):
                    return self.builder.call(self.rt_print_str, [argval])
                else:
                    return self.builder.call(self.rt_print_int, [argval])
            args = [self._emit_expr(a) for a in node.args]
            if name == 'input':
                ph = args[0] if args else ir.Constant(I64, 0)
                return self.builder.call(self.rt_input, [ph])
            if name == 'push':
                return self.builder.call(self.rt_push, [args[0], args[1]])
            if name == 'pop':
                return self.builder.call(self.rt_pop, [args[0]])
            if name == 'length':
                return self.builder.call(self.rt_length, [args[0]])
            if name == 'isPrime':
                return self.builder.call(self.rt_isPrime, [args[0]])
            if name == 'sort':
                return self.builder.call(self.rt_sort, [args[0]])
            if name == 'sum':
                return self.builder.call(self.rt_sum, [args[0]])
            if name == 'contains':
                return self.builder.call(self.rt_contains, [args[0], args[1]])
            if name == 'clear':
                return self.builder.call(self.rt_clear, [args[0]])

            # user-defined function
            if name in self.func_prototypes:
                fn = self.func_prototypes[name]
                return self.builder.call(fn, args)
            gf = self.module.globals.get(name)
            if isinstance(gf, ir.Function):
                return self.builder.call(gf, args)
            raise Exception(f"Unknown function: {name}")

        raise NotImplementedError(f"Expr emit not implemented: {type(node)}")

    def _bool_i64(self, cmpval):
        return self.builder.zext(cmpval, I64)
