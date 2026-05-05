"""Head-to-head SA vs PPO comparison on the V93K toy board.

Trains a PPO policy from scratch on V93KPlacementEnv, then evaluates both SA
and PPO on the same 10 random seeds. Reports per-seed and aggregate metrics
after P3 legalisation, plus wall-clock time.

Run from the `poc/` directory:

    python -m examples.compare_sa_rl
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from v93k_poc.metrics import (
    cap_to_vdd_distance,
    drc_violations,
    site_symmetry_error,
    total_wirelength,
)
from v93k_poc.p1_mapping import solve_channel_mapping
from v93k_poc.p2_placement import simulated_annealing
from v93k_poc.p3_legalize import legalize
from v93k_poc.rl_env import V93KPlacementEnv
from v93k_poc.synthetic import make_toy_board, randomize_components


EVAL_SEEDS = list(range(1000, 1010))
ARTIFACTS = os.path.join(_ROOT, "artifacts")
os.makedirs(ARTIFACTS, exist_ok=True)


def metrics_after_legalize(board) -> dict:
    legalize(board)
    mapping, _ = solve_channel_mapping(board)
    nv, _ = drc_violations(board)
    sym = site_symmetry_error(board)
    mean_d, max_d = cap_to_vdd_distance(board)
    wl = total_wirelength(board, mapping)
    return dict(drc=nv, sym=sym, cap_vdd_mean=mean_d,
                cap_vdd_max=max_d, wl=wl)


def run_sa(seed: int, iters: int = 12000):
    b = make_toy_board()
    randomize_components(b, seed=seed)
    t0 = time.perf_counter()
    res = simulated_annealing(b, iters=iters, seed=seed)
    elapsed = time.perf_counter() - t0
    return res.board, elapsed, res.energy


def run_rl(model: PPO, seed: int, max_steps: int = 200):
    env = V93KPlacementEnv(max_steps=max_steps)
    obs, _ = env.reset(seed=seed)
    t0 = time.perf_counter()
    truncated = False
    while not truncated:
        action, _ = model.predict(obs, deterministic=True)
        obs, r, terminated, truncated, info = env.step(action)
    elapsed = time.perf_counter() - t0
    return env.board, elapsed, env.E_prev


def train_ppo(total_timesteps: int = 60_000, seed: int = 0):
    env = DummyVecEnv([lambda: V93KPlacementEnv(max_steps=200)])
    model = PPO(
        "MlpPolicy", env, verbose=0, seed=seed,
        learning_rate=3e-4, n_steps=2048, batch_size=64,
        gamma=0.98, n_epochs=10, ent_coef=0.0,
    )
    t0 = time.perf_counter()
    model.learn(total_timesteps=total_timesteps)
    return model, time.perf_counter() - t0


class _Tee:
    """Write to stdout AND a file simultaneously."""
    def __init__(self, *streams):
        self._streams = streams

    def write(self, s):
        for st in self._streams:
            st.write(s)

    def flush(self):
        for st in self._streams:
            st.flush()


def main():
    log_path = os.path.join(ARTIFACTS, "sa_vs_rl_results.txt")
    log_file = open(log_path, "w")
    sys.stdout = _Tee(sys.__stdout__, log_file)

    print("=" * 96)
    print("V93K toy placement: SA vs PPO head-to-head")
    print("=" * 96)

    print(f"\n[Train] PPO ({60_000} timesteps) ...")
    model, train_t = train_ppo(total_timesteps=60_000, seed=0)
    print(f"        done in {train_t:.1f}s")

    rows = []
    print("\nPer-seed evaluation (after P3 legalisation):")
    header = (f"{'seed':>5} | {'SA E':>7} {'RL E':>7} | {'SA t':>6} {'RL t':>6} | "
              f"{'SA WL':>6} {'RL WL':>6} | {'SA DRC':>6} {'RL DRC':>6} | "
              f"{'SA sym':>7} {'RL sym':>7} | {'SA capD':>7} {'RL capD':>7}")
    print(header)
    print("-" * len(header))
    for seed in EVAL_SEEDS:
        sa_board, sa_t, sa_E = run_sa(seed)
        rl_board, rl_t, rl_E = run_rl(model, seed)
        sa_post = metrics_after_legalize(sa_board)
        rl_post = metrics_after_legalize(rl_board)
        rows.append(dict(seed=seed,
                         sa_E=sa_E, rl_E=rl_E,
                         sa_t=sa_t, rl_t=rl_t,
                         sa_post=sa_post, rl_post=rl_post))
        print(f"{seed:>5} | {sa_E:7.2f} {rl_E:7.2f} | "
              f"{sa_t:6.2f} {rl_t:6.2f} | "
              f"{sa_post['wl']:6.1f} {rl_post['wl']:6.1f} | "
              f"{sa_post['drc']:6d} {rl_post['drc']:6d} | "
              f"{sa_post['sym']:7.2f} {rl_post['sym']:7.2f} | "
              f"{sa_post['cap_vdd_mean']:7.2f} {rl_post['cap_vdd_mean']:7.2f}")

    def agg(getter):
        return np.mean([getter(r) for r in rows])

    print("\n" + "=" * 96)
    print("Aggregate (mean over 10 seeds):")
    print(f"  SA : E={agg(lambda r: r['sa_E']):7.2f}  "
          f"t={agg(lambda r: r['sa_t']):5.2f}s  "
          f"WL={agg(lambda r: r['sa_post']['wl']):6.1f}mm  "
          f"DRC={agg(lambda r: r['sa_post']['drc']):4.2f}  "
          f"sym={agg(lambda r: r['sa_post']['sym']):5.2f}mm  "
          f"capD={agg(lambda r: r['sa_post']['cap_vdd_mean']):5.2f}mm")
    print(f"  RL : E={agg(lambda r: r['rl_E']):7.2f}  "
          f"t={agg(lambda r: r['rl_t']):5.2f}s  "
          f"WL={agg(lambda r: r['rl_post']['wl']):6.1f}mm  "
          f"DRC={agg(lambda r: r['rl_post']['drc']):4.2f}  "
          f"sym={agg(lambda r: r['rl_post']['sym']):5.2f}mm  "
          f"capD={agg(lambda r: r['rl_post']['cap_vdd_mean']):5.2f}mm")
    print(f"  PPO training one-off cost: {train_t:.1f}s")
    print("=" * 96)

    # Persist the trained policy.
    model.save(os.path.join(ARTIFACTS, "ppo_v93k_policy.zip"))
    print(f"\nSaved PPO policy -> {ARTIFACTS}/ppo_v93k_policy.zip")
    print(f"Saved log         -> {log_path}")
    sys.stdout = sys.__stdout__
    log_file.close()


if __name__ == "__main__":
    main()
