def tokenize(source_code):
    tokens = []
    current = ''
    specials = {'(', ')', '{', '}', ':', ',', ';', '=', '+', '-', '*', '/', '%', '!', '<', '>', '&', '|', '~', '.'}
    multi_char_specials = {'->', '==', '!=', '<=', '>=', '&&', '||', '//', '>>', '<<'}

    i = 0
    while i < len(source_code):
        # Apenas comentários de bloco /* ... */
        if i + 1 < len(source_code) and source_code[i] == '/' and source_code[i + 1] == '*':
            i += 2
            while i + 1 < len(source_code) and not (source_code[i] == '*' and source_code[i + 1] == '/'):
                i += 1
            if i + 1 < len(source_code):
                i += 2  # Pular o */
            else:
                i += 1  # Caso tenha chegado ao fim do arquivo
            continue

        # Verificar operadores de dois caracteres (incluindo //)
        if i + 1 < len(source_code):
            two_chars = source_code[i] + source_code[i + 1]
            if two_chars in multi_char_specials:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(two_chars)
                i += 2
                continue

        char = source_code[i]

        if char.isspace():
            if current:
                tokens.append(current)
                current = ''
            i += 1
        elif char == '@':
            if current:
                tokens.append(current)
                current = ''
            word = '@'
            i += 1
            while i < len(source_code) and (source_code[i].isalnum() or source_code[i] == '_'):
                word += source_code[i]
                i += 1
            tokens.append(word)

            if word == "@cpu":
                raw_code = ""
                # Pular espaços em branco após @cpu
                while i < len(source_code) and source_code[i].isspace():
                    i += 1
                # Capturar todo o código do bloco CPU
                while i < len(source_code):
                    raw_code += source_code[i]
                    i += 1
                tokens.append(raw_code)
                break
            continue
        elif char in specials:
            if current:
                # Detectar se current + char + próximo é um float (ex: 2 . 5)
                if (
                        char == '.' and
                        current.isdigit() and
                        i + 1 < len(source_code) and source_code[i + 1].isdigit()
                ):
                    current += char  # incluir o ponto como parte do número
                    i += 1
                    continue

                tokens.append(current)
                current = ''
            tokens.append(char)
            i += 1

        else:
            current += char
            i += 1

    if current:
        tokens.append(current)

    # Debug para ver todos os tokens (descomente se necessário)
    # print("\nTODOS OS TOKENS:", tokens)

    return tokens