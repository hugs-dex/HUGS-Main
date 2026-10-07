# HUGS figure reproduction

## Shadow synthesis success and diversity

The figure reads raw `evaluation/` records from the sibling
`../HUGS-DexGraspBench/output` directory. Supply the four base `exp_name` values
used for the Bench evaluations, without the grasp-type and hand suffixes. Replace
the uppercase placeholders below with your own run names. HUGS evaluation
records are required and are not part of the current public download.

```bash
cd /path/to/hugs-public/HUGS-Main
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --hand shadow \
  --runs HEUR_FIX_EXP_NAME HEUR_SINGLE_EXP_NAME HEUR_MULTI_EXP_NAME HUGS_EXP_NAME \
  --labels Heur-Fix Heur-Single Heur-Multi HUGS \
  --diversity-feature wrist_joint \
  --exclude-both-three \
  --output-dir outputs/figures/synthetic-benchmark/shadow \
  --formats pdf png
```

The order of `--labels` must match `--runs`. The script derives HUGS-Single
from the HUGS evaluation records. Missing grasp types do not become zero-valued
experiments. With `--exclude-both-three`, the plotted modes omit Both-Three.
The output is
`outputs/figures/synthetic-benchmark/shadow/object_scale_synthesis_success_wrist_joint_diversity_combined.{pdf,png}`.

The first run refreshes count caches under the default
`outputs/figure-data/synthetic_benchmark/shadow` directory. Add
`--load-figure-data` on later runs to reuse those counts; diversity PCA still
reads the raw evaluation records. The script uses Times New Roman by default.
If Matplotlib cannot find it, pass local regular and bold font files with
`--font-files`, or choose another font with `--font-family`.

Success uses the evaluation `succ_flag` (or `succgrasp` for older records),
excludes positive `self_pene`, and applies the hand-geometry threshold. For
`wrist_joint`, each successful Shadow grasp contributes a 56-dimensional
left/right wrist-pose and finger-joint vector. PCA is centered per scene; the
figure plots the mean first-component variance ratio across scenes at each
object scale. Positions are in metres, rotations and joints in radians, and
the displayed object scale is in centimetres. See the figure script and its
data adapter for record and ordering details.

The generated `outputs/` directory is ignored by Git. Keep caches, figures,
raw evaluation records, and checkpoints out of the repository.
