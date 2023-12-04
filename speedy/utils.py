from speedy.imports import *

AV_CACHE_DIR = osp.join(osp.expanduser('~'), '.cache/av')
ICACHE = dict()


def mkdir_or_exist(dir_name):
    return os.makedirs(dir_name, exist_ok=True)


def dump_json_or_pickle(obj, fname, ensure_ascii=False):
    """
        Dump an object to a file, support both json and pickle
    """
    mkdir_or_exist(osp.abspath(os.path.dirname(osp.abspath(fname))))
    if fname.endswith('.json') or fname.endswith('.jsonl'):
        with open(fname, 'w') as f:
            json.dump(obj, f, ensure_ascii=ensure_ascii)
    elif fname.endswith('.pkl'):
        with open(fname, 'wb') as f:
            pickle.dump(obj, f)
    else:
        raise NotImplemented(fname)
import time

def timef(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} took {execution_time:0.2f} seconds to execute.")
        return result
    return wrapper


def load_json_or_pickle(fname):
    """
        Load an object from a file, support both json and pickle
    """
    if fname.endswith('.json') or fname.endswith('.jsonl'):
        with open(fname, 'r') as f:
            return json.load(f)
    else:
        with open(fname, 'rb') as f:
            return pickle.load(f)

def load_by_ext(fname, do_memoize=False, **pd_kwargs):
    def load_csv_csv(path):
        import pandas as pd
        return pd.read_csv(path, **pd_kwargs)

    def load_txt(path):
        with open(path, 'r') as f:
            return f.read().splitlines()

    
    def load_default(path):
        def _load_jsonl_by_line(path):
            lines = [json.loads(_) for _ in open(path).read().splitlines()]
            return lines
        if path.endswith('.jsonl'):
            try:
                return load_json_or_pickle(path)
            except:
                return _load_jsonl_by_line(path)
        return load_json_or_pickle(path)
    
        
    handlers = {
        '.csv': load_csv_csv,
        '.tsv': load_csv_csv,
        '.txt': load_txt,
        '.pkl': load_default,
        '.json': load_default,
        '.jsonl': load_default
    }

    ext = os.path.splitext(fname)[-1]  # Get file extension
    load_fn = handlers.get(ext)

    if not load_fn:
        raise NotImplementedError(f"File type {ext} not supported")

    if do_memoize:
        load_fn = memoize(load_fn)

    return load_fn(fname)


def identify(x):
    '''Return an hex digest of the input'''
    return xxhash.xxh64(pickle.dumps(x), seed=0).hexdigest()




def memoize(func, ignore_self=True, cache_dir=AV_CACHE_DIR, cache_type='.pkl', verbose=False, cache_key=None):
    '''Cache result of function call on disk
    Support multiple positional and keyword arguments'''
    assert cache_type in ['.pkl', '.json']

    @wraps(func)
    def memoized_func(*args, **kwargs):
        try:
            arg_names = inspect.getfullargspec(func).args
            func_source = inspect.getsource(func)
            func_source = func_source.replace(' ','')
            if cache_key is not None:
                logger.info(f'Use cache_key={kwargs[cache_key]}')
                func_id = identify(
                    (func_source), kwargs[cache_key])

            if len(arg_names) > 0 and arg_names[0] == 'self' and ignore_self:
                func_id = identify((func_source, args[1:], kwargs))
            else:
                func_id = identify((func_source, args, kwargs))

            cache_path = os.path.join(
                cache_dir, 'funcs', func.__name__+'/'+func_id+cache_type)
            mkdir_or_exist(os.path.dirname(cache_path))
            if os.path.exists(cache_path):
                if verbose:
                    logger.info(f'Load from cache file: {cache_path}')
                result = load_json_or_pickle(cache_path)
            else:

                result = func(*args, **kwargs)
                # pickle.dump(result, open(cache_path, 'wb'))
                dump_json_or_pickle(result, cache_path)
            return result
        except (KeyError, AttributeError, TypeError, Exception) as e:
            import traceback
            traceback.print_exc()

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



# def multi_thread(func, call_args_list, pbar='tqdm', n_workers=16):
#     """
#     Execute a given function concurrently using multiple threads.

#     Args:
#         func (callable): The function to be executed concurrently.
#         call_args_list (list): A list of argument dictionaries or tuples to call the function with.
#             Each element of the list should correspond to the arguments required by the function.
#             If a tuple, the values are matched with the function's positional arguments.
#             If a dictionary, the keys should correspond to function's argument names.
#         pbar (str or None, optional): Progress bar library to use. Options are 'tqdm' or None.
#             'tqdm' shows a progress bar. Default is 'tqdm'.
#         n_workers (int, optional): Number of worker threads to use. Default is 4.

#     Returns:
#         list: A list of results obtained from executing the function concurrently.

#     Example:
#         # Define a function
#         def add_numbers(a, b):
#             return a + b

#         # Create a list of argument tuples
#         args_list = [(1, 2), (3, 4), (5, 6)]
#         or list of dictionaries

#         args_list = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}, {'a': 5, 'b': 6}]

#         # Call the multi_thread function to execute add_numbers concurrently
#         results = multi_thread(add_numbers, args_list, pbar='tqdm', n_workers=2)
#         print(results)  # Output: [3, 7, 11]
#     """
#     real_func = func.__dict__.get('__wrapped__', func)
#     key_args = inspect.getfullargspec(real_func).args
#     key_kwargs = inspect.getfullargspec(real_func).kwonlyargs

#     if len(key_args)+len(key_kwargs) == 1:
#         call_args_list = [[_] for _ in call_args_list]

#     def wrapper(call_args):
#         # is list or tuple
#         if isinstance(call_args, (list, tuple)):
#             call_args = dict(zip(key_args, call_args))
#         return func(**call_args)

#     def tqdm_updater(future, pbar):
#         # try:
#         result = future.result()
#         with pbar.get_lock():
#             pbar.update(1)
#         return result

#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
#         if pbar:
#             with tqdm(total=len(call_args_list)) as pbar:
#                 future_to_args = {executor.submit(
#                     wrapper, args): args for args in call_args_list}
#                 for future in concurrent.futures.as_completed(future_to_args):
#                     result = tqdm_updater(future, pbar)
#                     results.append(result)
#         else:
#             for result in executor.map(wrapper, call_args_list):
#                 results.append(result)

#     return results


def multi_process_executor(args):
    global _global_function_to_execute  # using a global variable to store the function to be executed
    # If args is a tuple, unpack it to send multiple parameters to the function
    if isinstance(args, tuple):
        return _global_function_to_execute(*args)
    return _global_function_to_execute(args)

def flatten_list(list_of_lists):
    """
    Flatten a list of lists into a single list.

    Parameters:
    - list_of_lists (list of lists): The list to flatten.

    Returns:
    - list: A flattened list.
    """
    return [item for sublist in list_of_lists for item in sublist]


def multi_process(f, inputs, n_workers=16, desc='', verbose=True):
    if os.environ.get('DEBUG', '0') == '1':
        logger.info('DEBUGING set num worker to 1')
        n_workers = 1
    global _global_function_to_execute  # set the global variable to the function to be executed
    _global_function_to_execute = f
    
    logger.info('Multi processing {} | Num samples: {}', f.__name__, len(inputs))
    
    pbar = tqdm(total=len(inputs), desc=desc, disable=not verbose)
    
    results = []
    with Pool(n_workers) as p:
        try:
            for result in p.imap(multi_process_executor, inputs):
                results.append(result)
                pbar.update()
        except Exception as e:
            logger.error("Error occurred: {}", e)
        finally:
            pbar.close()
    
    return results

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
import inspect

def get_arg_names(func):
    return inspect.getfullargspec(func).args

def memoize_v2(keys):
    def decorator_memoize_v2(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            assert isinstance(keys, (list, tuple))
            arg_names = get_arg_names(func)
            # if not isinstance(keys, list):
            #     keys = [keys]
            def get_key_value(key):
                # k = kwargs.get(key) if key in kwargs else next((arg for arg in args if isinstance(arg, str)), None)
                if key in arg_names:
                    return args[arg_names.index(key)]
                if key in kwargs:
                    return kwargs[key]
            
            values = [get_key_value(key) for key in keys]

            # If no valid key, simply run the function
            if keys is None:
                return func(*args, **kwargs)

            key_id = identify(values)  # Assuming 'identify' generates a unique hash
            func_id = identify(inspect.getsource(func))
            key_names = '_'.join(keys)
            cache_path = osp.join(AV_CACHE_DIR, f'{func.__name__}_{func_id}', f'{key_names}_{key_id}.pkl')
            if osp.exists(cache_path):
                return load_json_or_pickle(cache_path)
            result = func(*args, **kwargs)
            dump_json_or_pickle(result, cache_path)
            return result
        return wrapper
    return decorator_memoize_v2
import sys

def is_interactive():
    try:
        # This will be True in Jupyter notebooks and IPython environments
        get_ipython
        return True
    except NameError:
        # Check if the script is run with arguments or as a standalone script
        return len(sys.argv) == 1


def set_trace_by_rank(rank=0):
    local_rank = int(os.environ.get('LOCAL_RANK', '-1'))
    if local_rank == rank:
        return ipdb.set_trace