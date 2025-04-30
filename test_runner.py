import subprocess
import sys
import os
import glob

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def run_command(command, description):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip(), e.stderr.strip()

def main():
    print(f"{YELLOW}==== RODANDO TODOS OS TESTES SIL ===={RESET}")

    test_files = glob.glob("sil_tests/**/*.sil", recursive=True)
    if not test_files:
        print(f"{RED}Nenhum teste encontrado em sil_tests/**/*{RESET}")
        return

    passed = []
    failed = []

    for test_file in sorted(test_files):
        print(f"\n{YELLOW}>> Executando teste: {test_file}{RESET}")
        ok, stdout, stderr = run_command(f"python main.py {test_file}", f"Compilando e executando {os.path.basename(test_file)}")

        if ok:
            print(f"{GREEN}✓ Sucesso:{RESET} {test_file}")
            if stdout:
                print(stdout)
            if stderr:
                print(f"{YELLOW}Avisos:{RESET}\n{stderr}")
            passed.append(test_file)
        else:
            print(f"{RED}✗ Falha:{RESET} {test_file}")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            failed.append(test_file)

    # Resumo final
    print(f"\n{YELLOW}==== RESUMO DOS TESTES ===={RESET}")
    print(f"{GREEN}✓ Passaram ({len(passed)}):{RESET}")
    for f in passed:
        print(f"  - {f}")

    print(f"{RED}✗ Falharam ({len(failed)}):{RESET}")
    for f in failed:
        print(f"  - {f}")

    if failed:
        sys.exit(1)
    else:
        print(f"\n{GREEN}✅ Todos os testes passaram com sucesso!{RESET}")

if __name__ == "__main__":
    main()
