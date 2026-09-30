# HUGS figure scripts

This document records the public-data figure commands and their input
contracts. It is not a paper profile and does not contain private experiment
paths or generated figure-data caches.

## Public data

The synthesis success/diversity script reads raw evaluation records from the
sibling repository:

```text
../HUGS-DexGraspBench/output
```

The currently available Shadow runs are:

| Label | Base run | Available grasp types |
|---|---|---|
| Heur-Fix | `readme_heur_fix_shadow_1000_20261001` | `right_full` |
| Heur-Single | `readme_heur_single_shadow_1000_20261001` | `right_two`, `right_three`, `right_full`, `both_full` |
| Heur-Multi | `readme_heur_multi_shadow_1000_20261001` | `right_two`, `right_three`, `right_full`, `both_three`, `both_full` |

HUGS raw synthesis records are not included in the current public bundle, so
HUGS and derived HUGS-Single curves are omitted until those records are
available. The combined figure keeps the paper's four-method synthesis-panel
layout and reserves the HUGS panel and HUGS/HUGS-Single legend positions, while
leaving their plots empty. Missing data are not interpreted as zero-valued
experiments.

## Synthesis success and diversity

Run from HUGS-Main after the public component repositories are checked out as
siblings:

```bash
cd /path/to/hugs-public/HUGS-Main
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --hand shadow \
  --stats-root ../HUGS-DexGraspBench/output \
  --runs \
    readme_heur_fix_shadow_1000_20261001 \
    readme_heur_single_shadow_1000_20261001 \
    readme_heur_multi_shadow_1000_20261001 \
  --labels Heur-Fix Heur-Single Heur-Multi \
  --figure-data-dir outputs/figure-data/synthetic-benchmark/shadow \
  --output-dir outputs/figures/synthetic-benchmark/shadow \
  --formats pdf png \
  --dpi 600 \
  --diversity-feature wrist \
  --exclude-both-three \
  --refresh-figure-data
```

The first run scans the public `evaluation/` records and writes schema-v2
figure-data caches under `outputs/figure-data/`. Subsequent runs can reuse the
cache with `--load-figure-data`; `--stats-root` is still required for the raw
wrist-pose PCA scan:

```bash
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --hand shadow \
  --stats-root ../HUGS-DexGraspBench/output \
  --runs \
    readme_heur_fix_shadow_1000_20261001 \
    readme_heur_single_shadow_1000_20261001 \
    readme_heur_multi_shadow_1000_20261001 \
  --labels Heur-Fix Heur-Single Heur-Multi \
  --figure-data-dir outputs/figure-data/synthetic-benchmark/shadow \
  --output-dir outputs/figures/synthetic-benchmark/shadow \
  --formats pdf png \
  --dpi 600 \
  --diversity-feature wrist \
  --exclude-both-three \
  --load-figure-data
```

The cache stores public run directory names rather than machine-specific
absolute paths. The adapter applies the evaluation `succ_flag` (or the
`succgrasp` fallback for older records), removes records with positive
`self_pene`, and uses the public hand-geometry threshold. Wrist pose records
use the HUGS `[w, x, y, z]` quaternion contract. Object scales are stored in
metres and displayed in centimetres; diversity is the scene-averaged first
principal-component variance ratio of the successful wrist poses.

The generated `outputs/` directory is ignored by Git. Do not commit caches,
plots, raw evaluation records, checkpoints, or other run products.

## Local model paths

MANO is not needed by the synthesis success/diversity figure. Other figure
scripts may read a local `MANO_ROOT` from an ignored `.env`; a shareable
`.env.example` may document the variable name without recording a machine-
specific path. MANO models and formatted meshes are not part of this public
repository.
