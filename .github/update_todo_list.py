import re
from pathlib import Path

README = Path("README.md")
TARGETS = [
    "luffy/deepscaler/utils.py",
    "luffy/verl/verl/protocol.py",
]
EXPECTED_COUNTS = {
    "luffy/deepscaler/utils.py": 11,
    "luffy/verl/verl/protocol.py": 7,
}

TODO_RE = re.compile(r"\bTODO\b\s*:?\s*(.*)$")
BULLET_RE = re.compile(r"^- \[ \] \*\*(.+?):(\d+)\*\* - (.*)$")


def extract_todos(path: str):
    path_obj = Path(path)
    if not path_obj.exists():
        raise SystemExit(f"Target file does not exist: {path}")
    entries = []
    lines = path_obj.read_text(encoding="utf-8").splitlines()
    for line_no, line in enumerate(lines, start=1):
        todo_pos = line.find("TODO")
        comment_pos = line.find("#")
        if todo_pos < 0 or comment_pos < 0 or comment_pos >= todo_pos:
            continue
        match = TODO_RE.search(line[comment_pos:])
        if not match:
            continue
        message = match.group(1).strip()
        entries.append((line_no, message))
    return entries


generated = {}
for target in TARGETS:
    todos = extract_todos(target)
    if not todos:
        raise SystemExit(f"No TODO entries extracted from {target}")
    generated[target] = todos
    print(f"{target}: {len(todos)} TODOs")
    for line_no, message in todos:
        print(f"  {line_no}: {message}")

counts = {path: len(entries) for path, entries in generated.items()}
if counts != EXPECTED_COUNTS:
    raise SystemExit(f"Unexpected extracted counts: {counts!r}; expected {EXPECTED_COUNTS!r}")

readme_text = README.read_text(encoding="utf-8")
readme_lines = readme_text.splitlines()

title_index = None
for index, line in enumerate(readme_lines):
    if line.lstrip().startswith("###") and "Complete TODO List" in line:
        title_index = index
        break
if title_index is None:
    raise SystemExit("Could not find the Complete TODO List section title.")

section_end = len(readme_lines)
for index in range(title_index + 1, len(readme_lines)):
    if readme_lines[index].startswith("## "):
        section_end = index
        break

prefix = readme_lines[: title_index + 1]
suffix = readme_lines[section_end:]
section_lines = readme_lines[title_index + 1: section_end]

kept_entries = []
for line in section_lines:
    match = BULLET_RE.match(line)
    if not match:
        continue
    path = match.group(1)
    if path in generated:
        continue
    line_no = int(match.group(2))
    kept_entries.append((path, line_no, line))

for path, todos in generated.items():
    for line_no, message in todos:
        bullet = f"- [ ] **{path}:{line_no}** - {message}"
        kept_entries.append((path, line_no, bullet))

kept_entries.sort(key=lambda item: (item[0], item[1]))

bullet_lines = [item[2] for item in kept_entries]
new_lines = list(prefix)
new_lines.append("")
new_lines.extend(bullet_lines)
new_lines.append("")
new_lines.extend(suffix)

new_text = "\n".join(new_lines)
if readme_text.endswith("\n"):
    new_text += "\n"

if new_text == readme_text:
    print("README already up to date; no changes written.")
else:
    README.write_text(new_text, encoding="utf-8")
    print(f"README updated with {len(bullet_lines)} complete TODO entries.")
