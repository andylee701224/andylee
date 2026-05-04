"""Matplotlib visualisation for the toy board."""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from .board import Board, SignalType


SIGNAL_COLORS = {
    SignalType.HIGH_SPEED: "#d62728",
    SignalType.LOW_SPEED: "#1f77b4",
    SignalType.VDD: "#ff7f0e",
    SignalType.GND: "#2ca02c",
}


def plot_board(board: Board,
               mapping: dict[str, str] | None = None,
               title: str = "V93K toy board",
               save_path: str | None = None,
               show_mapping_wires: bool = True):
    fig, ax = plt.subplots(figsize=(11, 8))

    # Board outline.
    ax.add_patch(mpatches.Rectangle(
        (-board.width / 2, -board.height / 2),
        board.width, board.height,
        fill=False, edgecolor="black", linewidth=2,
    ))

    # Keep-out zones (sockets).
    for k in board.keepouts:
        ax.add_patch(mpatches.Rectangle(
            (k.x - k.width / 2, k.y - k.height / 2),
            k.width, k.height,
            facecolor="#cccccc", edgecolor="#666666",
            linewidth=0.8, linestyle="--", alpha=0.5, zorder=0,
        ))

    # Mapping wires.
    if mapping and show_mapping_wires:
        for cid, pid in mapping.items():
            ca = board.anchors[cid]
            pa = board.anchors[pid]
            color = SIGNAL_COLORS.get(ca.signal_type, "gray")
            ax.plot([ca.x, pa.x], [ca.y, pa.y],
                    color=color, linewidth=0.5, alpha=0.35, zorder=1)

    # Cap-to-target lines.
    for c in board.components.values():
        a = board.anchors[c.target_anchor_id]
        ax.plot([c.x, a.x], [c.y, a.y],
                color="#ff7f0e", linewidth=0.8, alpha=0.7, zorder=2)

    # Anchors.
    for a in board.anchors.values():
        color = SIGNAL_COLORS.get(a.signal_type, "gray")
        marker = "s" if a.role == "v93k" else "o"
        ax.scatter(a.x, a.y, c=color, marker=marker, s=42,
                   edgecolors="black", linewidths=0.5, zorder=3)

    # Components.
    for c in board.components.values():
        ax.add_patch(mpatches.Rectangle(
            (c.x - c.width / 2, c.y - c.height / 2),
            c.width, c.height,
            facecolor="#444444", edgecolor="black", linewidth=0.6, zorder=4,
        ))
        ax.text(c.x, c.y + c.height / 2 + 0.5, c.id.replace("cap_", ""),
                fontsize=5, ha="center", va="bottom", zorder=5)

    ax.set_xlim(-board.width / 2 - 5, board.width / 2 + 5)
    ax.set_ylim(-board.height / 2 - 5, board.height / 2 + 5)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    legend_elements = [
        mpatches.Patch(color=SIGNAL_COLORS[SignalType.HIGH_SPEED], label="High speed"),
        mpatches.Patch(color=SIGNAL_COLORS[SignalType.LOW_SPEED], label="Low speed"),
        mpatches.Patch(color=SIGNAL_COLORS[SignalType.VDD], label="VDD"),
        mpatches.Patch(color=SIGNAL_COLORS[SignalType.GND], label="GND"),
        mpatches.Patch(color="#444444", label="Decoupling cap"),
        mpatches.Patch(color="#cccccc", label="Socket keep-out"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
    return fig, ax


def plot_sa_history(history, save_path: str | None = None):
    if not history:
        return None
    ks = [h[0] for h in history]
    cur = [h[2] for h in history]
    best = [h[3] for h in history]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(ks, cur, label="current", color="#1f77b4", alpha=0.5, linewidth=0.8)
    ax.plot(ks, best, label="best", color="#d62728", linewidth=1.4)
    ax.set_xlabel("iteration")
    ax.set_ylabel("energy")
    ax.set_title("Simulated annealing energy")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
    return fig
