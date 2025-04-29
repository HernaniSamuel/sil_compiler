# parser.py

import sil_ast


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.binary_operators = ['+', '-', '*', '/', '//', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||']
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

    def parse_statement(self):
        tok = self.peek()

        if self.debug:
            print(f"Analisando declaração, token: {tok}")

        if tok == "var":
            return self.parse_var_decl()
        elif tok == "const":
            return self.parse_const_decl()
        elif tok == "kernel":
            return self.parse_kernel()
        elif tok == "return":
            return self.parse_return()
        elif tok == "if":
            return self.parse_if()
        elif tok == "@cpu":
            return self.parse_cpu_block()
        else:
            # Verifica se é um identificador de variável antes de tentar parse_assign
            if self._is_identifier(tok) and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1] == "=":
                return self.parse_assign()
            else:
                raise Exception(f"Token inesperado: '{tok}' na posição {self.pos}")

    def _is_identifier(self, token):
        if token is None:
            return False
        if not isinstance(token, str):
            return False
        # Um identificador válido começa com letra ou _ e pode conter letras, números e _
        if not token:
            return False
        if not (token[0].isalpha() or token[0] == '_'):
            return False
        for char in token:
            if not (char.isalnum() or char == '_'):
                return False
        return True

    def parse_cpu_block(self):
        self.expect("@cpu")
        raw_code = self.next()  # O próximo token é TODO o código do bloco
        return sil_ast.CpuBlock(raw_code)

    def parse_if(self):
        self.expect("if")
        self.expect("(")
        condition = self.parse_expression()
        self.expect(")")
        self.expect("{")
        then_body = []
        while self.peek() != "}":
            if self.peek() is None:
                raise Exception("Fim inesperado do arquivo ao analisar bloco 'if'")
            then_body.append(self.parse_statement())
        self.expect("}")

        else_body = None
        if self.peek() == "else":
            self.expect("else")
            self.expect("{")
            else_body = []
            while self.peek() != "}":
                if self.peek() is None:
                    raise Exception("Fim inesperado do arquivo ao analisar bloco 'else'")
                else_body.append(self.parse_statement())
            self.expect("}")

        return sil_ast.If(condition, then_body, else_body)

    def parse_var_decl(self):
        self.expect("var")
        name = self.next()
        if not self._is_identifier(name):
            raise Exception(f"Nome de variável inválido: '{name}'")

        self.expect(":")
        declared_type = self.normalize_type(self.next())
        self.expect("=")
        value = self.parse_expression()

        # Debug: posição atual antes de expect(";")
        if self.debug:
            print(f"Antes de expect(';'), posição={self.pos}, próximo token={self.peek()}")

        self.expect(";")

        # Auto-corrigir tipo se o valor for float/int
        if isinstance(value, sil_ast.Literal):
            if isinstance(value.value, float) and declared_type != "float":
                declared_type = "float"
            if isinstance(value.value, int) and declared_type not in ("int", "uint"):
                declared_type = "uint"

        return sil_ast.VarDecl(name, declared_type, value)

    def parse_const_decl(self):
        self.expect("const")
        name = self.next()
        self.expect(":")
        declared_type = self.normalize_type(self.next())
        self.expect("=")
        value = self.parse_expression()
        self.expect(";")

        # Auto-corrigir tipo se o valor for float/int
        if isinstance(value, sil_ast.Literal):
            if isinstance(value.value, float) and declared_type != "float":
                declared_type = "float"
            if isinstance(value.value, int) and declared_type not in ("int", "uint"):
                declared_type = "uint"

        return sil_ast.ConstDecl(name, declared_type, value)

    def parse_kernel(self):
        self.expect("kernel")
        name = self.next()
        if not self._is_identifier(name):
            raise Exception(f"Nome de kernel inválido: '{name}'")

        self.expect("(")
        params = self.parse_params()
        self.expect(")")
        self.expect("{")
        body = []

        # Imprimir todos os tokens da função para debug
        if self.debug:
            print(f"Kernel '{name}' - tokens do corpo:")
            debug_pos = self.pos
            debug_tokens = []
            open_braces = 1  # Já estamos dentro de uma abertura de chave

            while debug_pos < len(self.tokens) and open_braces > 0:
                if self.tokens[debug_pos] == '{':
                    open_braces += 1
                elif self.tokens[debug_pos] == '}':
                    open_braces -= 1
                if open_braces > 0:  # Não incluir a chave de fechamento
                    debug_tokens.append(self.tokens[debug_pos])
                debug_pos += 1

            print(debug_tokens)

        while self.peek() != "}":
            if self.peek() is None:
                raise Exception(f"Fim inesperado do arquivo ao analisar corpo do kernel '{name}'")

            try:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            except Exception as e:
                print(f"Erro ao analisar declaração no kernel '{name}': {str(e)}")
                self.error_recovery()
                if self.peek() == "}":
                    break  # Saímos do corpo do kernel durante a recuperação
                raise  # Re-lançar exceção após tentativa de recuperação

        self.expect("}")
        return sil_ast.Kernel(name, params, "void", body)

    def parse_params(self):
        params = []
        while self.peek() != ")":
            pname = self.next()
            if not self._is_identifier(pname):
                raise Exception(f"Nome de parâmetro inválido: '{pname}'")

            self.expect(":")
            ptype = self.normalize_type(self.next())
            params.append(sil_ast.Param(pname, ptype))

            if self.peek() == ",":
                self.next()
            elif self.peek() != ")":
                raise Exception(f"Esperado ',' ou ')' após parâmetro, mas encontrado '{self.peek()}'")

        return params

    def parse_return(self):
        self.expect("return")
        value = None
        if self.peek() != ";":
            value = self.parse_expression()
        self.expect(";")
        return sil_ast.Return(value)

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_unary(self):
        tok = self.peek()
        if tok == '!':
            self.next()
            operand = self.parse_unary()
            return sil_ast.UnaryOp('!', operand)
        elif tok == '-':
            self.next()
            operand = self.parse_unary()
            return sil_ast.UnaryOp('-', operand)
        else:
            return self.parse_primary()

    def parse_logical_or(self):
        left = self.parse_logical_and()
        while self.peek() == '||':
            op = self.next()
            right = self.parse_logical_and()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_logical_and(self):
        left = self.parse_equality()
        while self.peek() == '&&':
            op = self.next()
            right = self.parse_equality()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.peek() in ['==', '!=']:
            op = self.next()
            right = self.parse_relational()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.peek() in ['<', '>', '<=', '>=']:
            op = self.next()
            right = self.parse_additive()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek() in ['+', '-']:
            op = self.next()
            right = self.parse_multiplicative()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek() in ['*', '/', '//', '%']:
            op = self.next()
            right = self.parse_unary()
            left = sil_ast.BinaryOp(left, op, right)
        return left

    def parse_primary(self):
        tok = self.peek()

        # Detectar parênteses para subexpressões
        if tok == "(":
            self.next()  # Consumir o parêntese de abertura
            expr = self.parse_expression()
            if self.peek() != ")":
                raise Exception(f"Esperado ')', mas encontrado '{self.peek()}'")
            self.next()  # Consumir o parêntese de fechamento
            return expr

        # Caso contrário, proceder com a análise normal
        tok = self.next()

        if tok is None:
            raise Exception("Fim inesperado da entrada durante a análise da expressão")

        # Verificar literais numéricos
        if isinstance(tok, str) and tok.isdigit():
            return sil_ast.Literal(int(tok))

        try:
            # Verificar se é um float
            if isinstance(tok, str) and '.' in tok:
                return sil_ast.Literal(float(tok))
            # Verificar se é um int
            if isinstance(tok, str) and tok.lstrip('-').isdigit():
                return sil_ast.Literal(int(tok))
        except ValueError:
            pass

        # Se não é um literal numérico, deve ser um identificador
        if self._is_identifier(tok):
            return sil_ast.Ident(tok)
        else:
            raise Exception(f"Token inesperado na expressão: '{tok}'")

    def parse_assign(self):
        name = self.next()
        if name is None:
            raise Exception("Esperado identificador no início da atribuição")
        if self.peek() != "=":
            raise Exception(f"Esperado '=' depois de '{name}', mas encontrado '{self.peek()}'")
        self.expect("=")
        value = self.parse_expression()
        self.expect(";")
        return sil_ast.Assign(name, value)