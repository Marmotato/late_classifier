import unittest
import os
import pandas as pd
from late_classifier.features import SupernovaeDetectionAndNonDetectionFeatureExtractor
from late_classifier.features import DetectionsPreprocessorZTF


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_PATH = os.path.abspath(os.path.join(FILE_PATH, "../data"))


class TestSNDetAndNonDetExtractor(unittest.TestCase):
    def setUp(self) -> None:
        preprocess_ztf = DetectionsPreprocessorZTF()

        raw_det_ZTF18abakgtm = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abakgtm_det.csv'), index_col="oid")
        det_ZTF18abakgtm = preprocess_ztf.preprocess(raw_det_ZTF18abakgtm)
        raw_nondet_ZTF18abakgtm = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abakgtm_nondet.csv'), index_col="oid")

        raw_det_ZTF18abvvcko = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abvvcko_det.csv'), index_col="oid")
        det_ZTF18abvvcko = preprocess_ztf.preprocess(raw_det_ZTF18abvvcko)
        raw_nondet_ZTF18abvvcko = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18abvvcko_nondet.csv'), index_col="oid")

        raw_det_ZTF17aaaaaxg = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF17aaaaaxg_det.csv'), index_col="oid")
        det_ZTF17aaaaaxg = preprocess_ztf.preprocess(raw_det_ZTF17aaaaaxg)
        raw_nondet_ZTF17aaaaaxg = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF17aaaaaxg_nondet.csv'), index_col="oid")

        raw_det_ZTF18aaveorp = pd.read_csv(os.path.join(EXAMPLES_PATH, 'ZTF18aaveorp_det.csv'), index_col="oid")
        det_ZTF18aaveorp = preprocess_ztf.preprocess(raw_det_ZTF18aaveorp)

        keys = ['mjd', 'fid', 'magpsf_corr', 'sigmapsf_corr', 'isdiffpos']
        self.detections = pd.concat(
            [det_ZTF17aaaaaxg[keys],
             det_ZTF18abvvcko[keys],
             det_ZTF18abakgtm[keys],
             det_ZTF18aaveorp[keys]],
            axis=0
        )

        non_det_keys = ["diffmaglim", "mjd", "fid"]
        self.non_detections = pd.concat(
            [
                raw_nondet_ZTF17aaaaaxg[non_det_keys],
                raw_nondet_ZTF18abakgtm[non_det_keys],
                raw_nondet_ZTF18abvvcko[non_det_keys]
            ],
            axis=0
        )
        self.just_one_non_detection = raw_nondet_ZTF17aaaaaxg[non_det_keys].iloc[[0]]

    def test_many_objects(self):
        sn_extractor = SupernovaeDetectionAndNonDetectionFeatureExtractor()
        sn_results = sn_extractor.compute_features(
            self.detections,
            non_detections=self.non_detections)
        print(sn_results)
        self.assertEqual(
            (4, 2 * len(sn_extractor.get_features_keys())),
            sn_results.shape)

    def test_just_one_non_detection(self):
        sn_extractor = SupernovaeDetectionAndNonDetectionFeatureExtractor()
        sn_results = sn_extractor.compute_features(
            self.detections,
            non_detections=self.just_one_non_detection)
        self.assertEqual(
            (4, 2 * len(sn_extractor.get_features_keys())),
            sn_results.shape)


if __name__ == '__main__':
    unittest.main()
