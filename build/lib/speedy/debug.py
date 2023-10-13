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

    def __init__(self, port=5678):
        self.port = port
        self.setup()
        if not self.is_enable:
            from loguru import logger
            logger.warning('[VSCODE DEBUGGER IS IMPORTED BUT NOT USE]')

    def setup(self):
        import os
        self.is_enable = os.environ.get('DEBUG', False) == '1'
                
        if self.is_enable:
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