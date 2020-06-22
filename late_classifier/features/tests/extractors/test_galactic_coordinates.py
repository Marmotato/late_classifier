import unittest
import os
import pandas as pd
from late_classifier.features import GalacticCoordinatesExtractor
from late_classifier.features import DetectionsPreprocessorZTF


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_PATH = os.path.abspath(os.path.join(FILE_PATH, "../data"))


class TestGalacticCoordinates(unittest.TestCase):
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

        keys = ['ra', 'dec']
        self.detections = pd.concat(
            [det_ZTF17aaaaaxg[keys],
             det_ZTF18abvvcko[keys],
             det_ZTF18abakgtm[keys],
             det_ZTF18aaveorp[keys]],
            axis=0
        )

    def test_many_objects(self):
        galactic_extractor = GalacticCoordinatesExtractor()
        galactic_coordinates = galactic_extractor.compute_features(self.detections)
        self.assertEqual(galactic_coordinates.shape, (4, 2))


if __name__ == '__main__':
    unittest.main()
