"""Read schema-v2 figure counts and compute scene-averaged wrist-pose PCA."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

GRASP_TYPES = ("right_two", "right_three", "right_full", "both_three", "both_full")
DEFAULT_RUNS = {
    "shadow": (
        "single_type_DGN2k_1000_shadow",
        "single_scale_2_DGN2k_1000_shadow",
        "multi_scale_2_DGN2k_1000_shadow",
        "human_9_DGN2k_1000_shadow",
    ),
    "leap_sp": (
        "single_type_5_DGN2k_1000_leap_sp",
        "single_scale_6_DGN2k_1000_leap_sp",
        "multi_scale_6_DGN2k_1000_leap_sp",
        "human_5_DGN2k_1000_leap_sp",
    ),
}
METHOD_LABELS = dict(zip(("single_type", "single_scale", "multi_scale", "human"),
                         ("Heur-Fix", "Heur-Single", "Heur-Multi", "HUGS")))


@dataclass
class Method:
    label: str
    path: Path
    counts: dict[str, dict[str, dict[str, int]]]
    scenes: dict[str, list[str]]
    outputs: dict[str, Path]
    hand_geom_dist_threshold: float

    def count(self, scale: str, grasp_type: str, kind: str) -> int:
        return self.counts.get(scale, {}).get(grasp_type, {}).get(kind, 0)

    def average_count(self, scale: str, grasp_type: str, kind: str) -> float:
        scene_count = len(self.scenes.get(scale, []))
        return self.count(scale, grasp_type, kind) / scene_count if scene_count else 0.0

    def success_rates(self, modes: dict[str, str] | None = None) -> dict[str, float]:
        rates = {}
        for scale, counts in self.counts.items():
            selected = counts.values() if modes is None else [counts.get(modes.get(scale), {})]
            records = list(selected)
            total = sum(record.get("evaluated_grasps", 0) for record in records)
            successful = sum(record.get("successful_grasps", 0) for record in records)
            rates[scale] = 100.0 * successful / total if total else math.nan
        return rates


def scale_sort_key(scale: str) -> tuple[int, float | str]:
    try:
        return (0, float(scale))
    except ValueError:
        return (1, scale)


def load_method(path: Path, hand: str, label: str | None, include_both_three: bool,
                stats_root: Path | None) -> Method:
    """Load counts without modifying the cache; an explicit root relocates all runs."""
    data = json.loads(path.read_text())
    if data.get("schema_version") != 2 or data.get("hand") != hand:
        raise ValueError(f"Expected schema_version=2 and hand={hand}: {path}")
    run = data.get("run_name", path.stem)
    label = label or next((name for prefix, name in METHOD_LABELS.items()
                           if run.startswith(prefix + "_")), run)
    types = set(data["grasp_types"])
    if not include_both_three:
        types.discard("both_three")
    if not types or types.difference(GRASP_TYPES):
        raise ValueError(f"Unsupported or empty grasp_types: {path}")
    figure_data = data["figure_data"]
    counts = {
        scale: {g: {kind: int(record[kind]) for kind in ("evaluated_grasps", "successful_grasps")}
                for g, record in by_type.items() if g in types}
        for scale, by_type in figure_data["scale_grasp_type_counts"].items()
    }
    scenes = figure_data["scene_scale"]["scale_scene_ids"]
    if not counts:
        raise ValueError(f"Missing scale_grasp_type_counts: {path}")
    for scale, by_type in counts.items():
        for record in by_type.values():
            if not 0 <= record["successful_grasps"] <= record["evaluated_grasps"]:
                raise ValueError(f"Invalid counts at scale {scale}: {path}")
        if any(record["evaluated_grasps"] for record in by_type.values()) and not scenes.get(scale):
            raise ValueError(f"Missing scene denominator at scale {scale}: {path}")
    outputs = {}
    for item in data["per_grasp_type"]:
        if item["grasp_type"] not in types:
            continue
        raw = Path(item["output_path"])
        # Cache paths identify run directories. Explicit relocation takes priority
        # even when the original absolute directory still exists.
        output = stats_root / raw.name if stats_root is not None else raw
        if not output.is_absolute():
            output = output.resolve() if stats_root is not None else path.parent / output
        outputs[item["grasp_type"]] = output
    needed = {g for by_type in counts.values() for g, v in by_type.items() if v["evaluated_grasps"]}
    if needed.difference(outputs):
        raise ValueError(f"Missing output_path for {sorted(needed.difference(outputs))}: {path}")
    return Method(label, path, counts, scenes, outputs,
                  float(data.get("thresholds", {}).get("hand_geom_dist_thre", 0.0)))


def selected_modes(method: Method) -> dict[str, str]:
    """Select Heur-Single's most evaluated mode at each scale, preserving tie order."""
    selected = {}
    for scale, counts in method.counts.items():
        active = {g: record["evaluated_grasps"] for g, record in counts.items()
                  if record["evaluated_grasps"] > 0}
        if active:
            selected[scale] = max(active, key=active.get)
    return selected


def scalar(record: dict, key: str) -> float | None:
    value = np.asarray(record.get(key, []), dtype=np.float64)
    if value.size != 1:
        return None
    result = float(value.item())
    return result if np.isfinite(result) else None


def is_success(record: dict, relative: Path, successful_paths: set[str] | None,
               hand_geom_dist_threshold: float) -> bool:
    """Use the simulator flag/fallback, then apply the legacy collision filters."""
    succeeded = (bool(np.asarray(record["succ_flag"]).item()) if "succ_flag" in record
                 else relative.as_posix() in (successful_paths or set()))
    penetration = scalar(record, "self_pene")
    signed_distance = scalar(record, "self_signed_dist")
    return (succeeded and not (penetration is not None and penetration > 0)
            and not (signed_distance is not None and -signed_distance < hand_geom_dist_threshold))


def wrist_vector(record: dict) -> np.ndarray | None:
    """Return [left xyz+rotvec, right xyz+rotvec]; single hands use the right slot."""
    pose = np.asarray(record.get("grasp_global_pose", []), dtype=np.float64).reshape(-1)
    if pose.size < 7 or pose.size % 7 or not np.isfinite(pose).all():
        return None
    slots = []
    for item in pose.reshape(-1, 7):
        quat = item[3:]
        norm = np.linalg.norm(quat)
        if not np.isfinite(norm) or norm <= 0:
            return None
        quat = quat / norm
        if quat[3] < 0:
            quat = -quat
        vector_norm = np.linalg.norm(quat[:3])
        rotvec = (np.zeros(3) if vector_norm < 1e-12 else
                  quat[:3] / vector_norm * (2 * math.atan2(vector_norm, float(quat[3]))))
        slots.append(np.r_[item[:3], rotvec])
    return np.r_[np.zeros(6), slots[0]] if len(slots) == 1 else np.r_[slots[0], slots[1]]


def pca_ratio(vectors: list[np.ndarray]) -> float | None:
    """Return PC1 variance percent after centering, without feature standardization."""
    if not vectors:
        return None
    matrix = np.asarray(vectors, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 12 or not np.isfinite(matrix).all():
        return None
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    weights = np.linalg.svd(centered, full_matrices=False, compute_uv=False) ** 2
    total = float(weights.sum())
    return 100.0 if total <= 0 else float(weights[0] / total * 100)


def mean_scene_pca(scene_vectors: dict, scales: list[str]) -> dict[str, float]:
    result = {}
    for scale in scales:
        ratios = [pca_ratio(vectors) for vectors in scene_vectors.get(scale, {}).values()]
        valid = [value for value in ratios if value is not None]
        # Preserve the original convention for a scale without successful scenes.
        result[scale] = float(np.mean(valid)) if valid else 0.0
    return result


def compute_pca(method: Method, modes: dict[str, str] | None = None) -> tuple[dict, dict]:
    """Scan each type once, collecting both pooled-mode and optional HUGS-Single scenes.

    Missing or incomplete raw inputs raise before rendering. Counts are reconciled
    with the cache per scale/type so PCA and success panels use the same records.
    """
    vectors = defaultdict(lambda: defaultdict(list))
    single_vectors = defaultdict(lambda: defaultdict(list))
    invalid = 0
    for grasp_type, output in method.outputs.items():
        expected = {s: method.count(s, grasp_type, "evaluated_grasps") for s in method.counts}
        if not sum(expected.values()):
            continue
        eval_dir = output / "evaluation"
        if not eval_dir.is_dir():
            raise FileNotFoundError(f"Missing evaluation directory: {eval_dir}. Set --stats-root.")
        print(f"Scanning {method.label} {grasp_type}: {eval_dir}", flush=True)
        fallback = None
        evaluated = defaultdict(int)
        successful = defaultdict(int)
        for eval_path in eval_dir.rglob("*.npy"):
            record = np.load(eval_path, allow_pickle=True).item()
            relative = eval_path.relative_to(eval_dir)
            value = scalar(record, "obj_scale")
            scale = "unknown" if value is None else f"{value:.6g}"
            evaluated[scale] += 1
            if "succ_flag" not in record and fallback is None:
                succ_dir = output / "succgrasp"
                if not succ_dir.is_dir():
                    raise FileNotFoundError(f"No succ_flag in {eval_path} and no {succ_dir}")
                fallback = {p.relative_to(succ_dir).as_posix() for p in succ_dir.rglob("*.npy")}
            if not is_success(record, relative, fallback, method.hand_geom_dist_threshold):
                continue
            successful[scale] += 1
            vector = wrist_vector(record)
            if vector is None:
                invalid += 1
                continue
            scene = relative.parent.as_posix()
            vectors[scale][scene].append(vector)
            if modes is not None and modes.get(scale) == grasp_type:
                single_vectors[scale][scene].append(vector)
        for scale in set(expected) | set(evaluated):
            actual = (evaluated[scale], successful[scale])
            cached = (expected.get(scale, 0), method.count(scale, grasp_type, "successful_grasps"))
            if actual != cached:
                raise ValueError(f"Raw/cache count mismatch: {method.label} {grasp_type} {scale}: "
                                 f"raw evaluated/successful={actual}, cache={cached}")
        print(f"  matched {sum(evaluated.values()):,} evaluated records", flush=True)
    if invalid:
        print(f"Warning: {method.label}: skipped {invalid} successful grasps with invalid wrist poses")
    scales = list(method.counts)
    return mean_scene_pca(vectors, scales), mean_scene_pca(single_vectors, scales)
