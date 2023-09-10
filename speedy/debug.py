import argparse
import debugpy

class Debugger:
    """
    A utility class for setting up debugging in scripts.

    Usage:
    if __name__ == "__main__":
        main_parser = argparse.ArgumentParser(description='Main program arguments')
        main_parser.add_argument('--example-arg', help='An example argument for the main program')
        debugger = Debugger(parser=main_parser)
        debugger.setup()
        # Rest of your code
    """

    def __init__(self, parser=None, port=5678):
        if parser is None:
            parser = argparse.ArgumentParser(description='Debugger Argument Parser')
        self.parser = parser
        self.port = port
        self._add_arguments()
        self.setup()

    def _add_arguments(self):
        self.parser.add_argument('-db', action='store_true', help='Run with debugger attached')

    def setup(self, args=None):
        if args is None:
            args = self.parser.parse_args()

        if args.db:
            try:
                debugpy.listen(self.port)
                print(f"Waiting for debugger to attach on port {self.port}...")
                debugpy.wait_for_client()
                print("Debugger attached.")
            except Exception as e:
                print(f"Error setting up debugger: {e}")
        return self
    
    def set_trace(self):
        """Set a breakpoint at this point in the code."""
        debugpy.breakpoint()