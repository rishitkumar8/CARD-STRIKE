"""Crash diagnosis wrapper - runs main.py and captures ANY crash output."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "main.py"],
    capture_output=True,
    text=True,
    cwd=r"c:\Users\Public\Documents\4thsem\projects\marve-strike\marve-strike"
)

print("=== STDOUT ===")
print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
print("\n=== STDERR ===")
print(result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr)
print(f"\n=== EXIT CODE: {result.returncode} ===")
