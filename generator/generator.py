import sil_ast
from . import types as t
from . import expressions
from .functions import collect_entry_points_and_function_types, generate_kernel
from . import flow
from . import statements


class Generator:
    """
    Responsible for converting a parsed SIL AST into SPIR-V code.

    This includes:
    - Type declarations
    - Constant generation
    - Kernel structure and function generation
    - Expression and statement compilation
    """

    def __init__(self):
        self.next_id = 1  # ID counter for SPIR-V %IDs

        self.type_ids = {}          # Maps type names to SPIR-V IDs
        self.var_ids = {}           # Maps variable names to (ID, type)
        self.param_ids = {}         # Maps parameter names to (ID, type)
        self.kernel_func_ids = {}   # Maps kernel names to function IDs
        self.func_type_ids = {}     # Maps kernel names to function type IDs

        self.constants = {}         # Maps literal values or const names to SPIR-V code
        self.constant_types = {}    # Maps const names to types
        self.module_types = []      # Additional custom types if needed

    def new_id(self):
        """
        Returns a new unique SPIR-V ID.
        """
        id = self.next_id
        self.next_id += 1
        return f"%{id}"

    def generate(self, ast_tree):
        """
        Main entry point: converts the full AST into a SPIR-V program.

        Args:
            ast_tree (list): List of top-level AST nodes.

        Returns:
            str: The full SPIR-V code as a single string.
        """
        header = ["; SPIR-V", "; Version: 1.0"]
        capabilities = ["OpCapability Kernel"]
        extensions = []
        memory_model = ["OpMemoryModel Logical OpenCL"]
        execution_modes = []
        debug = []
        annotations = []

        # 1. Register built-in types
        types = t.generate_builtin_types(self)

        # 2. Collect kernel entry points and function types
        entry_points, func_types = collect_entry_points_and_function_types(self, ast_tree)

        # 3. Pre-process constants to resolve literals early
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                self._process_constants(node.body)

        # 4. Generate functions from kernels
        functions = []
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                functions.extend(self.generate_kernel(node))

        # 5. Combine all pieces of the module
        result = (
            header
            + capabilities
            + extensions
            + memory_model
            + entry_points
            + execution_modes
            + debug
            + annotations
            + types
            + func_types
            + self.module_types
            + self._const_instructions()
            + functions
        )

        return "\n".join(result)

    def _process_constants(self, statements):
        """
        Pre-processes constant declarations before full code generation.
        Caches literal values or defers complex expressions.

        Args:
            statements (list): List of statements inside a kernel.
        """
        for stmt in statements:
            if isinstance(stmt, sil_ast.ConstDecl):
                if isinstance(stmt.value, sil_ast.Literal):
                    value = stmt.value.value
                    const_type = 'uint' if isinstance(value, int) else 'float'
                    const_id = self.get_constant(value)
                    self.constants[stmt.name] = const_id
                    self.constant_types[stmt.name] = const_type

                elif isinstance(stmt.value, sil_ast.Ident):
                    # Reference to another variable (defer resolution)
                    self.constants[stmt.name] = None
                    self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')

                else:
                    # More complex expressions (defer resolution)
                    self.constants[stmt.name] = None
                    self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')

    def _const_instructions(self):
        """
        Returns only finalized SPIR-V constant declarations.

        Returns:
            list[str]: SPIR-V OpConstant or OpConstantFalse lines.
        """
        out = []
        seen = set()
        for v in self.constants.values():
            if '=' in v and v not in seen:
                out.append(v)
                seen.add(v)
        return out

    # --- Delegates ---

    def generate_kernel(self, node):
        return generate_kernel(self, node)

    def generate_expr(self, expr):
        return expressions.generate_expr(self, expr)

    def generate_stmt(self, stmt):
        return statements.generate_stmt(self, stmt)

    def generate_var_only(self, stmt):
        return statements.generate_var_only(self, stmt)

    def generate_if(self, stmt):
        return flow.generate_if(self, stmt)

    def generate_loop(self, stmt):
        return flow.generate_loop(self, stmt)

    def get_constant(self, value):
        return t.get_constant(self, value)

    def get_constant_false(self):
        return t.get_constant_false(self)
