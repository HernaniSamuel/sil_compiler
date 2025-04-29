import sys
import lexer
import parser
import generator
import sil_ast
from runtime.host import HostRuntime
import numpy as np
import subprocess
import os

def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py arquivo.sil")
        sys.exit(1)

    filename = sys.argv[1]
    basename = os.path.splitext(os.path.basename(filename))[0]

    with open(filename, "r") as f:
        source_code = f.read()

    tokens = lexer.tokenize(source_code)
    p = parser.Parser(tokens)
    ast_tree = p.parse()

    g = generator.Generator()
    gpu_nodes = [node for node in ast_tree if not isinstance(node, sil_ast.CpuBlock)]
    cpu_nodes = [node for node in ast_tree if isinstance(node, sil_ast.CpuBlock)]

    # Compilar GPU
    if gpu_nodes:
        assembly = g.generate(gpu_nodes)

        # Garante a pasta build
        os.makedirs("build", exist_ok=True)

        spvasm_filename = f"build/{basename}.spvasm"
        spv_filename = f"build/{basename}.spv"

        # Salva o SPIR-V assembly
        with open(spvasm_filename, "w") as f:
            f.write(assembly)

        # Compila para SPIR-V binário usando spirv-as
        result = subprocess.run(["spirv-as", spvasm_filename, "-o", spv_filename], capture_output=True, text=True)
        if result.returncode != 0:
            print("Erro ao compilar SPIR-V:")
            print(result.stderr)
            sys.exit(1)

    # Executar CPU
    if cpu_nodes:
        rt = HostRuntime()
        rt.load_spirv(spv_filename)  # <<< Agora carrega o SPIR-V automático antes do @cpu
        globals()['rt'] = rt

        for node in cpu_nodes:
            exec(node.code, globals())

if __name__ == "__main__":
    main()
