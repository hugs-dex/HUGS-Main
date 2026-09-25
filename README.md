<h1 align="center">HUGS</h1>

<h3 align="center">Guiding Unified Dexterous Grasp Synthesis<br>Across Modes and Scales via Learned Human Priors</h3>

<p align="center">
  Mingrui Yu*, Yongpeng Jiang*, Yongyi Jia, Kangchen Lv,<br>
  Xiangjie Yan, Li Huang, Yi Ren, and Xiang Li<br>
  <strong>Tsinghua University</strong><br>
  <sup>* Equal contribution.</sup>
</p>

<p align="center">
  <a href="https://hugs-dex.github.io/">Project Page</a> •
  <a href="https://arxiv.org/abs/2607.04554">Paper</a> •
  <a href="https://hugs-dex.github.io/#overview">Video</a> •
  <a href="https://hugs-dex.github.io/blog.html">Blog</a> •
  <a href="https://huggingface.co/datasets/MingruiYu/HUGS">Object Assets</a> •
  <a href="https://huggingface.co/datasets/MingruiYu/HUGS-Human">Human Data</a>
</p>

<p align="center">
  <a href="https://hugs-dex.github.io/">
    <img src="https://hugs-dex.github.io/figures/teaser.png" width="100%" alt="HUGS generates dexterous grasps across object scales, from two-finger pinches to bimanual grasps.">
  </a>
</p>

**From small screws to large boxes.** HUGS learns human grasp preferences to guide
robot grasp synthesis across contact modes and object scales. It predicts plausible
contact modes and wrist initializations, then uses force-closure-aware optimization
to generate robot-specific grasps.

**HUGS-Main** is the project entry point for code, datasets, and reproduction guides.
The implementations live in the component repositories below.

## Overview

HUGS connects three stages:

1. **Learn human priors.** Learn object-conditioned contact-mode preferences and
   wrist poses from a compact human grasp dataset.
2. **Synthesize robot grasps.** Use these priors to guide robot-specific grasp
   optimization for single-hand and bimanual configurations.
3. **Evaluate and learn.** Filter grasps in simulation and use the resulting data
   to train grasp-generation models.

<p align="center">
  <img src="https://hugs-dex.github.io/figures/overview.png" width="100%" alt="HUGS pipeline: human demonstrations, object-conditioned priors, and robot grasp optimization.">
</p>

The paper reports **1.8K human grasps over 304 objects** and **3.2M synthesized
robot grasps over 157K scenes**, spanning object half-diagonal lengths of
**2–30 cm**. These are paper results; the currently available downloads are listed
separately below.

## Code

| Repository | What it provides | Availability |
| --- | --- | --- |
| **HUGS-Main** (this repository) | Project overview, component navigation, and dataset links | Public |
| [**HUGS-BODex**](https://github.com/hugs-dex/HUGS-BODex) | GPU-accelerated grasp synthesis and visualization for Shadow Hand and Leap-SP | Public |
| [**HUGS-DexGraspBench**](https://github.com/hugs-dex/HUGS-DexGraspBench) | MuJoCo evaluation, format conversion, and successful-grasp collection | Public |
| **HUGS-DexLearn** | Human-prior and robot grasp-model training, sampling, and export | In preparation |

### Getting started

Choose the component for your workflow and follow its installation guide. Each
component has its own environment; this entry repository needs no Python installation.

```bash
mkdir hugs-workspace
cd hugs-workspace
git clone https://github.com/hugs-dex/HUGS-Main.git

# Grasp synthesis
git clone https://github.com/hugs-dex/HUGS-BODex.git

# Simulation evaluation (optional)
git clone https://github.com/hugs-dex/HUGS-DexGraspBench.git
```

Continue with the component README to initialize its submodules and install its
dependencies:

- **Generate grasps:** [HUGS-BODex installation and examples](https://github.com/hugs-dex/HUGS-BODex#installation).
  Start with `surface_sample` initialization, which does not require human priors.
- **Evaluate grasps:** [HUGS-DexGraspBench workflows](https://github.com/hugs-dex/HUGS-DexGraspBench#producer-workflows).
  Supply generated grasp records and the matching object assets.
- **Train or export priors:** HUGS-DexLearn instructions will be linked when the
  public repository is available.

### Release status

The release is being prepared in stages. Current limitations:

- The published HUGS asset archives do not include
  `tabletop_scene_object_heights.jsonl`, required by the default synthesis suites.
  Surface synthesis needs a height cache computed from the selected public scenes
  and meshes, passed via `task.scene_source.object_height_record_path`.
  The public setup instructions for this preparation step are still pending.
- Exported human priors, model checkpoints, and the full synthesized robot-grasp
  dataset are not included in the current downloads. Human-initialized synthesis
  requires a prior export matching the scene IDs.
- Planning with a separately generated height cache has been checked for both hand
  suites. End-to-end synthesis and learning using only public inputs are still
  being validated; a successful dry-run is not a solver or reproduction result.

## Data

| Dataset | Available content |
| --- | --- |
| [**HUGS**](https://huggingface.co/datasets/MingruiYu/HUGS) | Processed DGN_2k object assets, scene configurations, splits, and partial point clouds |
| [**HUGS-Human**](https://huggingface.co/datasets/MingruiYu/HUGS-Human) | Human grasp processing inputs and formatted training data |

See each dataset card for download instructions, file layout, checksums, and usage
terms. Keep data outside the code repositories, preserve the archive directory
structure, and record the dataset revision used for each experiment. Write caches
and outputs to a separate run directory.

HUGS-Human training records are not exported synthesis priors. MANO models and
formatted canonical meshes are not included; workflows that need these resources
require separate preparation.

## Citation

If you find HUGS useful in your research, please cite our paper:

```bibtex
@article{yu2026hugs,
  title={HUGS: Guiding Unified Dexterous Grasp Synthesis Across Modes and Scales via Learned Human Priors},
  author={Mingrui Yu and Yongpeng Jiang and Yongyi Jia and Kangchen Lv and Xiangjie Yan and Li Huang and Yi Ren and Xiang Li},
  journal={arXiv preprint arXiv:2607.04554},
  year={2026}
}
```

## Acknowledgements and usage terms

HUGS builds on [BODex](https://github.com/JYChen18/BODex),
[cuRobo](https://github.com/NVlabs/curobo), and the dependencies acknowledged in
each component repository. We thank their authors for making their work available.

Code and datasets retain their respective licenses and usage terms. HUGS-BODex
inherits an NVIDIA license restricting use to non-commercial research or
evaluation; a project-wide license has not yet been selected. This entry repository
does not relicense component code, assets, or datasets.

For project questions, please open an
[issue](https://github.com/hugs-dex/HUGS-Main/issues). For a component-specific bug,
use that component's issue tracker and include the command, code commit, dataset
revision, and relevant logs.
