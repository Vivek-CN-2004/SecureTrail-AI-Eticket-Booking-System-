f = open('frontend/index.html', encoding='utf-8').read()
lines = f.split('\n')
found = False
for i, l in enumerate(lines):
    if 'monospace' in l and 'fontFamily' not in l and 'font-family' not in l:
        print(f"Line {i+1}: {l[:150]}")
        found = True
    if '0.1)}' in l:
        print(f"Line {i+1} MISSING QUOTE: {l[:150]}")
        found = True
if not found:
    print("No obvious corruption found.")
