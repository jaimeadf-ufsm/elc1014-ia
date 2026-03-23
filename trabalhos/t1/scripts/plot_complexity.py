"""
plot_complexity.py
==================
Gera dois plots de complexidade:
  - Complexidade por N: memória e tempo × N, com K fixo (linhas)
  - Complexidade por K: memória e tempo × K, com N fixo (linhas)

Uso:
    python plot_complexity.py [--dir experiments] [--out plots]
                              [--fixed-ks 2 3 4 5 6]
                              [--fixed-ns 3 5 8 12]
                              [--dedup 1]
"""

import re
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Estilo ────────────────────────────────────────────────────────────────────

BG      = "#ffffff"
SURFACE = "#fdfdfd"
GRID    = "#d4d4d4"
FG      = "#161717"
MUTED   = "#393a3b"
PALETTE = ["#58a6ff", "#f78166", "#3fb950", "#d2a8ff",
           "#ffa657", "#79c0ff", "#ff7b72", "#56d364"]

plt.rcParams.update({
    "figure.facecolor":  BG,   "axes.facecolor":    SURFACE,
    "axes.edgecolor":    GRID, "axes.labelcolor":   FG,
    "axes.titlecolor":   FG,   "xtick.color":       MUTED,
    "ytick.color":       MUTED,"grid.color":        GRID,
    "grid.linestyle":    "--", "grid.alpha":        0.5,
    "text.color":        FG,   "legend.facecolor":  SURFACE,
    "legend.edgecolor":  GRID, "legend.labelcolor": FG,
    "font.family":       "DejaVu Sans",
    "font.size":         11,   "axes.titlesize":    12,
    "axes.labelsize":    11,   "figure.dpi":        150,
})

# ── Parser ────────────────────────────────────────────────────────────────────

def parse_file(path: Path):
    text = path.read_text()

    m = re.search(r"n:\s*(\d+),\s*k:\s*(\d+),\s*deduplicate:\s*(\d+)", text)
    if not m:
        return None

    result = {
        "n": int(m.group(1)),
        "k": int(m.group(2)),
        "d": int(m.group(3)),
    }

    row_pat = re.compile(
        r"depth:\s*\d+.*?memory usage:\s*(\d+).*?time elapsed:\s*(\d+)"
    )
    memories = [int(x) for x, _ in row_pat.findall(text)]
    times    = [int(x) for _, x in row_pat.findall(text)]

    if not memories:
        return None

    result["peak_memory_mb"] = max(memories) / 1_048_576   # bytes → MB
    result["total_time_s"]   = max(times)    / 1_000_000_000  # ns → s

    sol = re.search(r"solution:\s*(.+)", text)
    result["solution"] = sol.group(1).strip() if sol else None

    return result


def load(exp_dir: str, dedup: int):
    data = {}
    pat = re.compile(r"n(\d+)_k(\d+)_d([01])\.txt$")
    for f in sorted(Path(exp_dir).glob("*.txt")):
        m = pat.match(f.name)
        if not m:
            continue
        n, k, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if d != dedup:
            continue
        r = parse_file(f)
        if r:
            data[(n, k)] = r
    print(f"  {len(data)} experimentos carregados (dedup={dedup}).")
    return data

# ── Helpers ───────────────────────────────────────────────────────────────────

def save(fig, path: Path, name: str):
    p = path / name
    fig.savefig(p, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  → {p}")


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, pad=8, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9)


def mb_fmt():
    return mticker.FuncFormatter(lambda x, _: f"{x:.0f} MB" if x >= 1 else f"{x*1024:.0f} KB")

def s_fmt():
    return mticker.FuncFormatter(lambda x, _: f"{x:.2f}s" if x >= 0.01 else f"{x*1000:.1f}ms")

# ── Plot A — Complexidade por N (K fixo) ──────────────────────────────────────

def plot_complexity_by_n(data: dict, out: Path, fixed_ks: list, n_max: int = 256):
    print("\n[Plot A] Complexidade por N")

    def make_plot(suffix, n_max):
        fig, (ax_mem, ax_time) = plt.subplots(1, 2, figsize=(14, 5))
        title = "Complexidade por N  (K fixo, com dedup)"
        if n_max:
            title += f"  —  N ≤ {n_max}"
        fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)

        for i, k in enumerate(fixed_ks):
            pts = sorted(
                [(n, d["peak_memory_mb"], d["total_time_s"])
                 for (n, kk), d in data.items()
                 if kk == k and (n_max is None or n <= n_max)],
                key=lambda x: x[0]
            )
            if not pts:
                continue
            ns, mems, times = zip(*pts)
            kw = dict(marker="o", markersize=5, linewidth=2,
                      color=PALETTE[i % len(PALETTE)], label=f"K = {k}")
            ax_mem.plot(ns, mems, **kw)
            ax_time.plot(ns, times, **kw)

        style(ax_mem,  "Memória de pico × N",  "N", "Memória de pico")
        style(ax_time, "Tempo de execução × N", "N", "Tempo")
        ax_mem.set_yscale("log")
        ax_mem.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x*1024:.0f} KB" if x < 1 else f"{x:.1f} MB")
        )
        fig.tight_layout()
        save(fig, out, f"complexidade_por_n{suffix}.png")

    make_plot("",       n_max=None)   # todos os N
    make_plot("_0_256", n_max=256)    # só N ≤ 256


# ── Plot B — Complexidade por K (N fixo) ──────────────────────────────────────

def plot_complexity_by_k(data: dict, out: Path, fixed_ns: list):
    print("[Plot B] Complexidade por K")

    fig, (ax_mem, ax_time) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Complexidade por K  (N fixo, com dedup)",
                 fontsize=14, fontweight="bold", y=1.02)

    for i, n in enumerate(fixed_ns):
        pts = sorted(
            [(k, d["peak_memory_mb"], d["total_time_s"])
             for (nn, k), d in data.items() if nn == n],
            key=lambda x: x[0]
        )
        if not pts:
            continue
        ks, mems, times = zip(*pts)
        kw = dict(marker="s", markersize=5, linewidth=2,
                  color=PALETTE[i % len(PALETTE)], label=f"N = {n}")
        ax_mem.plot(ks, mems, **kw)
        ax_time.plot(ks, times, **kw)

    style(ax_mem,  "Memória de pico × K",        "K", "Memória de pico")
    style(ax_time, "Tempo de execução × K",       "K", "Tempo")
    ax_mem.yaxis.set_major_formatter(mb_fmt())
    ax_time.yaxis.set_major_formatter(s_fmt())

    fig.tight_layout()
    save(fig, out, "complexidade_por_k.png")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir",       default="experiments")
    p.add_argument("--out",       default="plots")
    p.add_argument("--dedup",     type=int, default=1,
                   help="0 ou 1 (padrão: 1)")
    p.add_argument("--fixed-ks",  type=int, nargs="+", default=[2, 4, 8, 16, 32],
                   help="K fixos para o plot por N")
    p.add_argument("--fixed-ns",  type=int, nargs="+", default=[8388608, 4194304, 2097152, 1048576],
                   help="N fixos para o plot por K")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Carregando '{args.dir}' …")
    data = load(args.dir, args.dedup)

    plot_complexity_by_n(data, out, args.fixed_ks)
    plot_complexity_by_k(data, out, args.fixed_ns)

    print("\nPronto!")


if __name__ == "__main__":
    main()
