import sil_ast
from . import statements
from . import flow
from . import kernels
from . import expressions


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.binary_operators = ['+', '-', '*', '/', '//', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '<<', '>>']
        self.debug = False

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next(self):
        tok = self.peek()
        if tok is not None:
            self.pos += 1
            if self.debug:
                print(f"Consumido token: {tok}")
        return tok

    def expect(self, expected):
        tok = self.next()
        if tok != expected:
            # Adicionar contexto para ajudar na depuração
            start_pos = max(0, self.pos - 5)
            end_pos = min(len(self.tokens), self.pos + 5)
            context = self.tokens[start_pos:end_pos]
            raise Exception(f"Esperado '{expected}', mas encontrado '{tok}'. Contexto: {context}")

    def normalize_type(self, typ):
        if typ == "int":
            return "uint"
        # Deixar passar ponteiros como "ptr_uint", "ptr_float", "ptr_bool"
        if typ.startswith("ptr_"):
            return typ
        return typ

    def parse(self):
        statements = []
        while self.peek() is not None:
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except Exception as e:
                print(f"Erro ao analisar declaração na posição {self.pos}: {str(e)}")
                # Tentar recuperar para continuar a análise
                self.error_recovery()
                raise  # Re-lançar a exceção após tentativa de recuperação

        return statements

    def error_recovery(self):
        """Tentativa básica de recuperação de erro: avançar até o próximo ';' ou '}'"""
        while self.peek() not in [';', '}', None]:
            self.next()
        if self.peek() is not None:
            self.next()  # Consumir o ';' ou '}'

    def parse_cpu_block(self):
        self.expect("@cpu")
        raw_code = self.next()  # O próximo token é TODO o código do bloco
        return sil_ast.CpuBlock(raw_code)

    def parse_assign(self):
        return statements.parse_assign(self)

    def parse_statement(self):
        return statements.parse_statement(self)

    def _is_identifier(self, token):
        return statements.is_identifier(self, token)

    def parse_var_decl(self):
        return statements.parse_var_decl(self)

    def parse_const_decl(self):
        return statements.parse_const_decl(self)

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

    def parse_unary(self):
        return expressions.parse_unary(self)

    def parse_additive(self):
        return expressions.parse_additive(self)

    def parse_multiplicative(self):
        return expressions.parse_multiplicative(self)

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
