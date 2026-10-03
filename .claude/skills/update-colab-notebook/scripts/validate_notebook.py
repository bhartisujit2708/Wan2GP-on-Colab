#!/usr/bin/env python3
"""Sanity-check wan2gp-google-colab.ipynb and its README before committing."""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NOTEBOOK = ROOT / 'wan2gp-google-colab.ipynb'
README = ROOT / 'README.md'

errors = []

try:
    nb = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
except (OSError, json.JSONDecodeError) as exc:
    sys.exit(f'FAIL: cannot load {NOTEBOOK.name}: {exc}')

if nb.get('nbformat') != 4:
    errors.append(f"nbformat is {nb.get('nbformat')!r}, expected 4")
if nb.get('metadata', {}).get('accelerator') != 'GPU':
    errors.append("metadata.accelerator should be 'GPU'")

step_headings = []
for i, cell in enumerate(nb.get('cells', [])):
    if not isinstance(cell.get('source'), list):
        errors.append(f'cell {i}: source must be a list of lines')
        continue
    src = ''.join(cell['source'])
    if cell['cell_type'] == 'code':
        if cell.get('outputs'):
            errors.append(f'cell {i}: has outputs; clear them before committing')
        if cell.get('execution_count') is not None:
            errors.append(f'cell {i}: execution_count should be null')
        if re.search(r'^\s*[!%]', src, re.M):
            errors.append(f'cell {i}: uses shell/magic lines; use subprocess.run instead')
        try:
            ast.parse(src)
        except SyntaxError as exc:
            errors.append(f'cell {i}: syntax error line {exc.lineno}: {exc.msg}')
    elif cell['cell_type'] == 'markdown':
        m = re.match(r'##\s+(\d+)\.\s', src)
        if m:
            step_headings.append(int(m.group(1)))

expected = list(range(1, len(step_headings) + 1))
if step_headings != expected:
    errors.append(f'notebook step headings are {step_headings}, expected {expected}')

readme = README.read_text(encoding='utf-8')
section = re.search(r'## Notebook workflow\n(.*?)(?=\n## |\Z)', readme, re.S)
if not section:
    errors.append('README is missing the "## Notebook workflow" section')
else:
    readme_steps = len(re.findall(r'^\d+\.\s', section.group(1), re.M))
    if readme_steps != len(step_headings):
        errors.append(
            f'README lists {readme_steps} workflow steps but notebook has {len(step_headings)}'
        )

if errors:
    print('FAIL')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
print(f'OK: {len(nb["cells"])} cells, {len(step_headings)} steps, README in sync')
