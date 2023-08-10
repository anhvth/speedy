from speedy.imports import *
from speedy.utils import *

def read_json(fname):
    with open(fname, 'r') as f:
        return json.load(f)
    
def load_json(fname):
    mkdir_or_exist(os.path.dirname(fname))
    with open(fname, 'r') as f:
        return json.load(f)