import subprocess
import sys

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def run_command(command, description):
    print(f"{YELLOW}== {description} =={RESET}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(f"{YELLOW}Warnings:{RESET}\n{result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}ERROR during {description}:{RESET}")
        if e.stdout.strip():
            print(e.stdout.strip())
        if e.stderr.strip():
            print(e.stderr.strip())
        sys.exit(1)

def main():
    print(f"{YELLOW}==== TESTING SIL COMPILER PIPELINE ===={RESET}")

    # Step 1: Run your compiler (main.py must output 'output.spvasm')
    run_command("python main.py", "Running your SIL compiler (main.py)")

    # Step 2: Assemble .spvasm into .spv
    run_command("spirv-as output.spvasm -o output.spv", "Assembling SPIR-V binary (spirv-as)")

    # Step 3: Validate .spv
    run_command("spirv-val output.spv", "Validating SPIR-V binary (spirv-val)")

    print(f"\n{GREEN}✅ All steps completed successfully!{RESET}")

if __name__ == "__main__":
    main()
