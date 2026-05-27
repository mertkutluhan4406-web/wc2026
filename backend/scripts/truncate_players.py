"""
Find ALL bulk import markers and remove everything after the FIRST occurrence.
"""
PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

print("Reading...")
with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# The original file ends with the PLAYERS_DB conversion line
# Let's find that anchor
anchor = "PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}"
idx = content.find(anchor)
if idx != -1:
    # Keep everything up to and including this line plus a newline
    end_of_line = content.index("\n", idx) + 1
    clean = content[:end_of_line] + "\n"
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        f.write(clean)
    line_count = clean.count("\n")
    print(f"Truncated to {line_count} lines ({len(clean)} bytes)")
else:
    print("Anchor not found!")

# Verify
with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
    final = f.read()
try:
    compile(final, PLAYERS_FILE, "exec")
    print("Syntax OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
