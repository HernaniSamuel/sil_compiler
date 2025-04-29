import sys
import lexer
import parser
import generator
import sil_ast
from runtime.host import HostRuntime
import numpy as np
import subprocess
import os
import traceback


def display_tokens(tokens, max_per_line=10):
    """Exibe tokens em um formato mais legível"""
    print("\nTOKENS GERADOS:")
    for i in range(0, len(tokens), max_per_line):
        chunk = tokens[i:i + max_per_line]
        line = " ".join([f"'{t}'" if isinstance(t, str) else str(t) for t in chunk])
        print(f"{i:4d}: {line}")
    print()


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py caminho/para/arquivo.sil [--debug]")
        sys.exit(1)

    filename = sys.argv[1]
    debug_mode = "--debug" in sys.argv

    basename = os.path.splitext(os.path.basename(filename))[0]
    folder = os.path.dirname(filename)
    if not folder:
        folder = "."

    try:
        with open(filename, "r") as f:
            source_code = f.read()

        print(f"Compilando {filename}...")

        # Tokenizar o código fonte
        tokens = lexer.tokenize(source_code)

        # Exibir tokens de forma mais detalhada
        if debug_mode:
            display_tokens(tokens)
        else:
            # Mostrar apenas os primeiros 20 tokens
            print("Tokens gerados (primeiros 20):", tokens[:20])

        # Verificar tokens específicos
        if '//' in tokens:
            print(f"ATENÇÃO: Token '//' encontrado nas posições: {[i for i, t in enumerate(tokens) if t == '//']}")
        if ';' not in tokens:
            print("ALERTA: Nenhum token ';' encontrado!")

        # Analisar a árvore sintática
        p = parser.Parser(tokens)
        p.debug = debug_mode  # Habilitar modo de depuração se solicitado
        ast_tree = p.parse()

        # Exibir informações sobre a AST
        if debug_mode:
            print("\nÁRVORE SINTÁTICA:")
            for i, node in enumerate(ast_tree):
                print(f"Node {i}: {type(node).__name__}")
                if isinstance(node, sil_ast.Kernel):
                    print(f"  Kernel: {node.name}")
                    print(f"  Params: {len(node.params)}")
                    print(f"  Body statements: {len(node.body)}")
                elif isinstance(node, sil_ast.CpuBlock):
                    print(f"  CpuBlock: {node.code[:50]}...")

        # Separar nós do CPU e GPU
        g = generator.Generator()
        gpu_nodes = [node for node in ast_tree if not isinstance(node, sil_ast.CpuBlock)]
        cpu_nodes = [node for node in ast_tree if isinstance(node, sil_ast.CpuBlock)]

        # Compilar GPU
        spv_filename = None
        if gpu_nodes:
            print("Gerando código SPIR-V...")
            assembly = g.generate(gpu_nodes)

            spvasm_filename = os.path.join(folder, f"{basename}.spvasm")
            spv_filename = os.path.join(folder, f"{basename}.spv")

            # Salva o SPIR-V assembly
            with open(spvasm_filename, "w") as f:
                f.write(assembly)

            # Compila para SPIR-V binário usando spirv-as
            print(f"Compilando SPIR-V assembly para {spv_filename}...")
            result = subprocess.run(["spirv-as", spvasm_filename, "-o", spv_filename],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print("Erro ao compilar SPIR-V:")
                print(result.stderr)
                sys.exit(1)
            print("Compilação SPIR-V concluída com sucesso.")

        # Validar SPIR-V com spirv-val
        print(f"Validando SPIR-V {spv_filename}...")
        result = subprocess.run(["spirv-val", spv_filename], capture_output=True, text=True)
        if result.returncode != 0:
            print("Erro na validação SPIR-V:")
            print(result.stderr)
            sys.exit(1)
        print("SPIR-V validado com sucesso.")

        # Executar CPU
        if cpu_nodes and spv_filename:
            print("Executando bloco de código CPU...")
            rt = HostRuntime()
            rt.load_spirv(spv_filename)  # carrega o SPIR-V correspondente
            globals()['rt'] = rt

            for node in cpu_nodes:
                exec(node.code, globals())

            print("Execução do bloco CPU concluída.")

    except Exception as e:
        print(f"Erro durante a compilação: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()