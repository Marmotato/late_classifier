from late_classifier.features.core.base import FeatureExtractor


class MyFeature(FeatureExtractor):
    def __init__(self):
        super().__init__()
        self.features_keys = []
        self.required_keys = []

    def compute_features(self, detections, **kwargs):
        """
        Parameters
        ----------
        detections :class:pandas.`DataFrame`
        DataFrame with detections of an object.

        kwargs Not required.

        Returns :class:pandas.`DataFrame`
        -------
        """
        ################################
        #   Here comes the Step Logic  #
        ################################
        return