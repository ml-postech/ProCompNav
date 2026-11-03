"""Stimulus 로드 + 참가자별 5-세트 assignment (H2)."""
import json, hashlib, random
import config


def load_pool():
    with open(config.STIMULUS_JSON, "r") as f:
        return json.load(f)


def assign_h2(pid: str, pool):
    """참가자별 5 세트 배정.

    각 세트 = 세션 A + 세션 B (같은 ep, 다른 조건).
    조건 A/B 매핑은 참가자별 고정:
      - 짝수 seed: A=binary, B=open (5 세트 모두)
      - 홀수 seed: A=open,   B=binary (5 세트 모두)

    Pool 부족 시 ep 반복 사용.

    Returns:
      list of sets: [
        {"set_idx", "ep", "session_A": {letter, condition, ep}, "session_B": {...}},
        ...
      ]
    """
    eps = pool["episodes"][:]
    seed = int(hashlib.md5(pid.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    rng.shuffle(eps)

    n_sets = config.SETS_PER_PARTICIPANT_H2
    if len(eps) == 0:
        raise ValueError("Stimulus pool is empty")
    picked_eps = (eps * n_sets)[:n_sets]

    # A/B 조건 매핑 (참가자별 고정)
    if seed % 2 == 0:
        a_cond, b_cond = "binary", "open"
    else:
        a_cond, b_cond = "open", "binary"

    sets = []
    for i, ep in enumerate(picked_eps):
        sets.append({
            "set_idx": i,
            "ep": ep,
            "session_A": {"letter": "A", "condition": a_cond, "ep": ep},
            "session_B": {"letter": "B", "condition": b_cond, "ep": ep},
        })
    return sets
