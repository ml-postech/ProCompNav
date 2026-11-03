<div align="center">

# ProCompNav: Proactive Instance Navigation with Comparative Judgment for Ambiguous User Queries

<h2><strong>NeurIPS 2026 (Oral)</strong></h2>

**Junhyuk Kwon<sup>1</sup>, Seungjoon Lee<sup>2</sup>, Hyejin Park<sup>1</sup>, Kyle Min<sup>3</sup>, Jungseul Ok<sup>1,2</sup>**

<sup>1</sup>GSAI, POSTECH&nbsp;&nbsp; <sup>2</sup>CSE, POSTECH&nbsp;&nbsp; <sup>3</sup>Oracle

<a href="https://tree-jhk.github.io/procompnav/">
<img src="https://img.shields.io/badge/Project-Page-1f6feb?logo=githubpages&logoColor=white">
</a>
<a href="https://arxiv.org/abs/2605.06223">
<img src="https://img.shields.io/badge/arXiv-2605.06223-b31b1b?logo=arxiv&logoColor=white">
</a>
<a href="https://arxiv.org/pdf/2605.06223">
<img src="https://img.shields.io/badge/Paper-PDF-1a7f37?logo=adobeacrobatreader&logoColor=white">
</a>

</div>

---
<p align="center">
  <img src="docs/figures/teaser.jpg" alt="ProCompNav teaser" width="90%">
</p>

**ProCompNav** is a training-free, two-stage framework for instance navigation under ambiguous user queries. It first explores the scene to build a **candidate pool** of plausible targets, then disambiguates by *comparative judgment* — choosing, at each round, an attribute–value pair that **splits the current pool** into two non-empty groups, asking a single binary yes/no question, and pruning all inconsistent candidates at once.

Crucially, comparative judgment does not need an attribute that *uniquely identifies* the target. Every round only needs a valid splitter, whereas pooled independent matching — scoring each candidate against the user's description in isolation — is reliable only when the collected evidence is already sufficient to separate the target from its distractors. ProCompNav therefore reframes disambiguation from open-ended target description to **pool-level discriminative questioning**, where each question is chosen to narrow the candidate set.

---

## News

- [2026/12] Presenting at NeurIPS 2026 in Sydney: [Poster 🖼️ Session 5, Thu, Dec 10, 10:00 AM – 1:00 PM AEDT, Hall 1-4, ICC Sydney](https://neurips.cc/virtual/2026/loc/sydney/poster/153423). Come visit us! (Oral session schedule to be announced.)
- [2026/11] Code released.
- [2026/09] Accepted to **NeurIPS 2026 as an oral 🎤 presentation!** 🎉

---

## Method

<p align="center">
  <img src="docs/figures/method.jpg" alt="Method overview" width="90%">
</p>

---

## Installation

The full environment is packaged as a Docker image. All Python dependencies are frozen in [`requirements.lock`](requirements.lock); every `git+` dep is pinned to a specific commit hash; `llama.cpp` is pinned to tag `b7628`.

```bash
git clone https://github.com/ml-postech/ProCompNav.git
cd ProCompNav
docker build -t procompnav:latest .
```

The build pulls `nvidia/cuda:12.6.0-devel-ubuntu22.04`, compiles llama.cpp with CUDA, and installs the locked stack (PyTorch 2.9 + cu126, Habitat-Sim 0.2.4, GroundingDINO, MobileSAM, sentence-transformers, …). Expect ~45 minutes on a fast machine.

---

## Data & Weights

Set a host data root that will hold every dataset and weight not shipped in this repo. The launcher bind-mounts the same path inside the container, so absolute-path symlinks (common in HM3D scene folders) resolve transparently.

```bash
export PROCOMPNAV_DATA_DIR=$HOME/procompnav_data
mkdir -p $PROCOMPNAV_DATA_DIR
```

### 1. HM3D Scenes

You need a Matterport account. Register at [Matterport](https://matterport.com/habitat-matterport-3d-research-dataset) to obtain credentials.

```bash
export MATTERPORT_TOKEN_ID=<YOUR_TOKEN_ID>
export MATTERPORT_TOKEN_SECRET=<YOUR_TOKEN_SECRET>

# 3D scans (val split is sufficient for ProCompNav)
python -m habitat_sim.utils.datasets_download \
    --username $MATTERPORT_TOKEN_ID --password $MATTERPORT_TOKEN_SECRET \
    --uids hm3d_val_v0.2 \
    --data-path $PROCOMPNAV_DATA_DIR
```

After download you should have:

```
$PROCOMPNAV_DATA_DIR/scene_datasets/hm3d/hm3d_annotated_basis.scene_dataset_config.json
$PROCOMPNAV_DATA_DIR/scene_datasets/hm3d/val/<scene>/<scene>.{glb,semantic.glb,semantic.txt,basis.navmesh}
```

The Instance-ImageNav / TextNav episodes refer to scenes as `scene_datasets/hm3d_v0.2/val/...`. If that directory does not exist, add an alias:

```bash
ln -s hm3d $PROCOMPNAV_DATA_DIR/scene_datasets/hm3d_v0.2
```

### 2. Instance Text-Goal Navigation (PSL benchmark)

Follow [PSL-InstanceNav](https://github.com/XinyuSun/PSL-InstanceNav) for context.

```bash
# Instance-ImageNav episode scenes (val)
wget https://dl.fbaipublicfiles.com/habitat/data/datasets/imagenav/hm3d/v3/instance_imagenav_hm3d_v3.zip
unzip instance_imagenav_hm3d_v3.zip -d $PROCOMPNAV_DATA_DIR/datasets/
rm instance_imagenav_hm3d_v3.zip

# Text-goal annotations
mkdir -p $PROCOMPNAV_DATA_DIR/datasets/instancenav/val
wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1KNdv6isX1FDZi4KCVPiECYDxijg9cZ3L" \
    -O $PROCOMPNAV_DATA_DIR/datasets/instancenav/val/val_text.json.gz

# Link episode content
ln -s $PROCOMPNAV_DATA_DIR/datasets/instance_imagenav_hm3d_v3/val/content \
      $PROCOMPNAV_DATA_DIR/datasets/instancenav/val/content
```

### 3. CoIN-Bench

Download the CoIN-Bench dataset (`val_seen`, `val_unseen`, `val_seen_synonyms`) from [`ftaioli/CoIN-Bench`](https://huggingface.co/datasets/ftaioli/CoIN-Bench) on HuggingFace. Follow the instructions at the upstream [CoIN repository](https://github.com/intelligolabs/CoIN) for setup details, and place the resulting `CoIN-Bench/` directory in the repo root.

### 4. Model Weights

`mobile_sam.pt`, `pointnav_weights.pth`, `spot_pointnav_weights.pth`, and `dummy_policy.pth` are already in [`data/`](data/). The remaining weights are downloaded separately.

**Local weight files** (place under `data/`):

```bash
# GroundingDINO (too large to live in git)
wget -O data/groundingdino_swint_ogc.pth \
    https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
```

**HuggingFace cache** (point `HF_HOME` at a host directory; the launcher bind-mounts it):

```bash
export HF_HOME=$HOME/.cache/huggingface

# 1) Qwen3-VL-8B-Instruct GGUF — local LLM/MLLM via llama.cpp
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct-GGUF \
    "Qwen3VL-8B-Instruct-F16.gguf" "mmproj-Qwen3VL-8B-Instruct-F16.gguf"

# 2) BLIP2 image-text-matching — value-map scoring
huggingface-cli download Salesforce/blip2-itm-vit-g

# 3) DINOv2-large — dense image embedding for candidate clustering
huggingface-cli download facebook/dinov2-large

# 4) all-MiniLM-L6-v2 — dense text embedding for candidate clustering
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2

# 5) DeBERTa-v3-large MNLI — attribute–value entailment for comparative judgment
huggingface-cli download MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli
```

Models 2–5 are auto-downloaded by `transformers` on first run if missing, but pre-fetching avoids cold-start latency and unpredictable build-time network use.

### 5. Final layout

```
$PROCOMPNAV_DATA_DIR/
├── scene_datasets/
│   └── hm3d/
│       ├── hm3d_annotated_basis.scene_dataset_config.json
│       └── val/
│           └── <scene>/<scene>.{glb,semantic.glb,semantic.txt,basis.navmesh}
└── datasets/
    ├── instancenav/
    │   └── val/
    │       ├── val_text.json.gz
    │       └── content/ -> ../../instance_imagenav_hm3d_v3/val/content
    └── instance_imagenav_hm3d_v3/
        └── val/content/<scene>.json.gz
```

---

## Evaluation

All evaluations launch through [`run_experiments.py`](run_experiments.py), which generates a Docker `run` script and executes it. Two GPUs per invocation: one for the LLM (llama.cpp) server, one for the vision servers (GroundingDINO + BLIP2 + MobileSAM) and the policy.

### CoIN-Bench (main table)

```bash
# val_seen
python run_experiments.py \
    --task_type coin --split val_seen \
    --vllm_gpu 0 --vision_gpu 1 \
    --shard_size 70 --shard0 0 --shard1 1 \
    --eval_folder_name procompnav_coin_val_seen

# val_unseen
python run_experiments.py \
    --task_type coin --split val_unseen \
    --vllm_gpu 0 --vision_gpu 1 \
    --shard_size 70 --shard0 0 --shard1 1 \
    --eval_folder_name procompnav_coin_val_unseen

# val_seen_synonyms
python run_experiments.py \
    --task_type coin --split val_seen_synonyms \
    --vllm_gpu 0 --vision_gpu 1 \
    --shard_size 70 --shard0 0 --shard1 1 \
    --eval_folder_name procompnav_coin_val_seen_synonyms
```

### Instance Text-Goal Navigation (PSL val)

```bash
python run_experiments.py \
    --task_type text_goal --split val \
    --vllm_gpu 0 --vision_gpu 1 \
    --shard_size 70 --shard0 0 --shard1 1 \
    --eval_folder_name procompnav_textnav_val
```

### Parallel sharding

Each invocation occupies 2 GPUs and runs shards `--shard0` and `--shard1` (each `--shard_size` episodes) in parallel. Cover every shard of the split: CoIN-Bench val_seen has 831 episodes, so `--shard_size 70` gives 12 shards (0–11), i.e., 6 invocations. On a 12-GPU host:

```bash
for i in 0 1 2 3 4 5; do
  python run_experiments.py \
      --task_type coin --split val_seen \
      --vllm_gpu $((2*i)) --vision_gpu $((2*i+1)) \
      --shard_size 70 --shard0 $((2*i)) --shard1 $((2*i+1)) \
      --eval_folder_name procompnav_coin_val_seen &
  sleep 30   # stagger start-up
done
wait
```

With fewer GPUs, run the remaining invocations (the remaining `--shard0/--shard1` pairs) after the first ones finish.

### Flags

`python run_experiments.py -h` for the full list. Key knobs (defaults reproduce the main ProCompNav results):

| Flag | Default | Effect |
|---|---|---|
| `--enable_NLI_based` | `True` | NLI-based attribute–value question selection |
| `--enable_pbp_refinement` | `True` | Property-based pool refinement |
| `--pbp_refinement_thres` | `0.9` | NLI entailment threshold τ used in pool refinement |
| `--instance_grouping_method` | `dense_average_image_text` | How the current pool is split into a core set and a remainder |
| `--min_num_instances_for_pbp_trigger` | auto (CoIN: 5, TextNav: 3) | Candidate-pool size N_min that starts the Recursive Comparison Stage |
| `--trigger_step` | auto (CoIN: 400, TextNav: 600) | Step at which the Recursive Comparison Stage starts if the pool has not reached N_min |
| `--stage2_method` | `procompnav` | Disambiguation after pool construction: `procompnav` (comparative judgment) or `pim` (Pooled Independent Matching baseline) |

### Ablation options

| Flag | Value | Ablation in the paper |
|---|---|---|
| `--instance_grouping_method` | `kmeans` | *w/o similarity-based core set*: replaces the core–remainder split with KMeans (k=2, `random_state=42`, `n_init=10`) on the same text+image embeddings as the default split (all-MiniLM-L6-v2 and DINOv2, concatenated so that the inner product is the averaged similarity). Set by `--kmeans_modality` (default `image_text`). |

### Pooled Independent Matching baseline

`--stage2_method pim` keeps ProCompNav's pool construction and replaces comparative judgment with AIUTA-style independent matching: one open-ended question per collected candidate (conditioned on the facts gathered so far), then every candidate is rescored against the final facts and ties are broken by the LLM.

```bash
python run_experiments.py --task_type coin --split val_seen \
    --vllm_gpu 0 --vision_gpu 1 \
    --shard_size 70 --shard0 0 --shard1 1 \
    --stage2_method pim --eval_folder_name pim_coin_val_seen
```

### Question-format and attribute-selection ablations (separate branches)

The ablations in the appendix section "Question Format and Candidate Comparison" are kept on separate branches. Check out the branch and add the `--stage2_method` value to the commands above. Each branch README describes the variant.

| Branch | `--stage2_method` | Ablation |
|---|---|---|
| `ablation/binary-pim` | `binary_pim` | Binary PIM: PIM with one yes/no attribute-value question per candidate |
| `ablation/no-candidate-info` | `no_candidate_info` | "No candidate information": binary questions chosen from the category and previous answers only |
| `ablation/single-candidate` | `single_candidate` | "Single candidate": binary questions chosen from one candidate description at a time |

---

## Outputs

```
logs/<eval_folder_name>/                                         # stdout of the LLM server and each shard
eval_folder/<split>/<eval_folder_name>/<timestamp>_<a>_<b>/<episode_id>/info.json   # per-episode results (one folder per shard)
~/procompnav_videos/<eval_folder_name>/                          # rendered videos (if --save_video True)
```

Aggregate Success Rate (SR), SPL, number of questions, and response length over all shards:

```bash
python scripts/compute_info_averages.py eval_folder/<split>/<eval_folder_name>/*
```

The paper's metrics correspond to these rows of the summary table:

| Paper | Row | Averaged over |
|---|---|---|
| SR | `Average SR` | all episodes |
| SPL | `Average SPL` | all episodes |
| RL | `RL_total` | all episodes (response tokens per episode) |
| NQ | `NQ (episodes with >=1 question)` | episodes with at least one question |
| MaxQ | `MaxQ (episodes reaching 4 questions)` | all episodes |

---

## Repository layout

```
procompnav/
├── Dockerfile                  # CUDA 12.6 + llama.cpp b7628 + Habitat 0.2.4
├── requirements.lock           # locked pip env (290 pinned packages)
├── run_experiments.py          # Docker-based launcher (entrypoint)
├── scripts/
│   ├── launch_qwen3_vl_8b_instruct_llamacpp.sh
│   ├── new_launch_vlm_servers.sh
│   ├── compute_info_averages.py
│   └── parse_jsons.py
├── vlfm/                       # ProCompNav policy + PBP module (built on VLFM)
│   ├── policy/
│   ├── mapping/
│   ├── vlm/                    # GroundingDINO/BLIP2/MobileSAM clients + PBP module
│   └── ...
├── config/                     # Hydra task / experiment configs
├── data/                       # MobileSAM + PointNav weights (GroundingDINO download separately)
├── GroundingDINO/              # GroundingDINO source (configs)
├── user_study/                 # Streamlit apps + stimuli for the two user studies (see user_study/README.md)
└── docs/
    └── figures/                # teaser.jpg, method.jpg
```

The user-study apps and the stimuli drawn from ProCompNav and Pooled Independent Matching logs are in
[`user_study/`](user_study/README.md). Participant responses are not released.

---

## Acknowledgements

This codebase is built upon [VLFM](https://github.com/bdaiinstitute/vlfm) and [AIUTA / CoIN](https://github.com/intelligolabs/CoIN). We thank the authors for their excellent work and for releasing their code and benchmarks.

---

## Citation

```bibtex
@inproceedings{kwon2026proactive,
  title={Proactive Instance Navigation with Comparative Judgment for Ambiguous User Queries},
  author={Kwon, Junhyuk and Lee, Seungjoon and Park, Hyejin and Min, Kyle and Ok, Jungseul},
  booktitle={Advances in Neural Information Processing Systems},
  year={2026}
}
```

---

## License

This repository is released under the terms of the [LICENSE](LICENSE) file.
