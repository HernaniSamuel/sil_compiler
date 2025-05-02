import sil_ast
from .  import types as t
from . import expressions
from .functions import collect_entry_points_and_function_types, generate_kernel
from . import flow
from . import statements


class Generator:
    def __init__(self):
        self.next_id = 1
        self.type_ids = {}
        self.var_ids = {}
        self.param_ids = {}
        self.kernel_func_ids = {}
        self.func_type_ids = {}
        self.constants = {}
        self.module_types = []

    def new_id(self):
        id = self.next_id
        self.next_id += 1
        return f"%{id}"

    def generate(self, ast_tree):
        header = ["; SPIR-V", "; Version: 1.0"]
        capabilities = ["OpCapability Kernel"]
        extensions = []
        memory_model = ["OpMemoryModel Logical OpenCL"]
        execution_modes = []
        debug = []
        annotations = []

        types = t.generate_builtin_types(self)
        entry_points, func_types = collect_entry_points_and_function_types(self, ast_tree)

        functions = []
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                functions.extend(self.generate_kernel(node))

        result = (
                header + capabilities + extensions + memory_model + entry_points +
                execution_modes + debug + annotations + types + func_types +
                self.module_types + list(self.constants.values()) + functions
        )

        return "\n".join(result)

    def generate_kernel(self, node):
        return generate_kernel(self, node)

    def get_constant(self, value):
        return t.get_constant(self, value)

    def get_constant_false(self):
        return t.get_constant_false(self)

    def generate_expr(self, expr):
        return expressions.generate_expr(self, expr)

    def generate_var_only(self, stmt):
        return statements.generate_var_only(self, stmt)

    def generate_stmt(self, stmt):
        return statements.generate_stmt(self, stmt)

    def generate_if(self, stmt):
        return flow.generate_if(self, stmt)

    def generate_loop(self, stmt):
        return flow.generate_loop(self, stmt)
