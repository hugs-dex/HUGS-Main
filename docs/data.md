# Data and Assets

The [HUGS dataset](https://huggingface.co/datasets/MingruiYu/HUGS) provides object
assets; [HUGS-Human](https://huggingface.co/datasets/MingruiYu/HUGS-Human) provides
human grasp processing inputs and formatted training data. Follow the dataset
cards for download instructions, archive layout, checksums, and usage terms.
Record the dataset revision used for each experiment.

## Shared Dataset Root

```bash
export HUGS_DATASET_ROOT=/path/to/hugs-dataset
```

Keep datasets outside source repositories. The loader-facing layout is:

```text
hugs-dataset/
├── object/
│   └── DGN_2k/
│       ├── processed_data/
│       ├── scene_cfg/
│       ├── valid_split/
│       └── vision_data/          # If partial point clouds are installed
└── OurHumanGraspFormat/
    ├── grasp/
    ├── object/
    └── metadata.csv
```

Outer archive/extraction directories are storage organization, not loader roots.
Preserve relative mesh paths inside scene files. Exported records with
`path_root: HUGS_DATASET_ROOT` resolve their dataset-relative paths against this
root; explicit absolute inputs must exist on the current machine. Components
do not infer former dataset locations.

## Inputs by Task

| Task | Inputs beyond source code |
| --- | --- |
| BODex surface synthesis | Object meshes/collision assets, scenes, splits, and generated height table |
| BODex human initialization | Surface-task assets plus compatible per-scene Human Prior exports |
| DexLearn Human training | Formatted human grasps and their object data |
| DexLearn prior export | Trained Human checkpoints and target object scenes |
| DexLearn Human visualization | Separately obtained MANO models |
| Bench evaluation | Producer grasp records and corresponding objects, including `info/simplified.json`; original joint metadata for learned robot samples |
| DexLearn Robot training | Assembled successful robot grasps, metadata, hand assets, splits, and configured point clouds |

For synthesis, the object release includes
`object_assets/DGN_2k/DGN_2k_processed_scene_cfg_valid_split.tar.gz`.
The separate `DGN_2k_three_realsense_d435_random4096.tar.gz` contains partial point
clouds used by the default Robot learning configuration.

The height table `tabletop_scene_object_heights.jsonl` is generated locally.
Follow [BODex data preparation](https://github.com/hugs-dex/HUGS-BODex/blob/main/docs/workflows.md#prepare-data),
including the local-cache option for read-only datasets. A partial height cache
must cover the scenes selected for synthesis.

## Asset and Output Settings

`HUGS_DATASET_ROOT` is shared. Other settings belong to individual components:

| Component | Setting | Meaning |
| --- | --- | --- |
| BODex | `HUGS_OBJECT_ROOT` in README commands | Object collection used to construct the explicit scene glob |
| BODex | `HUGS_OUTPUT_ROOT` | Override the default `src/curobo/content/assets/output/` root |
| BODex | `task.mano_root` | MANO files for the optional human-hand viewer |
| Bench | `HUGS_BODEX_OUTPUT_ROOT` / `--bodex-path` | BODex producer output root consumed by the wrapper |
| Bench | `save_root` | Output root for direct Hydra tasks; batch wrappers use `output/` |
| DexLearn | `HUGS_ASSET_ROOT` | Robot URDF and mesh assets |
| DexLearn | `HUGS_OUTPUT_ROOT` | Model checkpoints, samples, and exports; defaults to `output/` |
| DexLearn | `MANO_ROOT` | Licensed MANO models for tasks that use MANO |

These settings do not create assets or download weights. Follow each component's
installation and input guide in its own environment.

## Availability

Current downloads contain object assets and Human data. They do not contain
model checkpoints, exported synthesis priors, or the full synthesized robot-grasp
dataset reported in the paper. HUGS-Human records are training inputs, rather
than ready-to-consume synthesis priors.

MANO models and formatted canonical meshes are not included. Obtain and prepare
them separately for tasks requiring them. Code, object assets, and human data
retain their own usage terms.

Use [DexLearn](https://github.com/hugs-dex/HUGS-DexLearn#human-prior) to train and
export priors. Use [BODex and Bench](workflows.md) to generate, filter, and assemble
robot training data. Figure scripts require their corresponding raw evaluation
records; local run names in a guide do not make those records part of a checkout.
