import subprocess
import sys
import os
import glob

# ANSI escape codes for terminal color formatting
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def run_command(command, description):
    """
    Executes a shell command and captures its output.

    Parameters:
        command (str): The shell command to execute.
        description (str): Description of the action (not used here, but could be for logging).

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip(), e.stderr.strip()


def main():
    """
    Entry point for the SIL test runner.

    - Finds all `.sil` test files recursively under `sil_tests/`
    - Runs each test via `main.py`
    - Collects and reports passed/failed results
    - Exits with code 1 if any test fails
    """
    print(f"{YELLOW}==== RUNNING ALL SIL TESTS ===={RESET}")

    # Find all `.sil` files under sil_tests/ subdirectories
    test_files = glob.glob("sil_tests/**/*.sil", recursive=True)
    if not test_files:
        print(f"{RED}No test files found in sil_tests/**/*{RESET}")
        return

    passed = []  # List of test files that passed
    failed = []  # List of test files that failed

    # Run each test file
    for test_file in sorted(test_files):
        print(f"\n{YELLOW}>> Running test: {test_file}{RESET}")
        ok, stdout, stderr = run_command(
            f"python main.py {test_file}",
            f"Compiling and executing {os.path.basename(test_file)}",
        )

        if ok:
            print(f"{GREEN}✓ Passed:{RESET} {test_file}")
            if stdout:
                print(stdout)
            if stderr:
                print(f"{YELLOW}Warnings:{RESET}\n{stderr}")
            passed.append(test_file)
        else:
            print(f"{RED}✗ Failed:{RESET} {test_file}")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            failed.append(test_file)

    # Summary report
    print(f"\n{YELLOW}==== TEST SUMMARY ===={RESET}")
    print(f"{GREEN}✓ Passed ({len(passed)}):{RESET}")
    for f in passed:
        print(f"  - {f}")

    print(f"{RED}✗ Failed ({len(failed)}):{RESET}")
    for f in failed:
        print(f"  - {f}")

    # Exit code reflects success/failure
    if failed:
        sys.exit(1)
    else:
        print(f"\n{GREEN}✅ All tests passed successfully!{RESET}")


if __name__ == "__main__":
    main()
