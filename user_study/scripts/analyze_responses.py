"""사용자 응답 분석 — Google Sheet CSV export 를 받아 참가자별 요약 + 조건별 통계.

사용법:
  python scripts/analyze_responses.py <CSV_PATH>
"""
import json, sys
from collections import defaultdict
import pandas as pd

if len(sys.argv) < 2:
    sys.exit(f"usage: python {sys.argv[0]} <responses.csv exported from your own Google Sheet>")
CSV = sys.argv[1]

df = pd.read_csv(CSV)

# 1) webhook_test 필터
df = df[df["event"] != "webhook_test"].copy()

# 2) response_submitted 중복 제거 (같은 pid+trial+q_idx 는 첫 응답만)
resp = df[df["event"] == "response_submitted"].copy()
resp = resp.drop_duplicates(subset=["pid", "trial_idx", "q_idx"], keep="first")

# 3) trial_start (wait_sec) + preference_submitted
starts = df[df["event"] == "trial_start"][["pid", "trial_idx", "condition", "ep_id", "wait_sec"]]
prefs  = df[df["event"] == "preference_submitted"][["pid", "preference"]]
done   = df[df["event"] == "session_done"]["pid"].unique()

# 4) 완주자만
complete = set(done)
print(f"\n[완주자] {len(complete)} / {df['pid'].nunique()}명")

# 5) 참가자별 요약
rows = []
for pid, g in resp.groupby("pid"):
    if pid not in complete: continue
    pref = prefs[prefs["pid"] == pid]["preference"].iloc[0] if (prefs["pid"] == pid).any() else None
    for cond in ["batched", "interleaved"]:
        gc = g[g["condition"] == cond]
        if len(gc) == 0: continue
        w = starts[(starts["pid"] == pid) & (starts["condition"] == cond)]["wait_sec"].mean()
        rows.append({
            "pid": pid,
            "condition": cond,
            "n_answered": len(gc),
            "mean_rt_sec": round(gc["response_time_sec"].mean(), 2),
            "median_rt_sec": round(gc["response_time_sec"].median(), 2),
            "n_yes": (gc["response"] == "Yes").sum(),
            "n_no":  (gc["response"] == "No").sum(),
            "n_unclear": (gc["response"] == "Unclear").sum(),
            "wait_sec": round(w, 2) if w == w else None,
            "final_pref": pref,
        })
summary = pd.DataFrame(rows)
print("\n[참가자 × 조건별 요약]")
print(summary.to_string(index=False))

# 6) 최종 선호 분포
print("\n[최종 선호 (Q1) 분포]")
pref_counts = prefs["preference"].value_counts()
print(pref_counts.to_string())
n_total = pref_counts.sum()
for k, v in pref_counts.items():
    print(f"  {k}: {v}/{n_total} ({100*v/n_total:.1f}%)")

# 7) 조건별 평균 응답 시간
print("\n[조건별 평균 응답 시간 (완주자, 중복 제거)]")
resp_c = resp[resp["pid"].isin(complete)]
for cond, g in resp_c.groupby("condition"):
    print(f"  {cond}: n={len(g)}, mean={g['response_time_sec'].mean():.2f}s, "
          f"median={g['response_time_sec'].median():.2f}s")
