from speedy.imports import *
from speedy.utils import *

def read_json(fname):
    with open(fname, 'r') as f:
        return json.load(f)
    
def write_json(fname, data):
    os.makedirs(os.path.normpath(os.path.dirname(fname)), exist_ok=True)
    with open(fname, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)