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

The Shadow runs used for the local figure are:

| Label | Base run | Available grasp types |
|---|---|---|
| Heur-Fix | `readme_heur_fix_shadow_1000_20261001` | `right_full` |
| Heur-Single | `readme_heur_single_shadow_1000_20261001` | `right_two`, `right_three`, `right_full`, `both_full` |
| Heur-Multi | `readme_heur_multi_shadow_1000_20261001` | `right_two`, `right_three`, `right_full`, `both_three`, `both_full` |
| HUGS | `human_prior_1000_gpu0_5_20261007_090621` | `right_two`, `right_three`, `right_full`, `both_three`, `both_full` |

The HUGS evaluation records are available in the local sibling Bench output,
but are not included in the current public download. The script derives the
HUGS-Single curves from the same HUGS run. Reproducing those curves requires
the corresponding raw evaluation records; missing data are not interpreted as
zero-valued experiments.

## Synthesis success and diversity

Run from HUGS-Main after the public component repositories are checked out as
siblings. Times New Roman must be available to Matplotlib; it is the default
font and matches the original figure's typography.

The run names must be supplied because the script's default run list does not
select these evaluations. Method labels are inferred from the names.

```bash
cd /path/to/hugs-public/HUGS-Main
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --runs \
    readme_heur_fix_shadow_1000_20261001 \
    readme_heur_single_shadow_1000_20261001 \
    readme_heur_multi_shadow_1000_20261001 \
    human_prior_1000_gpu0_5_20261007_090621 \
  --diversity-feature wrist_joint \
  --figure-data-dir outputs/figure-data/synthetic-benchmark/shadow \
  --output-dir outputs/figures/synthetic-benchmark/shadow \
  --formats pdf png \
  --exclude-both-three
```

The command uses the defaults for Shadow, 600 DPI, and raw records under
`../HUGS-DexGraspBench/output`. It rebuilds schema-v2 count caches in the
specified figure-data directory and writes the wrist-joint PDF and PNG in the
specified output directory. `--exclude-both-three` removes the Both-Three mode.

For subsequent runs, append `--load-figure-data` to reuse count caches. PCA
still scans the raw records at the default stats root. Caches created with a
custom `--figure-data-dir` require that same option when loading.

If Matplotlib cannot find Times New Roman, add `--font-files /path/to/regular.ttf
/path/to/bold.ttf` with your local font paths. Alternatively, add
`--font-family "DejaVu Serif"`, which changes the figure's appearance.

The cache stores public run directory names rather than machine-specific
absolute paths. The adapter applies the evaluation `succ_flag` (or the
`succgrasp` fallback for older records), removes records with positive
`self_pene`, and uses the public hand-geometry threshold. Wrist pose records
use the HUGS `[w, x, y, z]` quaternion contract. Object scales are stored in
metres and displayed in centimetres.

The default diversity feature is `wrist_joint`: 12 wrist-pose dimensions
(left xyz + rotation vector, then right xyz + rotation vector), followed by
left and right finger-joint slots from `grasp_joint_pos`. Shadow uses 22 joints
per hand (56 total dimensions); Leap-SP uses 16 (44 total dimensions).
`wrist_body_names` identifies wrist order; older records without it use the
public producer's right-then-left order. `joint_names` is required in joint
mode: dummy-arm names are excluded, and finger joints are ordered by their
name suffix within each hand so record ordering cannot change PCA columns.
Absent hands have zero-filled slots. Invalid joint-mode features raise an
error rather than silently dropping successful grasps.

For each scene, PCA centers the successful-grasp vectors without feature
standardization or weighting, then computes the first principal-component
variance ratio. The plotted value is the mean of those ratios across scenes
at each scale. Positions are in metres; rotations and finger angles are in
radians, so joint mode changes the metric as well as its dimensionality.

Joint mode writes `object_scale_synthesis_success_wrist_joint_diversity_combined`
in the requested formats. Use `--diversity-feature wrist` for wrist-only PCA,
which retains the `object_scale_synthesis_success_diversity_combined` filename.
The two modes share counts, success rates, and layout; their outputs are
separate to avoid confusing different diversity metrics.

The generated `outputs/` directory is ignored by Git. Do not commit caches,
plots, raw evaluation records, checkpoints, or other run products.

## Local model paths

MANO is not needed by the synthesis success/diversity figure. Other figure
scripts may read a local `MANO_ROOT` from an ignored `.env`; a shareable
`.env.example` may document the variable name without recording a machine-
specific path. MANO models and formatted meshes are not part of this public
repository.
