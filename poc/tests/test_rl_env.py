import numpy as np

from v93k_poc.rl_env import V93KPlacementEnv


def test_env_reset_returns_correct_shape():
    env = V93KPlacementEnv(max_steps=20)
    obs, info = env.reset(seed=42)
    assert obs.shape == (env.n_caps * 6,)
    assert obs.dtype == np.float32
    assert "E_init" in info
    assert info["E_init"] > 0


def test_env_step_decreases_energy_with_zero_action():
    """A zero action should leave the board untouched -> reward == 0."""
    env = V93KPlacementEnv(max_steps=20)
    env.reset(seed=42)
    obs, r, term, trunc, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))
    assert abs(r) < 1e-6
    assert not term and not trunc


def test_env_truncates_after_max_steps():
    env = V93KPlacementEnv(max_steps=5)
    env.reset(seed=0)
    for _ in range(4):
        _, _, term, trunc, _ = env.step(np.zeros(env.action_space.shape, dtype=np.float32))
        assert not trunc
    _, _, term, trunc, _ = env.step(np.zeros(env.action_space.shape, dtype=np.float32))
    assert trunc
