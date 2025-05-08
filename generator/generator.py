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
        # Add a dictionary to store constant types
        self.constant_types = {}

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

        # Process all constant declarations first
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                self._process_constants(node.body)

        functions = []
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                functions.extend(self.generate_kernel(node))

        result = (
                header + capabilities + extensions + memory_model + entry_points +
                execution_modes + debug + annotations + types + func_types +
                self.module_types + self._const_instructions() + functions
        )

        return "\n".join(result)

    def _process_constants(self, statements):
        """Pre-process all constant declarations to make them available to expressions"""
        for stmt in statements:
            if isinstance(stmt, sil_ast.ConstDecl):
                if isinstance(stmt.value, sil_ast.Literal):
                    # Process direct literal constants
                    value = stmt.value.value
                    const_type = 'uint' if isinstance(value, int) else 'float'
                    const_id = self.get_constant(value)
                    # Store the constant ID with its name
                    self.constants[stmt.name] = const_id
                    # Store the constant type separately
                    self.constant_types[stmt.name] = const_type
                elif isinstance(stmt.value, sil_ast.Ident):
                    # For variable references, we can't process yet, but we'll store for later
                    # Use getattr to safely check for value_type attribute
                    # If it doesn't exist, default to 'uint' as a fallback
                    self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')
                    # Just store the name for now, we'll resolve it during actual generation
                    self.constants[stmt.name] = None
                else:
                    # For other expression types, default to uint if var_type is not specified
                    self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')
                    self.constants[stmt.name] = None

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

    # -------------------------------------------------
    #  Constantes únicas que realmente vão para o módulo
    # -------------------------------------------------
    def _const_instructions(self):
        """Retorna apenas as linhas OpConstant/OpConstantFalse,
        filtrando IDs soltos e evitando duplicatas."""
        out, seen = [], set()
        for v in self.constants.values():
            if '=' in v and v not in seen:   # instr. completas têm "="
                out.append(v)
                seen.add(v)
        return out
