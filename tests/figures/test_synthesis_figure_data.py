import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from scripts.figures.synthetic_benchmark.synthesis_figure_data import (
    Method,
    compute_pca,
    hand_joint_slots,
    pca_ratio,
    public_output_name,
    summarize_run_from_raw,
    wrist_vector,
    wrist_joint_vector,
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

    def test_dual_wrists_follow_body_names(self):
        right = [1, 2, 3, 1, 0, 0, 0]
        left = [4, 5, 6, 1, 0, 0, 0]
        record = {"grasp_global_pose": right + left,
                  "wrist_body_names": ["rh_palm", "lh_palm"]}
        vector = wrist_vector(record)
        np.testing.assert_allclose(vector[:3], left[:3])
        np.testing.assert_allclose(vector[6:9], right[:3])
        record.update(grasp_global_pose=left + right, wrist_body_names=["lh_palm", "rh_palm"])
        np.testing.assert_allclose(wrist_vector(record), vector)
        np.testing.assert_allclose(wrist_vector({"grasp_global_pose": right + left}), vector)

    def test_joint_slots_filter_arms_and_align_reordered_names(self):
        record = {"joint_names": ["ra_TransXJ", "rh_b", "rh_a", "la_TransXJ", "lh_a", "lh_b"],
                  "grasp_joint_pos": [20, 10, 30, 40]}
        np.testing.assert_allclose(hand_joint_slots(record, 2), [30, 40, 10, 20])
        # Also accept joint values aligned to the complete names list.
        record["grasp_joint_pos"] = [999, 20, 10, 999, 30, 40]
        np.testing.assert_allclose(hand_joint_slots(record, 2), [30, 40, 10, 20])
        record = {"joint_names": ["rh_a", "lh_b", "lh_a", "rh_b"],
                  "grasp_joint_pos": [10, 40, 30, 20]}
        np.testing.assert_allclose(hand_joint_slots(record, 2), [30, 40, 10, 20])

    def test_single_joint_feature_padding_and_invalid_metadata(self):
        record = {"grasp_global_pose": [1, 2, 3, 1, 0, 0, 0],
                  "joint_names": ["rh_b", "rh_a"], "grasp_joint_pos": [20, 10]}
        vector = wrist_joint_vector(record, 2)
        self.assertEqual(vector.shape, (16,))
        np.testing.assert_allclose(vector[12:], [0, 0, 10, 20])
        self.assertIsNone(wrist_joint_vector(record, 3))
        self.assertIsNone(hand_joint_slots({"grasp_joint_pos": [10, 20]}, 2))
        record["wrist_body_names"] = ["lh_palm"]
        self.assertIsNone(wrist_joint_vector(record, 2))
        record["wrist_body_names"] = ["rh_palm"]
        record["grasp_joint_pos"] = [np.nan, 10]
        self.assertIsNone(wrist_joint_vector(record, 2))
        record.update(grasp_joint_pos=[20, 10], joint_names=["rh_a", "rh_a"])
        self.assertIsNone(wrist_joint_vector(record, 2))

    def test_joint_variation_reaches_scene_pca_and_single_selection(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            evaluation = root / "evaluation" / "scene_a"
            evaluation.mkdir(parents=True)
            for index, joints in enumerate(([1, 0], [-1, 0], [0, 1], [0, -1])):
                np.save(evaluation / f"{index}.npy", {
                    "obj_scale": 0.08, "succ_flag": True,
                    "grasp_global_pose": [0, 0, 0, 1, 0, 0, 0],
                    "joint_names": ["rh_a", "rh_b"], "grasp_joint_pos": joints,
                })
            method = Method("HUGS", root / "cache.json",
                            {"0.08": {"right_full": {"evaluated_grasps": 4, "successful_grasps": 4}}},
                            {"0.08": ["scene_a"]}, {"right_full": root}, 0.0)
            wrist, _ = compute_pca(method)
            joint, single = compute_pca(method, {"0.08": "right_full"}, "wrist_joint", 2)
            self.assertAlmostEqual(wrist["0.08"], 100.0)
            self.assertAlmostEqual(joint["0.08"], 50.0)
            self.assertEqual(joint, single)
            bad_record = {"obj_scale": 0.08, "succ_flag": True,
                          "grasp_global_pose": [0, 0, 0, 1, 0, 0, 0]}
            np.save(evaluation / "0.npy", bad_record)
            with self.assertRaisesRegex(ValueError, "Invalid wrist/joint feature"):
                compute_pca(method, diversity_feature="wrist_joint", joint_dim_per_hand=2)

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
