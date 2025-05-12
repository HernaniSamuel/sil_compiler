import sil_ast
from . import statements
from . import flow
from . import kernels
from . import expressions


class Parser:
    """
    Top-level parser for Mini-SIL source code.

    Delegates sub-parsing to the appropriate module:
    - statements.py: declarations, assignments, etc.
    - flow.py: control flow structures
    - kernels.py: kernel definitions
    - expressions.py: all expression handling
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.binary_operators = [
            '+', '-', '*', '/', '//', '%', '==', '!=',
            '<', '>', '<=', '>=', '&&', '||', '<<', '>>'
        ]
        self.debug = False

    def peek(self):
        """Returns the current token without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next(self):
        """Consumes and returns the next token."""
        tok = self.peek()
        if tok is not None:
            self.pos += 1
            if self.debug:
                print(f"Consumed token: {tok}")
        return tok

    def expect(self, expected):
        """
        Consumes a token and raises an error if it doesn't match the expected value.
        Includes context around the error for debugging.
        """
        tok = self.next()
        if tok != expected:
            start_pos = max(0, self.pos - 5)
            end_pos = min(len(self.tokens), self.pos + 5)
            context = self.tokens[start_pos:end_pos]
            raise Exception(f"Expected '{expected}', but got '{tok}'. Context: {context}")

    def normalize_type(self, typ):
        """
        Converts legacy types (like 'int') to the canonical type used internally.
        Allows pointer types to pass through.
        """
        if typ == "int":
            return "uint"
        if typ.startswith("ptr_"):
            return typ
        return typ

    def parse(self):
        """
        Entry point: parses an entire program from the token list.
        Returns a list of AST nodes.
        """
        ast = []
        while self.peek() is not None:
            try:
                stmt = self.parse_statement()
                if stmt:
                    ast.append(stmt)
            except Exception as e:
                print(f"Error parsing statement at position {self.pos}: {str(e)}")
                self.error_recovery()
                raise  # Let the exception propagate after recovery
        return ast

    def error_recovery(self):
        """
        Basic recovery strategy: skip tokens until we find a semicolon or closing brace.
        """
        while self.peek() not in [';', '}', None]:
            self.next()
        if self.peek() is not None:
            self.next()

    def parse_cpu_block(self):
        """
        Parses a @cpu block and returns a CpuBlock node containing the raw code string.
        """
        self.expect("@cpu")
        raw_code = self.next()  # The next token should be the full code block
        return sil_ast.CpuBlock(raw_code)

    # Statement and expression parsing delegates

    def parse_statement(self):
        return statements.parse_statement(self)

    def parse_var_decl(self):
        return statements.parse_var_decl(self)

    def parse_const_decl(self):
        return statements.parse_const_decl(self)

    def parse_assign(self):
        return statements.parse_assign(self)

    def parse_return(self):
        return statements.parse_return(self)

    def parse_if(self):
        return flow.parse_if(self)

    def parse_loop(self):
        return flow.parse_loop(self)

    def parse_kernel(self):
        return kernels.parse_kernel(self)

    def parse_params(self):
        return kernels.parse_params(self)

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        return expressions.parse_logical_or(self)

    def parse_logical_and(self):
        return expressions.parse_logical_and(self)

    def parse_equality(self):
        return expressions.parse_equality(self)

    def parse_relational(self):
        return expressions.parse_relational(self)

    def parse_additive(self):
        return expressions.parse_additive(self)

    def parse_multiplicative(self):
        return expressions.parse_multiplicative(self)

    def parse_unary(self):
        return expressions.parse_unary(self)

    def parse_primary(self):
        return expressions.parse_primary(self)

    def parse_bitwise_block(self):
        return expressions.parse_bitwise_block(self)

    def parse_bitwise_expression(self):
        return expressions.parse_bitwise_expression(self)

    def parse_bitwise_primary(self):
        return expressions.parse_bitwise_primary(self)

    def parse_bitwise_unary(self):
        return expressions.parse_bitwise_unary(self)

    def parse_cast_block(self):
        return expressions.parse_cast_block(self)

    def _is_identifier(self, token):
        return statements.is_identifier(self, token)
