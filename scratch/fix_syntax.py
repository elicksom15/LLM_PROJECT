path = r"E:\AI_MODELS\PROXY-REVERSA\auto_refill.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'acc.send_keys("' in line and i + 1 < len(lines) and '")' in lines[i+1]:
        new_lines.append('                acc.send_keys("\\n")\n')
        i += 2
        continue
    if 'pw.send_keys("' in line and i + 1 < len(lines) and '")' in lines[i+1]:
        new_lines.append('            pw.send_keys("\\n")\n')
        i += 2
        continue
    new_lines.append(line)
    i += 1

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Fixed syntax cleanly!")
