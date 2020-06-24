import unittest
import os
import pandas as pd
from late_classifier.features import ColorFeatureExtractor
from late_classifier.features import DetectionsPreprocessorZTF


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_PATH = os.path.abspath(os.path.join(FILE_PATH, "../data"))


class TestColors(unittest.TestCase):
    def setUp(self) -> None:
        preprocess_ztf = DetectionsPreprocessorZTF()

        raw_det_ZTF18abakgtm = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abakgtm_det.csv'), index_col="oid")
        det_ZTF18abakgtm = preprocess_ztf.preprocess(raw_det_ZTF18abakgtm)

        raw_det_ZTF18abvvcko = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abvvcko_det.csv'), index_col="oid")
        det_ZTF18abvvcko = preprocess_ztf.preprocess(raw_det_ZTF18abvvcko)

        raw_det_ZTF17aaaaaxg = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF17aaaaaxg_det.csv'), index_col="oid")
        det_ZTF17aaaaaxg = preprocess_ztf.preprocess(raw_det_ZTF17aaaaaxg)

        raw_det_ZTF18aaveorp = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18aaveorp_det.csv'), index_col="oid")
        det_ZTF18aaveorp = preprocess_ztf.preprocess(raw_det_ZTF18aaveorp)

        keys = ['fid', 'magpsf_corr', 'magpsf']
        self.detections = pd.concat(
            [det_ZTF17aaaaaxg[keys],
             det_ZTF18abvvcko[keys],
             det_ZTF18abakgtm[keys],
             det_ZTF18aaveorp[keys]],
            axis=0
        )
        fake_objects = pd.DataFrame(
            index=['ZTF17aaaaaxg', 'ZTF18abvvcko', 'ZTF18abakgtm', 'ZTF18aaveorp'],
            data=[[True], [False], [True], [False]],
            columns=['corrected']
        )
        self.objects = fake_objects

    def test_many_objects(self):
        color_extractor = ColorFeatureExtractor()
        colors = color_extractor.compute_features(self.detections, objects=self.objects)
        self.assertEqual(colors.shape, (4, 4))
        objects_without_colors = colors[['g-r_max', 'g-r_mean']].isna().any(axis=1).values.flatten()
        self.assertTrue(
            (objects_without_colors == [False, True, True, False]).all()
        )
        objects_without_colors = colors[['g-r_max_corr', 'g-r_mean_corr']].isna().any(axis=1).values.flatten()
        self.assertTrue(
            (objects_without_colors == [False, True, True, True]).all()
        )


if __name__ == '__main__':
    unittest.main()
