from llvmlite import ir, binding
from parser import (
    ProgramNode, MakeNode, ShowNode, LoopNode, IfNode,
    NumberNode, StringNode, IdentifierNode, BinaryOpNode
)


binding.initialize_all_targets()
binding.initialize_all_asmprinters()


class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="xlang_module")
        self.module.triple = binding.get_default_triple()
        
        self.builder = None
        self.func = None
        self.variables = {}
        self.string_counter = 0
        self.collected_vars = set()
        
        self.int_type = ir.IntType(64)
        self.bool_type = ir.IntType(1)
        self.char_ptr_type = ir.IntType(8).as_pointer()
        self.void_type = ir.VoidType()
        
        self._declare_printf()
    
    def _declare_printf(self):
        printf_type = ir.FunctionType(ir.IntType(32), [self.char_ptr_type], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")
    
    def _create_global_string(self, string: str) -> ir.GlobalVariable:
        string_bytes = (string + '\0').encode('utf-8')
        string_type = ir.ArrayType(ir.IntType(8), len(string_bytes))
        
        global_str = ir.GlobalVariable(self.module, string_type, name=f".str.{self.string_counter}")
        global_str.global_constant = True
        global_str.linkage = 'private'
        global_str.initializer = ir.Constant(string_type, bytearray(string_bytes))
        
        self.string_counter += 1
        return global_str
    
    def _get_string_ptr(self, global_str: ir.GlobalVariable):
        zero = ir.Constant(ir.IntType(32), 0)
        return self.builder.gep(global_str, [zero, zero], inbounds=True)
    
    def _collect_variables(self, node):
        if isinstance(node, MakeNode):
            self.collected_vars.add(node.name)
        elif isinstance(node, LoopNode):
            for stmt in node.body:
                self._collect_variables(stmt)
        elif isinstance(node, IfNode):
            for stmt in node.then_body:
                self._collect_variables(stmt)
            for stmt in node.else_body:
                self._collect_variables(stmt)
        elif isinstance(node, ProgramNode):
            for stmt in node.statements:
                self._collect_variables(stmt)
    
    def generate(self, ast: ProgramNode):
        func_type = ir.FunctionType(ir.IntType(32), [])
        self.func = ir.Function(self.module, func_type, name="main")
        
        entry_block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        
        self._collect_variables(ast)
        
        for var_name in self.collected_vars:
            ptr = self.builder.alloca(self.int_type, name=var_name)
            self.builder.store(ir.Constant(self.int_type, 0), ptr)
            self.variables[var_name] = ptr
        
        for statement in ast.statements:
            self._generate_statement(statement)
        
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))
        
        return self.module
    
    def _generate_statement(self, node):
        if isinstance(node, MakeNode):
            self._generate_make(node)
        elif isinstance(node, ShowNode):
            self._generate_show(node)
        elif isinstance(node, LoopNode):
            self._generate_loop(node)
        elif isinstance(node, IfNode):
            self._generate_if(node)
    
    def _generate_make(self, node: MakeNode):
        value = self._generate_expression(node.value)
        ptr = self.variables[node.name]
        self.builder.store(value, ptr)
    
    def _generate_show(self, node: ShowNode):
        if isinstance(node.value, StringNode):
            format_str = self._create_global_string(node.value.value + "\n")
            format_ptr = self._get_string_ptr(format_str)
            self.builder.call(self.printf, [format_ptr])
        else:
            value = self._generate_expression(node.value)
            format_str = self._create_global_string("%lld\n")
            format_ptr = self._get_string_ptr(format_str)
            self.builder.call(self.printf, [format_ptr, value])
    
    def _generate_loop(self, node: LoopNode):
        loop_cond = self.func.append_basic_block(name="loop.cond")
        loop_body = self.func.append_basic_block(name="loop.body")
        loop_end = self.func.append_basic_block(name="loop.end")
        
        self.builder.branch(loop_cond)
        
        self.builder.position_at_end(loop_cond)
        cond_value = self._generate_expression(node.condition)
        self.builder.cbranch(cond_value, loop_body, loop_end)
        
        self.builder.position_at_end(loop_body)
        for stmt in node.body:
            self._generate_statement(stmt)
        
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_cond)
        
        self.builder.position_at_end(loop_end)
    
    def _generate_if(self, node: IfNode):
        then_block = self.func.append_basic_block(name="if.then")
        else_block = self.func.append_basic_block(name="if.else")
        merge_block = self.func.append_basic_block(name="if.merge")
        
        cond_value = self._generate_expression(node.condition)
        self.builder.cbranch(cond_value, then_block, else_block)
        
        self.builder.position_at_end(then_block)
        for stmt in node.then_body:
            self._generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        self.builder.position_at_end(else_block)
        for stmt in node.else_body:
            self._generate_statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        self.builder.position_at_end(merge_block)
    
    def _generate_expression(self, node):
        if isinstance(node, NumberNode):
            return ir.Constant(self.int_type, node.value)
        
        elif isinstance(node, IdentifierNode):
            ptr = self.variables.get(node.name)
            if ptr is None:
                raise NameError(f"Undefined variable: {node.name}")
            return self.builder.load(ptr, name=node.name + ".val")
        
        elif isinstance(node, BinaryOpNode):
            left = self._generate_expression(node.left)
            right = self._generate_expression(node.right)
            
            if node.op == '+':
                return self.builder.add(left, right, name="addtmp")
            elif node.op == '-':
                return self.builder.sub(left, right, name="subtmp")
            elif node.op == '*':
                return self.builder.mul(left, right, name="multmp")
            elif node.op == '/':
                return self.builder.sdiv(left, right, name="divtmp")
            elif node.op == '<':
                return self.builder.icmp_signed('<', left, right, name="cmptmp")
            elif node.op == '==':
                return self.builder.icmp_signed('==', left, right, name="eqtmp")
            else:
                raise ValueError(f"Unknown operator: {node.op}")
        
        elif isinstance(node, StringNode):
            return node.value
        
        else:
            raise TypeError(f"Unknown expression type: {type(node)}")
    
    def verify(self):
        llvm_ir = str(self.module)
        mod = binding.parse_assembly(llvm_ir)
        mod.verify()
        return mod
    
    def compile_and_run(self):
        mod = self.verify()
        
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        
        backing_mod = binding.parse_assembly(str(self.module))
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        engine.finalize_object()
        
        main_ptr = engine.get_function_address("main")
        
        import ctypes
        main_func = ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)
        return main_func()
