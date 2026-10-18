import re

with open('jarvis_command_center.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_idx = html.find('<script>')
script_part = html[script_idx:] if script_idx != -1 else html

ids_in_js = set(re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]\)", script_part))
ids_in_dom = set(re.findall(r'id=["\']([^"\']+)["\']', html))

missing = []
for i in sorted(ids_in_js):
    if i not in ids_in_dom:
        missing.append(i)

print(f"Total IDs checked: {len(ids_in_js)}")
print(f"Missing IDs count: {len(missing)}")
for m in missing:
    print(f"MISSING ID: {m}")
