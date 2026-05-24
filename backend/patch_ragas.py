import os
import re

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find type | type patterns
    # This might catch some bitwise ORs, but in Ragas it's mostly types.
    # We look for patterns like 'Type | Type' or 'Type | None'
    new_content = re.sub(r'([a-zA-Z0-9\[\]\.]+) +\| +([a-zA-Z0-9\[\]\.]+)', r't.Union[\1, \2]', content)
    
    # Also handle multiple pipes: Type | Type | Type -> t.Union[Type, t.Union[Type, Type]]
    # (The regex above handles 2 types. We run it multiple times to handle more.)
    for _ in range(3):
        new_content = re.sub(r'([a-zA-Z0-9\[\]\.]+) +\| +([a-zA-Z0-9\[\]\.]+)', r't.Union[\1, \2]', new_content)

    if new_content != content:
        # Ensure 'typing as t' or 'import typing' is present if we use t.Union
        if 't.Union' in new_content and 'import typing as t' not in new_content:
            new_content = "import typing as t\n" + new_content
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

root_dir = r"d:\SAMI\INTERNSHIP\DRDL\rag_chatbot\backend\venv\lib\site-packages\ragas"
patched_count = 0
for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.py'):
            if patch_file(os.path.join(root, file)):
                patched_count += 1
                print(f"Patched: {os.path.join(root, file)}")

print(f"Total files patched: {patched_count}")
