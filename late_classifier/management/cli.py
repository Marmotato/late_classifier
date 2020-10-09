import click
import os

CLI_PATH = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.abspath(os.path.join(CLI_PATH, "../features/"))
TEST_PATH = os.path.abspath(os.path.join(CLI_PATH, "../../tests/"))
TEMPLATE_PATH = os.path.abspath(os.path.join(CLI_PATH, "templates/"))


@click.group()
def cli():
    pass


@cli.command()
@click.argument('detections_dir', type=click.Path(exists=True))
@click.argument('output_dir', default="features", type=click.Path())
@click.option('-n', 'non_detections_dir', type=click.Path(exists=True),
              help="Path to non-detection(s)  file(s). Valid extension [csv, pkl, parquet]")
@click.option("-ex", type=click.STRING, help="Extractor to execute.", default=None)
def compute_features(detections_dir, non_detections_dir, output_dir, ex):
    import late_classifier.features.extractors as extractor
    from late_classifier.management.helpers import iodf, iodir
    from late_classifier.features import DetectionsPreprocessorZTF

    detections = iodf.merge_df(detections_dir)
    iodir.exists_dir(output_dir)
    ztf_v2 = DetectionsPreprocessorZTF()
    detections_preprocess = ztf_v2.preprocess(detections)
    a = extractor.ColorFeatureExtractor().compute_features(detections_preprocess)
    """for file in detections_files:
        filename = iodir.get_filename(file)
        data = iodf.read_file(file, index_col="oid")
        data = ztf_v2.preprocess(data)
        features = extractor.features_mapping["color_feature"].compute_features(data, non_detections=None)
        iodf.write_file(features, os.path.join(output_dir, f"{filename}_features_color.csv"))"""


@cli.command()
@click.argument('detections_dir', type=click.Path(exists=True))
@click.argument('output_dir', default="preprocess", type=click.Path())
@click.option('-t', '--type-preprocess', default=None, help="Type of preprocess, i.e 'ztf' for preprocess ZTF's data")
def preprocess(detections_dir, output_dir, type_preprocess):
    from late_classifier.management.helpers import iodf, iodir
    from late_classifier.features import DetectionsPreprocessorZTF
    detections_files = iodir.list_files(detections_dir)
    iodir.exists_dir(output_dir)
    type_preprocess = type_preprocess.lower() if type_preprocess is not None else "all"

    ztf_v1 = DetectionsPreprocessorZTF()

    for file in detections_files:
        filename = iodir.get_filename(file)
        data = iodf.read_file(file, index_col="oid")
        iodf.write_file(ztf_v1.preprocess(data), os.path.join(output_dir, f"{filename}_preprocess_ztf_v1.csv"))


@cli.command()
@click.argument('name', type=click.STRING)
@click.option('-s', '--single-band', type=click.BOOL, default=False, help="Create a single band feature extractor.")
def create_extractor(name, single_band):
    import re
    from jinja2 import FileSystemLoader, Environment

    name = name.lower()
    class_name = "".join([word.capitalize() for word in re.split("_|\s|-|\||;|\.|,", name)])

    loader = FileSystemLoader(TEMPLATE_PATH)
    route = Environment(loader=loader)

    with open(os.path.join(os.path.join(FEATURES_PATH, "extractors"), f"{name}_extractor.py"), "w") as f:
        init_template = route.get_template("extractor_code")
        f.write(init_template.render(extractor_name=class_name))

    with open(os.path.join(os.path.join(TEST_PATH, "features", "extractors"), f"{name}_extractor_test.py"), "w") as f:
        init_template = route.get_template("extractor_test")
        f.write(init_template.render(extractor_name=class_name, formal_name=name))

    print(f"Create extractor: {name}. Please fill with the feature extractor logic.")


@cli.command()
def run_tests():
    print("Code for run tests...")


if __name__ == '__main__':
    cli()

