"""H2 stimulus 준비 — 일반 가정 사물 5개 카테고리에서 각 1 ep 랜덤 샘플링.

각 ep 별로:
  - Ours 로그의 binary Q (yes_no_result) 그대로 (Q 수는 원래대로, 통일 X)
  - Pooled 로그의 open Q (questions_for_target_object_list) 그대로 (Q 수 원래대로)
  - Target image
"""
import json, os, glob, shutil, random

random.seed(20260727)  # reproducible

OURS_ROOT   = os.environ["OURS_ROOT"]      # ProCompNav eval folder (binary questions)
POOLED_ROOT = os.environ["POOLED_ROOT"]    # Pooled Independent Matching eval folder (open-ended questions)
PAIRS_DIR   = os.environ["PAIRS_DIR"]      # folder with rendered target images named ep<id>_TARGET.png
OUT_DIR     = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study1_binary_vs_open/data"))
IMG_DIR     = f"{OUT_DIR}/target_images_h2"

os.makedirs(IMG_DIR, exist_ok=True)

# 일반 가정 일상 사물 카테고리
DAILY_CATEGORIES = ["cabinet", "bed", "table", "desk", "tv"]

# 인덱스
ours_idx, pooled_idx = {}, {}
for p in glob.glob(f"{OURS_ROOT}/*/*/info.json"):
    eid = int(os.path.basename(os.path.dirname(p)))
    ours_idx[eid] = p
for p in glob.glob(f"{POOLED_ROOT}/*/*/info.json"):
    eid = int(os.path.basename(os.path.dirname(p)))
    pooled_idx[eid] = p

# 카테고리별 후보 ep 수집 (Ours + Pooled 둘 다 존재 + 이미지 존재)
by_cat = {c: [] for c in DAILY_CATEGORIES}
for eid, p in ours_idx.items():
    if eid not in pooled_idx: continue
    img = f"{PAIRS_DIR}/ep{eid}_TARGET.png"
    if not os.path.exists(img): continue
    try:
        info = json.load(open(p))
    except: continue
    cat = info.get('object_category')
    if cat not in DAILY_CATEGORIES: continue
    # 유효 이벤트만: binary Q 1개 이상 + open Q 1개 이상
    bqs = []
    for ex in (info.get('pbp_results') or []):
        for prop, ans, _ in (ex.get('yes_no_result') or []):
            bqs.append({"prop": prop, "gt_answer": ans})
    if not bqs: continue
    try:
        pi = json.load(open(pooled_idx[eid]))
    except: continue
    oqs = []
    for ql in (pi.get('questions_for_target_object_list') or []):
        oqs.append(ql[0] if isinstance(ql, list) else str(ql))
    if not oqs: continue
    by_cat[cat].append({
        "ep_id": eid,
        "category": cat,
        "target_instance_id": info.get('target_object_instance_id'),
        "binary_qs": bqs,
        "open_qs": oqs,
        "target_img_src": img,
    })

print("Candidate 수 by category:")
for c, lst in by_cat.items():
    print(f"  {c:10s}: {len(lst)}")

# 각 카테고리 1 ep 랜덤 샘플
selected = []
for c in DAILY_CATEGORIES:
    if not by_cat[c]:
        print(f"⚠️ {c}: 후보 없음, 스킵")
        continue
    ep = random.choice(by_cat[c])
    selected.append(ep)

# 이미지 복사 + relative path 로 변경
for ep in selected:
    dst = f"{IMG_DIR}/ep{ep['ep_id']}_target.png"
    shutil.copy(ep['target_img_src'], dst)
    ep['target_img'] = f"target_images_h2/ep{ep['ep_id']}_target.png"
    del ep['target_img_src']
    ep['n_binary_q'] = len(ep['binary_qs'])
    ep['n_open_q'] = len(ep['open_qs'])

out_path = f"{OUT_DIR}/stimulus_pool_h2.json"
with open(out_path, "w") as f:
    json.dump({"meta": {"n_eps": len(selected)}, "episodes": selected}, f, ensure_ascii=False, indent=2)

print(f"\nSelected {len(selected)} episodes:")
for ep in selected:
    print(f"  ep{ep['ep_id']:5d} ({ep['category']:10s}): {ep['n_binary_q']}Q binary + {ep['n_open_q']}Q open")
print(f"\nWrote {out_path}")
