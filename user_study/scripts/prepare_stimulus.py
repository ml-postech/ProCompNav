"""Prepare stimulus pool for H1 experiment.

Reads Ours val_seen logs, filters to episodes with Q>=2 (so cadence has room),
stratifies by Q count (Q=2, Q=3, Q=4+), samples 20 episodes total.

For each episode collects:
  - ep_id, category
  - target_image_path (absolute path)
  - binary questions in order (property text + GT user answer from log)
  - Pooled equivalent (open-ended questions), if the Pooled log has this ep

Outputs:
  data/stimulus_pool.json — 20 episode records
  data/target_images/*.png — copied target images for portability
"""
import json, os, glob, shutil, random
from collections import defaultdict, Counter

random.seed(42)  # reproducible sampling

OURS_ROOT   = os.environ["OURS_ROOT"]      # ProCompNav eval folder (binary questions)
POOLED_ROOT = os.environ["POOLED_ROOT"]    # Pooled Independent Matching eval folder (open-ended questions)
PAIRS_DIR   = os.environ["PAIRS_DIR"]      # folder with rendered target images named ep<id>_TARGET.png
OUT_DIR     = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study2_delivery/data"))
IMG_DIR     = f"{OUT_DIR}/target_images"

os.makedirs(IMG_DIR, exist_ok=True)

# --- 1. index Ours ---
ours_index = {}
for p in sorted(glob.glob(f"{OURS_ROOT}/*/*/info.json")):
    eid = int(os.path.basename(os.path.dirname(p)))
    ours_index[eid] = p

# --- 2. index Pooled ---
pooled_index = {}
for p in sorted(glob.glob(f"{POOLED_ROOT}/*/*/info.json")):
    eid = int(os.path.basename(os.path.dirname(p)))
    pooled_index[eid] = p

print(f"Ours eps: {len(ours_index)}")
print(f"Pooled eps: {len(pooled_index)}")

# --- 3. collect (ep_id, category, ours_binary_qs, pooled_open_qs, target_img) ---
candidates = []
for eid, ours_p in ours_index.items():
    try:
        info = json.load(open(ours_p))
    except Exception:
        continue
    # Ours binary questions
    binary_qs = []
    for ex in (info.get('pbp_results') or []):
        for prop, ans, _ in (ex.get('yes_no_result') or []):
            binary_qs.append({"prop": prop, "gt_answer": ans})
    if len(binary_qs) < 2:
        continue  # need Q>=2 for H1

    # target image exists?
    img_src = f"{PAIRS_DIR}/ep{eid}_TARGET.png"
    if not os.path.exists(img_src):
        continue

    # Pooled open questions (may be absent)
    open_qs = []
    if eid in pooled_index:
        try:
            pooled_info = json.load(open(pooled_index[eid]))
            for q_list in (pooled_info.get('questions_for_target_object_list') or []):
                # each q_list is [question_text]
                q = q_list[0] if isinstance(q_list, list) else str(q_list)
                open_qs.append(q)
        except Exception:
            pass

    candidates.append({
        "ep_id":    eid,
        "category": info.get('object_category'),
        "target_instance_id": info.get('target_object_instance_id'),
        "n_binary_q": len(binary_qs),
        "n_open_q":  len(open_qs),
        "binary_qs": binary_qs,
        "open_qs":   open_qs,
        "target_img_src": img_src,
    })

# --- 4. category=cabinet + Q=4 필터 (참가자당 1 trial x 2 조건, 4개 질문 씩) ---
before = len(candidates)
candidates = [c for c in candidates if c['category'] == 'cabinet' and c['n_binary_q'] == 4]
print(f"cabinet + Q=4 filter: {before} -> {len(candidates)}")

buckets = defaultdict(list)
buckets["Q4"] = candidates  # 하나의 bucket 만 유지

print(f"\nCandidate distribution (Q>=2, target img exists):")
for k in ['Q2', 'Q3', 'Q4p']:
    print(f"  {k}: {len(buckets[k])}")

# small pool 로 4개만 뽑음 (counterbalance 용). 참가자당 실제로는 2 trial 만 진행.
target_pool_size = 4
pool = buckets["Q4"]
random.shuffle(pool)
selected = pool[:target_pool_size]

print(f"\nSelected {len(selected)} episodes")
print("Category distribution in selected:")
for c, n in Counter(x['category'] for x in selected).most_common():
    print(f"  {c}: {n}")

# --- 5. copy target images to portable location ---
for c in selected:
    dst = f"{IMG_DIR}/ep{c['ep_id']}_target.png"
    shutil.copy(c['target_img_src'], dst)
    c['target_img'] = f"target_images/ep{c['ep_id']}_target.png"  # relative for app
    del c['target_img_src']

# --- 6. write stimulus_pool.json ---
out_path = f"{OUT_DIR}/stimulus_pool.json"
with open(out_path, 'w') as f:
    json.dump({
        "meta": {
            "n_eps": len(selected),
            "n_with_pooled": sum(1 for c in selected if c['open_qs']),
            "buckets": {k: len([c for c in selected if (c['n_binary_q']==2 if k=='Q2' else c['n_binary_q']==3 if k=='Q3' else c['n_binary_q']>=4)]) for k in ['Q2','Q3','Q4p']},
        },
        "episodes": selected,
    }, f, ensure_ascii=False, indent=2)

print(f"\nWrote {out_path}")
print(f"With Pooled open questions: {sum(1 for c in selected if c['open_qs'])}/{len(selected)}")
