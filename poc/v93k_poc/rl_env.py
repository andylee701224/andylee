"""Gymnasium environment for V93K cap placement.

Observation (per cap, normalised to board half-extent, in [-2, 2]):
    [x, y, target_vdd_x, target_vdd_y, nearest_keepout_dx, nearest_keepout_dy]
Stack -> shape (n_caps * 6,)

Action (per cap):
    [dx, dy] in [-1, 1], scaled by `step_mm` per environment step.
Stack -> shape (n_caps * 2,)

Reward (dense):
    r = (E_prev - E_new) / max(E_init, 1)

Episode is truncated after `max_steps` steps; never terminated early.
"""
from __future__ import annotations

from copy import deepcopy

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .p2_placement import total_energy
from .synthetic import make_toy_board, randomize_components


class V93KPlacementEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, max_steps: int = 200, step_mm: float = 1.0,
                 randomize: bool = True):
        super().__init__()
        self.max_steps = max_steps
        self.step_mm = step_mm
        self.randomize = randomize

        template = make_toy_board()
        self._template = template
        self.n_caps = len(template.components)
        self.half_w = template.width / 2
        self.half_h = template.height / 2

        self.observation_space = spaces.Box(
            low=-2.0, high=2.0, shape=(self.n_caps * 6,), dtype=np.float32)
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(self.n_caps * 2,), dtype=np.float32)

        self.board = None
        self._cap_order: list[str] = []
        self.steps = 0
        self.E_init = 1.0
        self.E_prev = 1.0

    def _build_board(self, ep_seed: int):
        board = deepcopy(self._template)
        if self.randomize:
            randomize_components(board, seed=ep_seed)
        return board

    def _obs(self) -> np.ndarray:
        b = self.board
        feats = np.empty(self.n_caps * 6, dtype=np.float32)
        for i, cid in enumerate(self._cap_order):
            c = b.components[cid]
            tgt = b.anchors[c.target_anchor_id]
            # Nearest keep-out (Manhattan).
            best_dx = best_dy = 0.0
            best_d = float("inf")
            for k in b.keepouts:
                dx = c.x - k.x
                dy = c.y - k.y
                d = abs(dx) + abs(dy)
                if d < best_d:
                    best_d = d
                    best_dx, best_dy = dx, dy
            base = i * 6
            feats[base + 0] = c.x / self.half_w
            feats[base + 1] = c.y / self.half_h
            feats[base + 2] = tgt.x / self.half_w
            feats[base + 3] = tgt.y / self.half_h
            feats[base + 4] = best_dx / self.half_w
            feats[base + 5] = best_dy / self.half_h
        return feats

    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        ep_seed = seed if seed is not None else int(self.np_random.integers(0, 2**31 - 1))
        self.board = self._build_board(ep_seed)
        self._cap_order = sorted(self.board.components.keys())
        self.steps = 0
        self.E_init = float(total_energy(self.board))
        self.E_prev = self.E_init
        return self._obs(), {"E_init": self.E_init}

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).reshape(self.n_caps, 2)
        for i, cid in enumerate(self._cap_order):
            c = self.board.components[cid]
            c.x = float(np.clip(c.x + action[i, 0] * self.step_mm,
                                -self.half_w, self.half_w))
            c.y = float(np.clip(c.y + action[i, 1] * self.step_mm,
                                -self.half_h, self.half_h))
        self.steps += 1
        E_new = float(total_energy(self.board))
        reward = (self.E_prev - E_new) / max(self.E_init, 1.0)
        self.E_prev = E_new
        truncated = self.steps >= self.max_steps
        info = {"energy": E_new}
        return self._obs(), float(reward), False, truncated, info
