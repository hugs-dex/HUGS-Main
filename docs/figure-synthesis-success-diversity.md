# Object-scale synthesis, success, and diversity figure

The script reproduces the three panels used by the Shadow (Fig. 4) and LEAP-SP
(Fig. 16) results. It consumes schema-v2 `figure_data` JSON files and the raw
`evaluation/` records referenced by those files for the scene-level 12D wrist
pose PCA. Object scales are stored in metres and displayed in centimetres.
`HUGS-Single` is derived from the HUGS records using the mode selected by the
Heur-Single counts at each scale.

No paper profile is required. The paper commands explicitly exclude Both-Three:

```bash
cd /path/to/HUGS-Main
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --hand shadow \
  --runs single_type_DGN2k_1000_shadow single_scale_2_DGN2k_1000_shadow \
         multi_scale_2_DGN2k_1000_shadow human_9_DGN2k_1000_shadow \
  --figure-data-dir /path/to/AnyScaleGraspMain/output/figure_data/synthetic_benchmark/shadow \
  --stats-root /path/to/BimanDexGraspBench/output \
  --output-dir output/figures/synthetic_benchmark/shadow \
  --formats pdf png --dpi 600 \
  --diversity-feature wrist --exclude-both-three
```

```bash
cd /path/to/HUGS-Main
python scripts/figures/synthetic_benchmark/plot_object_scale_synthesis_success_diversity_combined.py \
  --hand leap_sp \
  --runs single_type_5_DGN2k_1000_leap_sp single_scale_6_DGN2k_1000_leap_sp \
         multi_scale_6_DGN2k_1000_leap_sp human_5_DGN2k_1000_leap_sp \
  --figure-data-dir /path/to/AnyScaleGraspMain/output/figure_data/synthetic_benchmark/leap_sp \
  --stats-root /path/to/BimanDexGraspBench/output \
  --output-dir output/figures/synthetic_benchmark/leap_sp \
  --formats pdf png --dpi 600 \
  --diversity-feature wrist --exclude-both-three
```

The JSON cache and raw evaluation output are external inputs; do not commit them
or generated figures to HUGS-Main. `--stats-root` must point to the directory
containing the per-run grasp-type output directories. The script validates raw
and cached evaluated/successful counts before rendering, so incomplete inputs
fail clearly instead of producing an empty PCA curve.
