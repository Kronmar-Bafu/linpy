import argparse
import os
import pandas as pd
import yaml
import py_cube
from py_cube.frictionless import convert_frictionless_from_url
from py_cube.lindas.upload import upload_ttl
import logging

logger = logging.getLogger('pycube')


def serialize(input_directory: str, output_ttl: str, na_values: list[str], sep: str = ",", decimal: str = "."):
    csv_path = os.path.join(input_directory, "data.csv")
    yml_path = os.path.join(input_directory, "description.yml")
    json_path = os.path.join(input_directory, "description.json")

    if os.path.exists(yml_path):
        with open(yml_path) as file:
            cube_yaml = yaml.safe_load(file)
    elif os.path.exists(json_path):
        with open(json_path) as file:
            cube_yaml = yaml.safe_load(file)
    else:
        raise FileNotFoundError("Neither description.yml nor description.json found in the directory")

    df = pd.read_csv(csv_path, na_values=na_values, sep=sep, decimal=decimal)

    cube = py_cube.Cube(dataframe=df, cube_yaml=cube_yaml, environment="TEST", local=True)
    cube.prepare_data()
    cube.write_cube()
    cube.write_observations()
    cube.write_shape()
    cube.serialize(os.path.join(os.getcwd(), output_ttl))
    print(cube)


def configure_logging(log_level):
    class CustomFormatter(logging.Formatter):
        """Custom logging formatter to add colors based on log level."""

        COLORS = {
            'DEBUG': '\033[0m',  # Normal
            'INFO': '\033[94m',  # Blue
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',  # Red
            'CRITICAL': '\033[91m',  # Red
        }

        def format(self, record):
            log_fmt = self.COLORS.get(record.levelname, '\033[0m') + '%(levelname)s: %(message)s\033[0m'
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    console_handler = logging.StreamHandler()
    logger.setLevel(log_level)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cube data operations")
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    serialize_parser = subparsers.add_parser("serialize", help="Serialize cube data")
    serialize_parser.add_argument("input_directory", help="Directory containing the data files")
    serialize_parser.add_argument("output_ttl", help="Output TTL file")
    serialize_parser.add_argument("--na_value", nargs="+", help="Values to treat as NA")
    serialize_parser.add_argument("--sep", default=",", nargs="?", help="Separator for CSV file")
    serialize_parser.add_argument("--decimal", default=".", nargs="?", help="Decimal separator")
    serialize_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    frictionless_parser = subparsers.add_parser("frictionless", help="Converts a frictionless dataset")
    frictionless_parser.add_argument("input_url", type=str, help="The URL of the dataset to process")
    frictionless_parser.add_argument("output", type=str, help="The directory to save the output files")
    frictionless_parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose == 1 else logging.INFO

    configure_logging(log_level)

    if args.operation == "serialize":
        serialize(args.input_directory, args.output_ttl, args.na_value, args.sep, args.decimal)
    elif args.operation == "frictionless":
        convert_frictionless_from_url(args.input_url, args.output)