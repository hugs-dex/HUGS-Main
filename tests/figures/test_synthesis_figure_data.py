import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from scripts.figures.synthetic_benchmark.synthesis_figure_data import (
    pca_ratio,
    public_output_name,
    summarize_run_from_raw,
    wrist_vector,
)

class SynthesisFigureDataTest(unittest.TestCase):
    def test_single_wrist_is_zero_padded(self):
        record = {"grasp_global_pose": np.array([1, 2, 3, 1, 0, 0, 0], dtype=float)}
        vector = wrist_vector(record)
        self.assertEqual(vector.shape, (12,))
        np.testing.assert_allclose(vector[:6], 0)
        np.testing.assert_allclose(vector[6:9], [1, 2, 3])

    def test_wxyz_quaternion_becomes_rotvec(self):
        record = {"grasp_global_pose": np.array([0, 0, 0, np.cos(np.pi / 4), 0, 0, np.sin(np.pi / 4)])}
        vector = wrist_vector(record)
        np.testing.assert_allclose(vector[9:], [0, 0, np.pi / 2], atol=1e-7)

    def test_public_raw_summary_uses_scale_and_success_filters(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = "readme_heur_fix_shadow_1000_20261001"
            output = root / public_output_name(run, "right_full", "shadow") / "evaluation" / "scene_a"
            output.mkdir(parents=True)
            np.save(output / "success.npy", {
                "obj_scale": np.array(0.08),
                "succ_flag": np.array(True),
                "grasp_global_pose": np.array([0, 0, 0, 1, 0, 0, 0]),
            })
            np.save(output / "penetrating.npy", {
                "obj_scale": np.array(0.08),
                "succ_flag": np.array(True),
                "self_pene": np.array(0.01),
            })
            summary = summarize_run_from_raw(run, root, "shadow", include_both_three=False)
            counts = summary["figure_data"]["scale_grasp_type_counts"]["0.08"]["right_full"]
            self.assertEqual(counts, {"evaluated_grasps": 2, "successful_grasps": 1})
            self.assertEqual(summary["grasp_types"], ["right_full"])

    def test_public_raw_summary_falls_back_to_succgrasp(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = "readme_heur_fix_shadow_1000_20261001"
            output_root = root / public_output_name(run, "right_full", "shadow")
            evaluation = output_root / "evaluation" / "scene_a"
            succgrasp = output_root / "succgrasp" / "scene_a"
            evaluation.mkdir(parents=True)
            succgrasp.mkdir(parents=True)
            record = {
                "obj_scale": np.array(0.08),
                "grasp_global_pose": np.array([0, 0, 0, 1, 0, 0, 0]),
            }
            np.save(evaluation / "success.npy", record)
            np.save(succgrasp / "success.npy", record)
            summary = summarize_run_from_raw(run, root, "shadow", include_both_three=False)
            counts = summary["figure_data"]["scale_grasp_type_counts"]["0.08"]["right_full"]
            self.assertEqual(counts["successful_grasps"], 1)

    def test_pca_ratio_uses_scene_centering(self):
        vectors = [np.array([x, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float) for x in (0, 1, 2)]
        self.assertAlmostEqual(pca_ratio(vectors), 100.0)

if __name__ == "__main__":
    unittest.main()
