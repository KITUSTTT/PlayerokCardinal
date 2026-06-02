"""Print VERSION from main.py (for release scripts)."""
import re
import sys

with open("main.py", encoding="utf-8") as f:
    text = f.read()
match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', text, re.M)
if not match:
    sys.exit(1)
print(match.group(1))
