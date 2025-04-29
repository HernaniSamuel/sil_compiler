def tokenize(source_code):
    tokens = []
    current = ''
    specials = {'(', ')', '{', '}', ':', ',', ';', '=', '+', '-', '*', '/', '%', '!', '<', '>', '&', '|'}
    multi_char_specials = {'->', '==', '!=', '<=', '>=', '&&', '||', '//'}

    i = 0
    while i < len(source_code):
        char = source_code[i]

        # Tratamento de comentários
        if char == '/':
            if i + 1 < len(source_code):
                next_char = source_code[i+1]
                if next_char == '/':
                    i += 2
                    while i < len(source_code) and source_code[i] != '\n':
                        i += 1
                    continue
                elif next_char == '*':
                    i += 2
                    while i+1 < len(source_code) and not (source_code[i] == '*' and source_code[i+1] == '/'):
                        i += 1
                    i += 2
                    continue

        # Tenta pegar operadores de dois caracteres
        if i + 1 < len(source_code):
            two_chars = source_code[i] + source_code[i+1]
            if two_chars in multi_char_specials:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(two_chars)
                i += 2
                continue

        # Se espaço ou quebra
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

            # Se for @cpu, capturar tudo bruto depois
            if word == "@cpu":
                raw_code = ""
                while i < len(source_code):
                    raw_code += source_code[i]
                    i += 1
                tokens.append(raw_code)
                break  # já lemos tudo
            continue
        elif char in specials:
            if current:
                tokens.append(current)
                current = ''
            tokens.append(char)
            i += 1
        else:
            current += char
            i += 1

    if current:
        tokens.append(current)

    return tokens
