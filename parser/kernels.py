import sil_ast


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
