with open(r"D:\Claude项目\order\static\js\app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find all .join('')); and fix them
# The ONLY one that needs extra ) is at line ~642 in renderAdminDishes
# Let me first check how many occurrences there are

# Replace all .join('')); with .join('');
content = content.replace(").join(''));", ").join('');")

# Now add the extra ) back at line 642 (renderAdminDishes)
lines = content.split('\n')
# Find the line in renderAdminDishes that has .join('')
for i, line in enumerate(lines):
    if 'renderAdminDishes' in line:
        # Look for .join('') in subsequent lines
        for j in range(i, min(i+30, len(lines))):
            if ").join('');" in lines[j] and "}":  # This is the closing line
                lines[j] = lines[j].replace(").join('');", ").join(''));")
                break
        break

content = '\n'.join(lines)

with open(r"D:\Claude项目\order\static\js\app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed!")
