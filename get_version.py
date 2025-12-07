import re
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'VERSION = "([^"]+)"', content)
    if match:
        print(match.group(1))
    else:
        print("")

