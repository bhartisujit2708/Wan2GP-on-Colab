---
name: update-colab-notebook
description: Safely edit and maintain wan2gp-google-colab.ipynb — bumping PyTorch/CUDA/xformers pins, adding Wan2GP data directories (checkpoints, LoRA folders), patching upstream Wan2GP files, changing launch flags, or fixing breakage from Colab runtime or upstream Wan2GP changes. Use whenever a task touches the notebook or the README's notebook workflow section.
---

# Updating the Wan2GP Colab notebook

This repo is a single notebook (`wan2gp-google-colab.ipynb`) plus a `README.md` that documents it. Users open it straight from GitHub via the Colab badge, so a broken `main` breaks everyone immediately.

## Notebook layout

| Cell | Step | What it owns |
|------|------|--------------|
| 0 | Intro (markdown) | VRAM note for free-tier T4 |
| 1–2 | 1. Confirm accelerator | `nvidia-smi` check |
| 3–4 | 2. Workspace / storage | `USE_GOOGLE_DRIVE_DATA`, `WAN2GP_ROOT`, `WAN_DATA_ROOT` and every `WAN_*_DIR` path; creates dirs |
| 5–6 | 3. Download or update Wan2GP | clone/pull, `attach_data_directory()` symlinks `ckpts`, `loras`, `outputs` into the data root |
| 7–8 | 4. System deps | `apt-get install` list |
| 9–10 | 5. Python deps | `TORCH_VERSION`, `TORCHVISION_VERSION`, `TORCHAUDIO_VERSION`, `PYTORCH_INDEX_URL`, xformers pin, `requirements.txt`, version check |
| 11–12 | 5b. Headless matplotlib | idempotent text patch of upstream `interact_tools.py` |
| 13–14 | 6. Launch | cache env vars, `wgp.py` flags, keepalive thread |

Cell indices drift — always locate cells by content, not index.

## How to edit

1. **Edit the JSON programmatically**, never by hand-splicing strings. Load with `json`, change the target cell's `source` (a list of lines, each ending in `\n` except the last), and dump with `indent=1` and `ensure_ascii=False` to match the existing formatting:
   ```python
   import json
   p = 'wan2gp-google-colab.ipynb'
   nb = json.load(open(p))
   cell = next(c for c in nb['cells'] if "TORCH_VERSION = " in ''.join(c['source']))
   src = ''.join(cell['source']).replace("TORCH_VERSION = '2.8.0'", "TORCH_VERSION = '2.9.0'")
   cell['source'] = src.splitlines(keepends=True)
   with open(p, 'w', encoding='utf-8') as f:
       json.dump(nb, f, indent=1, ensure_ascii=False)
       f.write('\n')
   ```
   Check `git diff` afterwards — it should show only the lines you meant to change. If whitespace churns across the whole file, match the original's indent/trailing-newline style instead.
2. **Keep code cells output-free**: `outputs: []`, `execution_count: null`. Never commit Colab outputs (they leak paths, tokens, Gradio share links).
3. **Run the validator** before committing:
   ```bash
   python3 .claude/skills/update-colab-notebook/scripts/validate_notebook.py
   ```
   It checks JSON/nbformat structure, empty outputs, that every code cell compiles, and that the README step list matches the notebook's step headings.

## Conventions to preserve

- **Re-runnable cells.** Users rerun from the top after a runtime reset or Drive remount. Every cell must be idempotent: `mkdir(..., exist_ok=True)`, skip `git pull` when the checkout has local changes, check for an existing symlink before creating one, and make text patches no-ops when already applied (see Step 5b).
- **Paths live in Step 2.** A new data directory (e.g. a new model family's LoRA folder like `WAN_LTX2_LORAS_DIR`) gets a `WAN_*_DIR` constant, a `mkdir`, and a `print` there. If Wan2GP expects it inside the repo, link it in Step 3 with `attach_data_directory()` — never write data into `/content/Wan2GP` directly, or it is lost on reset and blocks `git pull`.
- **Caches go through env vars in Step 6** (`HF_HOME`, `TORCH_HOME`, `XDG_CACHE_HOME`, …) so Drive mode persists them.
- **Pinned torch stack.** torch/torchvision/torchaudio must be a matching triple from the same `PYTORCH_INDEX_URL` (CUDA tag), and the xformers pin must be built for that torch version. Update all of them together and keep the post-install mismatch check.
- **Fail loudly with a fix.** Raise `RuntimeError` with a message that tells the user what to click or rerun (see Steps 1 and 5).
- **Use `subprocess.run([...], check=True)`** with list args, not `!shell` magics, so cells stay valid Python.
- **Free-tier guidance.** If a change affects VRAM use or the recommended model, update the VRAM note in cell 0 and the warning in the README.

## Keep README in sync

`README.md` → "Notebook workflow" is a numbered list mirroring the notebook's `## N.` headings. Adding, removing, renaming or reordering a step means updating that list in the same commit. Sub-steps like `5b` are not listed separately.

## Before pushing

- Validator passes.
- `git diff` reviewed: only intended lines changed, no outputs added.
- If you changed pins, apt packages or launch flags, say in the commit/PR that it has not been run on a live Colab GPU runtime unless it actually was — this container cannot run Colab.
