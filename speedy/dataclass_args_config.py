import dataclasses
from dataclasses import dataclass
import argparse
from typing import List
from tabulate import tabulate

@dataclass
class CommandLineArgs:
    # This class will be extended to define specific arguments
    def __repr__(self):
        # use tabulate to print out the arguments
        return tabulate(
            [
                [field.name, field.type, getattr(self, field.name)]
                for field in dataclasses.fields(self)
            ],
            headers=["Argument", "Type", "Value"],
            tablefmt="orgtbl",
        )
    def __str__(self):
        return self.__repr__()

class GenericArgumentParser:
    def __init__(self, arg_class: CommandLineArgs, args_dict=None):
        if args_dict is not None:
            self.args = arg_class(**args_dict)
        else:
            self.args = self.parse_arguments(arg_class)

    @staticmethod
    def parse_arguments(arg_class) -> CommandLineArgs:
        parser = argparse.ArgumentParser(description="Generic Argument Parser")
        for field in dataclasses.fields(arg_class):
            arg_type = field.type
            default = (
                field.default
                if not dataclasses.is_dataclass(field.default)
                else field.default_factory()
            )
            if arg_type == List[int]:  # Special handling for nargs
                parser.add_argument(
                    f"--{field.name}",
                    nargs="+",
                    type=int,
                    default=default,
                    help=f"{field.name} argument",
                )
            else:
                parser.add_argument(
                    f"--{field.name}",
                    type=arg_type,
                    required=default is dataclasses.MISSING,
                    default=default,
                    help=f"{field.name} argument",
                )
        try:
            args = parser.parse_args()
        # if in jupyternotebook we just parse known args
        except SystemExit:
            args = parser.parse_known_args()[0]
        return arg_class(**vars(args))

    def get_arguments(self) -> CommandLineArgs:
        return self.args
