"""Stimulus 로드 + 참가자별 assignment (H1 기준)."""
import json, hashlib, random
import config


def load_pool():
    with open(config.STIMULUS_JSON, "r") as f:
        return json.load(f)


def assign_h1(pid: str, pool):
    """참가자별 H1 assignment.

    참가자 seed 로 stimulus 를 shuffle 하고, 앞 절반은 조건 A, 뒷 절반은 조건 B.
    조건 순서도 참가자 seed 로 counterbalance (짝수 번째 pid 는 A→B, 홀수는 B→A).

    Returns:
      list of trials: [{"trial_idx", "condition", "ep": <ep record>}, ...]
    """
    eps = pool["episodes"][:]
    # 참가자 seed = pid hash → reproducible
    seed = int(hashlib.md5(pid.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    rng.shuffle(eps)

    # 앞 절반 A, 뒷 절반 B
    n_trials = min(config.TRIALS_PER_PARTICIPANT_H1, len(eps))
    half = n_trials // 2
    a_eps = eps[:half]
    b_eps = eps[half:n_trials]

    # 조건 순서 counterbalance
    first_a = seed % 2 == 0
    trials = []
    if first_a:
        for e in a_eps: trials.append({"condition": "interleaved", "ep": e})
        for e in b_eps: trials.append({"condition": "batched",     "ep": e})
    else:
        for e in b_eps: trials.append({"condition": "batched",     "ep": e})
        for e in a_eps: trials.append({"condition": "interleaved", "ep": e})

    for i, t in enumerate(trials):
        t["trial_idx"] = i
    return trials
