import unittest

import numpy as np

from scripts.figures.synthetic_benchmark.synthesis_figure_data import pca_ratio, wrist_vector

class SynthesisFigureDataTest(unittest.TestCase):
    def test_single_wrist_is_zero_padded(self):
        record = {"grasp_global_pose": np.array([1, 2, 3, 0, 0, 0, 1], dtype=float)}
        vector = wrist_vector(record)
        self.assertEqual(vector.shape, (12,))
        np.testing.assert_allclose(vector[:6], 0)
        np.testing.assert_allclose(vector[6:9], [1, 2, 3])

    def test_pca_ratio_uses_scene_centering(self):
        vectors = [np.array([x, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float) for x in (0, 1, 2)]
        self.assertAlmostEqual(pca_ratio(vectors), 100.0)

if __name__ == "__main__":
    unittest.main()
