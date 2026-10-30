"""
Build executed Jupyter notebooks from the percent-format sources in notebooks/src/*.py.

Each source file uses the Jupytext "percent" convention:
    # %% [markdown]          <- markdown cell (each line starts with "# ")
    # %%                     <- code cell
The script runs every code cell in order (one shared namespace per notebook, working
directory = notebooks/), captures printed output, the value of a trailing expression and
any matplotlib figures, and writes a standard .ipynb (nbformat v4) with outputs embedded.

You can also open the generated .ipynb files in Jupyter/VS Code and re-run them normally.

Usage:  python tools/build_notebooks.py            # all notebooks
        python tools/build_notebooks.py 03_eda     # one notebook
"""
import ast
import base64
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
SRC_DIR = NB_DIR / "src"


def parse_cells(text):
    cells, cur, kind = [], [], None
    for line in text.splitlines():
        if line.startswith("# %%"):
            if kind is not None:
                cells.append((kind, cur))
            kind = "markdown" if "[markdown]" in line else "code"
            cur = []
        elif kind is not None:
            cur.append(line)
    if kind is not None:
        cells.append((kind, cur))
    out = []
    for kind, lines in cells:
        while lines and not lines[-1].strip():
            lines.pop()
        while lines and not lines[0].strip():
            lines.pop(0)
        if kind == "markdown":
            lines = [l[2:] if l.startswith("# ") else l.lstrip("#") for l in lines]
        if lines:
            out.append((kind, "\n".join(lines)))
    return out


def rich_repr(value):
    data = {"text/plain": [repr(value)]}
    if hasattr(value, "to_html"):
        try:
            data["text/html"] = [value.to_html(max_rows=25, max_cols=20)]
        except TypeError:
            data["text/html"] = [value.to_html()]
    if hasattr(value, "_repr_html_") and "text/html" not in data:
        h = value._repr_html_()
        if h:
            data["text/html"] = [h]
    return data


def run_cell(code, ns, count):
    outputs = []
    buf = io.StringIO()
    tree = ast.parse(code)
    last_expr = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last_expr = ast.Expression(tree.body.pop().value)
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(tree, f"<cell {count}>", "exec"), ns)
            value = eval(compile(last_expr, f"<cell {count}>", "eval"), ns) if last_expr else None
    except Exception:
        sys.stderr.write(buf.getvalue())
        raise RuntimeError(f"cell {count} failed:\n{code}\n\n{traceback.format_exc()}")
    if buf.getvalue():
        outputs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue().splitlines(True)})
    for num in plt.get_fignums():
        fig = plt.figure(num)
        b = io.BytesIO()
        fig.savefig(b, format="png", bbox_inches="tight")
        outputs.append({"output_type": "display_data", "metadata": {},
                        "data": {"image/png": base64.b64encode(b.getvalue()).decode(),
                                 "text/plain": ["<Figure>"]}})
    plt.close("all")
    if value is not None and not isinstance(value, matplotlib.figure.Figure) and \
            not (isinstance(value, list) and value and hasattr(value[0], "figure")) and \
            not hasattr(value, "figure"):
        outputs.append({"output_type": "execute_result", "execution_count": count,
                        "metadata": {}, "data": rich_repr(value)})
    return outputs


def build(src_path):
    cells = parse_cells(src_path.read_text())
    ns = {"__name__": "__main__"}
    cwd = os.getcwd()
    os.chdir(NB_DIR)
    sys.path.insert(0, str(ROOT / "src"))
    nb_cells, count = [], 0
    try:
        for kind, text in cells:
            src_lines = text.splitlines(True)
            if kind == "markdown":
                nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": src_lines})
                continue
            count += 1
            outs = run_cell(text, ns, count)
            nb_cells.append({"cell_type": "code", "execution_count": count, "metadata": {},
                             "outputs": outs, "source": src_lines})
    finally:
        os.chdir(cwd)
    nb = {"cells": nb_cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0]}},
        "nbformat": 4, "nbformat_minor": 5}
    out = NB_DIR / (src_path.stem + ".ipynb")
    out.write_text(json.dumps(nb, indent=1))
    print(f"built {out.relative_to(ROOT)}  ({count} code cells)")


if __name__ == "__main__":
    wanted = sys.argv[1:]
    for p in sorted(SRC_DIR.glob("*.py")):
        if not wanted or any(w in p.stem for w in wanted):
            build(p)
