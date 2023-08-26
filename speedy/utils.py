from speedy.imports import *

AV_CACHE_DIR = osp.join(osp.expanduser('~'), '.cache/av')
ICACHE = dict()


def mkdir_or_exist(dir_name):
    return os.makedirs(dir_name, exist_ok=True)


def dump_json_or_pickle(obj, fname):
    """
        Dump an object to a file, support both json and pickle
    """
    mkdir_or_exist(os.path.dirname(fname))
    if fname.endswith('.json'):
        with open(fname, 'w') as f:
            json.dump(obj, f)
    else:
        with open(fname, 'wb') as f:
            pickle.dump(obj, f)


def load_json_or_pickle(fname):
    """
        Load an object from a file, support both json and pickle
    """
    if fname.endswith('.json'):
        with open(fname, 'r') as f:
            return json.load(f)
    else:
        with open(fname, 'rb') as f:
            return pickle.load(f)


def identify(x):
    '''Return an hex digest of the input'''
    return xxhash.xxh64(pickle.dumps(x), seed=0).hexdigest()


def memoize(func):
    '''Cache result of function call on disk
    Support multiple positional and keyword arguments'''
    @wraps(func)
    def memoized_func(*args, **kwargs):
        try:
            if 'cache_key' in kwargs:
                cache_key = kwargs['cache_key']

                func_id = identify((inspect.getsource(func))) + \
                    '_cache_key_'+str(kwargs['cache_key'])
            else:
                func_id = identify((inspect.getsource(func), args, kwargs))
            cache_path = os.path.join(
                AV_CACHE_DIR, 'funcs', func.__name__+'/'+func_id)
            mkdir_or_exist(os.path.dirname(cache_path))

            if (os.path.exists(cache_path) and
                    not func.__name__ in os.environ and
                    not 'BUST_CACHE' in os.environ):
                result = pickle.load(open(cache_path, 'rb'))
            else:
                result = func(*args, **kwargs)
                pickle.dump(result, open(cache_path, 'wb'))
            return result
        except (KeyError, AttributeError, TypeError, Exception) as e:
            logger.warning(f'Exception: {e}, use default function call')
            return func(*args, **kwargs)
    return memoized_func


def imemoize(func):
    """
        Memoize a function into memory, the function recaculate only 
        change when its belonging arguments change
    """
    @wraps(func)
    def _f(*args, **kwargs):
        ident_name = identify((inspect.getsource(func), args, kwargs))
        try:
            result = ICACHE[ident_name]
        except:
            result = func(*args, **kwargs)
            ICACHE[ident_name] = result
        return result
    return _f




def multi_thread(func, call_args_list, pbar='tqdm', n_workers=4):
    """
    Execute a given function concurrently using multiple threads.

    Args:
        func (callable): The function to be executed concurrently.
        call_args_list (list): A list of argument dictionaries or tuples to call the function with.
            Each element of the list should correspond to the arguments required by the function.
            If a tuple, the values are matched with the function's positional arguments.
            If a dictionary, the keys should correspond to function's argument names.
        pbar (str or None, optional): Progress bar library to use. Options are 'tqdm' or None.
            'tqdm' shows a progress bar. Default is 'tqdm'.
        n_workers (int, optional): Number of worker threads to use. Default is 4.

    Returns:
        list: A list of results obtained from executing the function concurrently.

    Example:
        # Define a function
        def add_numbers(a, b):
            return a + b

        # Create a list of argument tuples
        args_list = [(1, 2), (3, 4), (5, 6)]
        or list of dictionaries
        
        args_list = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}, {'a': 5, 'b': 6}]
        
        # Call the multi_thread function to execute add_numbers concurrently
        results = multi_thread(add_numbers, args_list, pbar='tqdm', n_workers=2)
        print(results)  # Output: [3, 7, 11]
    """
    key_args = inspect.getfullargspec(func).args
    key_kwargs = inspect.getfullargspec(func).kwonlyargs
    
    def wrapper(call_args):
        # is list or tuple
        if isinstance(call_args, (list, tuple)):
            call_args = dict(zip(key_args, call_args))
        return func(**call_args)
    
    # Function to update tqdm progress in a thread-safe manner
    def tqdm_updater(future, pbar):
        try:
            result = future.result()
            with pbar.get_lock():
                pbar.update(1)
            return result
        except Exception as e:
            with pbar.get_lock():
                pbar.update(1)
            return e

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        if pbar:
            with tqdm(total=len(call_args_list)) as pbar:
                future_to_args = {executor.submit(wrapper, args): args for args in call_args_list}
                for future in concurrent.futures.as_completed(future_to_args):
                    result = tqdm_updater(future, pbar)
                    results.append(result)
        else:
            for result in executor.map(wrapper, call_args_list):
                results.append(result)

    return results

def multi_process(f, inputs, n_workers=16, desc='', verbose=True):
    logger.info('Multi processing {} | Num samples: {}', f.__name__, len(inputs))
    pbar = tqdm(total=len(inputs), desc=desc)
        
    with Pool(n_workers) as p:
        it = p.imap(f, inputs)
        return_list = []
        for i, ret in enumerate(it):
            return_list.append(ret)
            pbar.update()
    return return_list

def pp(input, key_ignore=None, max_width=100, **kwargs):
    """
        Pretty print
    """
    import pprint
    if hasattr(input, 'to_dict'):
        input = input.to_dict()
    if key_ignore is not None:
        for key in key_ignore:
            input.pop(key, None)
    pprint.pprint(input, width=max_width, **kwargs)