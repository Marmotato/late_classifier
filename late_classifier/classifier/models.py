import numpy as np
import pandas as pd
import os
import pickle
import wget
from imblearn.ensemble import BalancedRandomForestClassifier as RandomForestClassifier
from late_classifier.classifier.preprocessing import FeaturePreprocessor
from late_classifier.classifier.preprocessing import intersect_oids_in_dataframes
from abc import ABC, abstractmethod


MODEL_PATH = os.path.dirname(os.path.abspath(__file__))
PICKLE_PATH = os.path.join(MODEL_PATH, "pickles")


class BaseClassifier(ABC):
    @abstractmethod
    def fit(self, samples: pd.DataFrame, labels: pd.DataFrame) -> None:
        pass

    def predict(self, samples: pd.DataFrame) -> pd.DataFrame:
        probs = self.predict_proba(samples)
        predicted_class = probs.idxmax(axis=1)
        predicted_class_df = pd.DataFrame(
            predicted_class,
            columns=['classALeRCE'],
            index=samples.index)
        predicted_class_df.index.name = samples.index.name
        return predicted_class_df

    @abstractmethod
    def predict_proba(self, samples: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_list_of_classes(self) -> list:
        pass

    @abstractmethod
    def save_model(self, directory: str) -> None:
        pass

    @abstractmethod
    def load_model(self, directory: str) -> None:
        pass


def invert_dictionary(dictionary):
    inverted_dictionary = {}
    for top_group, list_of_classes in dictionary.items():
        for astro_class in list_of_classes:
            inverted_dictionary[astro_class] = top_group
    return inverted_dictionary


class BaselineRandomForest(BaseClassifier):
    def __init__(self):
        self.random_forest_classifier = RandomForestClassifier(
            n_estimators=500,
            max_features='auto',
            max_depth=None,
            n_jobs=1,
            class_weight=None,
            criterion='entropy',
            min_samples_split=2,
            min_samples_leaf=1)
        self.feature_preprocessor = FeaturePreprocessor()
        self.feature_list = None
        self.model_filename = 'baseline_rf.pkl'

    def fit(self, samples: pd.DataFrame, labels: pd.DataFrame):
        samples = self.feature_preprocessor.preprocess_features(samples)
        samples = self.feature_preprocessor.remove_duplicates(samples)

        # intersect samples and labels
        samples, labels = intersect_oids_in_dataframes(samples, labels)

        self.feature_list = samples.columns
        samples_np_array = samples.values
        labels_np_array = labels['classALeRCE'].loc[samples.index].values
        self.random_forest_classifier.fit(samples_np_array, labels_np_array)

    def predict_proba(self, samples: pd.DataFrame) -> pd.DataFrame:
        samples = self.feature_preprocessor.preprocess_features(samples)
        samples_np_array = samples[self.feature_list].values
        predicted_probs = self.random_forest_classifier.predict_proba(samples_np_array)
        predicted_probs_df = pd.DataFrame(
            predicted_probs,
            columns=self.get_list_of_classes(),
            index=samples.index.values
        )
        predicted_probs_df.index.name = 'oid'
        return predicted_probs_df

    def get_list_of_classes(self) -> list:
        return self.random_forest_classifier.classes_

    def save_model(self, directory: str) -> None:
        with open(os.path.join(directory, self.model_filename), 'wb') as f:
            pickle.dump(
                self.random_forest_classifier,
                f,
                pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(directory, 'feature_list.pkl'), 'wb') as f:
            pickle.dump(
                self.feature_list,
                f,
                pickle.HIGHEST_PROTOCOL)

    def load_model(self, directory: str) -> None:
        rf = pd.read_pickle(os.path.join(directory, self.model_filename))
        self.random_forest_classifier = rf
        self.feature_list = pd.read_pickle(
            os.path.join(directory, 'feature_list.pkl'))


class HierarchicalRandomForest(BaseClassifier):
    MODEL_NAME = "hierarchical_random_forest"
    MODEL_VERSION = "1.0.0"
    MODEL_VERSION_NAME = f"{MODEL_NAME}_{MODEL_VERSION}"
    MODEL_PICKLE_PATH =  os.path.join(PICKLE_PATH, f"{MODEL_VERSION_NAME}")

    def __init__(self, taxonomy_dictionary, non_used_features=None):
        n_trees = 500
        self.top_classifier = RandomForestClassifier(
            n_estimators=n_trees,
            max_depth=None,
            max_features='auto'
        )

        self.stochastic_classifier = RandomForestClassifier(
            n_estimators=n_trees,
            max_depth=None,
            max_features=0.2
        )

        self.periodic_classifier = RandomForestClassifier(
            n_estimators=n_trees,
            max_depth=None,
            max_features='auto'
        )

        self.transient_classifier = RandomForestClassifier(
            n_estimators=n_trees,
            max_depth=None,
            max_features='auto'
        )

        self.feature_preprocessor = FeaturePreprocessor(non_used_features=non_used_features)

        self.taxonomy_dictionary = taxonomy_dictionary
        self.feature_list = None
        self.inverted_dictionary = invert_dictionary(self.taxonomy_dictionary)
        self.pickles = {
            "features_list":"features_RF_model.pkl",
            "top_rf":"hierarchical_level_RF_model.pkl",
            "periodic_rf":"periodic_level_RF_model.pkl",
            "stochastic_rf":"stochastic_level_RF_model.pkl",
            "transient_rf":"transient_level_RF_model.pkl"
        }
        self.url_model = f"https://assets.alerce.online/pipeline/hierarchical_rf_{self.MODEL_VERSION}/"

    def fit(self, samples: pd.DataFrame, labels: pd.DataFrame) -> None:
        labels = labels.copy()

        # Check that the received labels are in the taxonomy
        feeded_labels = labels.classALeRCE.unique()
        expected_labels = self.inverted_dictionary.keys()

        for label in feeded_labels:
            if label not in expected_labels:
                raise Exception(f'{label} is not in the taxonomy dictionary')

        # Create top class
        labels['top_class'] = labels['classALeRCE'].map(self.inverted_dictionary)

        # Preprocessing
        samples = self.feature_preprocessor.preprocess_features(samples)
        samples = self.feature_preprocessor.remove_duplicates(samples)
        samples, labels = intersect_oids_in_dataframes(samples, labels)

        # Save list of features to know their order
        self.feature_list = samples.columns

        # Train top classifier
        self.top_classifier.fit(samples.values, labels['top_class'].values)

        # Train specialized classifiers
        is_stochastic = labels['top_class'] == 'Stochastic'
        self.stochastic_classifier.fit(
            samples[is_stochastic].values,
            labels[is_stochastic]['classALeRCE'].values
        )

        is_periodic = labels['top_class'] == 'Periodic'
        self.periodic_classifier.fit(
            samples[is_periodic].values,
            labels[is_periodic]['classALeRCE'].values
        )

        is_transient = labels['top_class'] == 'Transient'
        self.transient_classifier.fit(
            samples[is_transient].values,
            labels[is_transient]['classALeRCE'].values
        )

    def check_missing_features(self,columns, feature_list):
        missing = set(feature_list).difference(set(columns))
        return missing

    def predict_proba(self, samples: pd.DataFrame) -> pd.DataFrame:
        missing = self.check_missing_features(samples.columns, self.feature_list)
        if len(missing) > 0:
            raise Exception(f"Missing features: {missing}")

        samples = samples[self.feature_list]
        samples = self.feature_preprocessor.preprocess_features(samples)

        top_probs = self.top_classifier.predict_proba(samples.values)

        stochastic_probs = self.stochastic_classifier.predict_proba(samples.values)
        periodic_probs = self.periodic_classifier.predict_proba(samples.values)
        transient_probs = self.transient_classifier.predict_proba(samples.values)

        stochastic_index = self.top_classifier.classes_.tolist().index('Stochastic')
        periodic_index = self.top_classifier.classes_.tolist().index('Periodic')
        transient_index = self.top_classifier.classes_.tolist().index('Transient')

        stochastic_probs = stochastic_probs * top_probs[:, stochastic_index].reshape([-1, 1])
        periodic_probs = periodic_probs * top_probs[:, periodic_index].reshape([-1, 1])
        transient_probs = transient_probs * top_probs[:, transient_index].reshape([-1, 1])

        final_probs = np.concatenate(
            [stochastic_probs, periodic_probs, transient_probs],
            axis=1
        )

        df = pd.DataFrame(
            data=final_probs,
            index=samples.index,
            columns=self.get_list_of_classes()
        )
        df.index.name = samples.index.name
        return df

    def get_list_of_classes(self) -> list:
        final_columns = (
                self.stochastic_classifier.classes_.tolist()
                + self.periodic_classifier.classes_.tolist()
                + self.transient_classifier.classes_.tolist())
        return final_columns

    def save_model(self, directory: str) -> None:
        with open(os.path.join(directory, self.pickles['top_rf']), 'wb') as f:
            pickle.dump(
                self.top_classifier,
                f,
                pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(directory, self.pickles['stochastic_rf']), 'wb') as f:
            pickle.dump(
                self.stochastic_classifier,
                f,
                pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(directory, self.pickles['periodic_rf']), 'wb') as f:
            pickle.dump(
                self.periodic_classifier,
                f,
                pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(directory, self.pickles['transient_rf']), 'wb') as f:
            pickle.dump(
                self.transient_classifier,
                f,
                pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(directory, self.pickles['features_list']), 'wb') as f:
            pickle.dump(
                self.feature_list,
                f,
                pickle.HIGHEST_PROTOCOL)

    def load_model(self, directory: str) -> None:
        self.top_classifier = pd.read_pickle(
            os.path.join(directory, self.pickles['top_rf'] ))
        self.stochastic_classifier = pd.read_pickle(
            os.path.join(directory,  self.pickles['stochastic_rf']))
        self.periodic_classifier = pd.read_pickle(
            os.path.join(directory, self.pickles['periodic_rf']))
        self.transient_classifier = pd.read_pickle(
            os.path.join(directory, self.pickles['transient_rf']))
        self.feature_list = pd.read_pickle(
            os.path.join(directory, self.pickles['features_list']))

    def download_model(self):
        if not os.path.exists(self.MODEL_PICKLE_PATH):
            os.makedirs(self.MODEL_PICKLE_PATH)
        for pkl in self.pickles.values():
            tmp_path = os.path.join(self.MODEL_PICKLE_PATH, pkl)
            if not os.path.exists(tmp_path):
                command = f"wget {self.url_model}{pkl} -O {tmp_path}"
                wget.download(os.path.join(self.url_model, pkl), tmp_path)

    def predict_in_pipeline(self, input_features: pd.DataFrame) -> dict:
        if isinstance(input_features, pd.Series):
            input_features = input_features.to_frame().transpose()
        if len(input_features) != 1:
            raise ValueError('predict_in_pipeline receives features one by one')

        missing = self.check_missing_features(input_features.columns, self.feature_list)
        if len(missing) > 0:
            raise Exception(f"Missing features: {missing}")

        input_features = input_features[self.feature_list]

        input_features = self.feature_preprocessor.preprocess_features(input_features)
        prob_root = pd.DataFrame(
            self.top_classifier.predict_proba(input_features),
            columns=self.top_classifier.classes_,
            index=input_features.index
        )

        prob_children = []
        resp_children = {}

        child_models = [
            self.stochastic_classifier,
            self.periodic_classifier,
            self.transient_classifier
        ]
        child_names = [
            'Stochastic',
            'Periodic',
            'Transient'
        ]
        for name, model in zip(child_names, child_models):
            prob_child = pd.DataFrame(
                model.predict_proba(input_features),
                columns=model.classes_,
                index=input_features.index
            )

            resp_children[name] = prob_child.iloc[0].to_dict()
            prob_child = prob_child.mul(prob_root[name].values, axis="rows")
            prob_children.append(prob_child)
        prob_all = pd.concat(prob_children, axis=1, sort=False)

        return {
            "hierarchical": {
                "top": prob_root.iloc[0].to_dict(),
                "children": resp_children},
            "probabilities": prob_all.iloc[0].to_dict(),
            "class": prob_all.idxmax(axis=1).iloc[0]
        }
