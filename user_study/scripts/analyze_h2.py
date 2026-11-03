"""H2 실험 분석 — 5 세트 완주자 기준.

1. 두 방식별 평균 답변 소요 시간 (IQR outlier trim)
2. 두 방식별 선호 집계 (3가지 버전)
"""
import json, sys
import pandas as pd
import numpy as np

if len(sys.argv) < 2:
    sys.exit(f"usage: python {sys.argv[0]} <responses.csv exported from your own Google Sheet>")
CSV = sys.argv[1]
df = pd.read_csv(CSV)
df = df[df["experiment"] == "H2"].copy()

# --- set_idx / session_letter / preference_letter 는 raw_json 에서 파싱 ---
def _from_raw(row, key):
    try:
        return json.loads(row["raw_json"]).get(key)
    except: return None

for k in ["set_idx", "session_letter", "preference_letter", "preference_condition",
          "session_A_condition", "session_B_condition"]:
    df[k] = df.apply(lambda r: _from_raw(r, k), axis=1)

# --- 완주자 판정: session_done 이벤트가 있는 pid ---
finished_pids = set(df[df["event"] == "session_done"]["pid"].tolist())
print(f"\n=== 완주자 (session_done 있는) ===")
print(f"완주자 수: {len(finished_pids)} / 전체 pid {df['pid'].nunique()}")
for p in sorted(finished_pids): print(f"  {p}")

# --- 완주자만 필터 ---
df = df[df["pid"].isin(finished_pids)].copy()

# =========================================
# 1. 두 방식별 답변 소요 시간 (IQR trim)
# =========================================
resp = df[df["event"] == "response_submitted"].copy()
# 중복 제거 (같은 pid+set_idx+session_letter+q_idx 는 첫 응답만)
resp = resp.drop_duplicates(subset=["pid", "set_idx", "session_letter", "q_idx"], keep="first")
resp["response_time_sec"] = pd.to_numeric(resp["response_time_sec"], errors="coerce")
resp = resp.dropna(subset=["response_time_sec", "condition"])

def iqr_trim(x):
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return x[(x >= lo) & (x <= hi)]

print("\n=== 1. 두 방식별 답변 소요 시간 (완주자만, IQR trim) ===")
for cond in ["binary", "open"]:
    x = resp[resp["condition"] == cond]["response_time_sec"]
    x_trim = iqr_trim(x)
    print(f"\n  [{cond}] n={len(x)} → IQR trim n={len(x_trim)} "
          f"({len(x) - len(x_trim)} outliers 제거)")
    print(f"    full : mean={x.mean():.2f}s  median={x.median():.2f}s  "
          f"p25={x.quantile(0.25):.2f}s  p75={x.quantile(0.75):.2f}s  "
          f"max={x.max():.2f}s")
    print(f"    trim : mean={x_trim.mean():.2f}s  median={x_trim.median():.2f}s  "
          f"std={x_trim.std():.2f}s")

# 통계 유의성 (Mann-Whitney U, non-parametric)
from scipy import stats
bx = iqr_trim(resp[resp["condition"] == "binary"]["response_time_sec"])
ox = iqr_trim(resp[resp["condition"] == "open"]["response_time_sec"])
u, pval = stats.mannwhitneyu(bx, ox, alternative='less')  # binary < open
print(f"\n  Mann-Whitney U (binary < open, IQR trimmed): U={u:.0f}, p={pval:.2e}")

# =========================================
# 2. 두 방식별 선호 집계 (3 버전)
# =========================================
pref = df[df["event"] == "set_preference_submitted"].copy()
pref = pref.dropna(subset=["preference_condition", "set_idx"])
pref["set_idx"] = pref["set_idx"].astype(int)

print(f"\n\n=== 2. 두 방식별 선호 집계 (완주자만, n_pref_rows={len(pref)}) ===")

# --- 버전 A: 전체 vote 집계 (5 vote/participant × N) ---
print("\n[버전 A] 전체 vote 집계 (5 세트 × N 참가자 개별 vote)")
counts = pref["preference_condition"].value_counts()
total = counts.sum()
for c, n in counts.items():
    print(f"  {c}: {n}/{total} vote ({100*n/total:.1f}%)")

# --- 버전 B: 참가자별 다수결 → 참가자 단위 집계 ---
print("\n[버전 B] 참가자 단위 다수결 (각 참가자의 5 세트 중 다수 선호)")
per_pp = pref.groupby("pid")["preference_condition"].agg(
    lambda x: x.value_counts().idxmax()
).value_counts()
n_pp = per_pp.sum()
for c, n in per_pp.items():
    print(f"  {c}: {n}/{n_pp} 명 ({100*n/n_pp:.1f}%)")

# --- 버전 C: 참가자별 5 세트 중 각 조건 vote 수 → 평균 ---
print("\n[버전 C] 참가자별 5 세트 중 open/binary vote 수의 평균")
per_pp_counts = pref.groupby(["pid", "preference_condition"]).size().unstack(fill_value=0)
for c in ["binary", "open"]:
    if c in per_pp_counts.columns:
        mean_c = per_pp_counts[c].mean()
        std_c  = per_pp_counts[c].std()
        print(f"  {c}: 참가자당 평균 {mean_c:.2f} vote (SD {std_c:.2f}, 최대 5)")

# --- 버전 D: 세트별 (set_idx=0~4) 각 조건 선호 비율 — 학습 효과 확인 ---
print("\n[버전 D] 세트 순서별 선호 분포 (학습/피로 효과 확인)")
by_set = pref.groupby(["set_idx", "preference_condition"]).size().unstack(fill_value=0)
by_set["total"] = by_set.sum(axis=1)
for c in ["binary", "open"]:
    if c in by_set.columns:
        by_set[f"{c}_pct"] = (100 * by_set[c] / by_set["total"]).round(1)
print(by_set.to_string())

# =========================================
# 참고: response_length (open condition 만)
# =========================================
open_resp = resp[resp["condition"] == "open"].copy()
open_resp["response_length_chars"] = pd.to_numeric(open_resp["response_length_chars"], errors="coerce")
open_resp = open_resp.dropna(subset=["response_length_chars"])
if len(open_resp) > 0:
    print("\n\n=== 참고: Open 조건 응답 글자수 (완주자, 중복 제거) ===")
    lx = open_resp["response_length_chars"]
    lx_trim = iqr_trim(lx)
    print(f"  n={len(lx)} → IQR trim n={len(lx_trim)}")
    print(f"  full : mean={lx.mean():.1f} chars  median={lx.median():.1f}  max={lx.max():.0f}")
    print(f"  trim : mean={lx_trim.mean():.1f} chars  median={lx_trim.median():.1f}")
