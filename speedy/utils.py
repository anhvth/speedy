from speedy.imports import *

AV_CACHE_DIR = osp.join(osp.expanduser("~"), ".cache/av")
ICACHE = dict()


def mkdir_or_exist(dir_name):
    return os.makedirs(dir_name, exist_ok=True)

def dump_jsonl(list_dictionaries, file_name="output.jsonl"):
    """
    Dumps a list of dictionaries to a file in JSON Lines format.

    Parameters:
    - list_dictionaries (list): A list of dictionaries to be written to the file.
    - file_name (str, optional): The name of the output file. Defaults to "output.jsonl".
    """
    # Open or create the file with the specified file_name in write mode
    with open(file_name, 'w', encoding='utf-8') as file:
        # Iterate over each dictionary in the list
        for dictionary in list_dictionaries:
            # Dump the dictionary to a JSON string and write it to the file followed by a newline
            file.write(json.dumps(dictionary, ensure_ascii=False) + '\n')


def dump_json_or_pickle(obj, fname, ensure_ascii=False):
    """
    Dump an object to a file, support both json and pickle
    """
    mkdir_or_exist(osp.abspath(os.path.dirname(osp.abspath(fname))))
    if fname.endswith(".json"):
        with open(fname, "w") as f:
            json.dump(obj, f, ensure_ascii=ensure_ascii)
    elif fname.endswith(".jsonl"):
        dump_jsonl(obj, fname)
    elif fname.endswith(".pkl"):
        with open(fname, "wb") as f:
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
    if fname.endswith(".json") or fname.endswith(".jsonl"):
        with open(fname, "r") as f:
            return json.load(f)
    else:
        with open(fname, "rb") as f:
            return pickle.load(f)


def load_by_ext(fname, do_memoize=False, **pd_kwargs):
    try:
        if "*" in fname:
            paths = glob(fname)
            paths = list(sorted(paths))
            return multi_process(load_by_ext, paths, n_workers=16)
        elif isinstance(fname, list):
            paths = fname
            return multi_process(load_by_ext, paths, n_workers=16)

        def load_csv_csv(path, **pd_kwargs):
            import pandas as pd

            return pd.read_csv(path, engine="pyarrow", **pd_kwargs)

        def load_txt(path):
            with open(path, "r") as f:
                return f.read().splitlines()

        def load_default(path):
            def _load_jsonl_by_line(path):
                lines = [json.loads(_) for _ in open(path).read().splitlines()]
                return lines

            if path.endswith(".jsonl") or path.endswith(".json"):
                try:
                    return load_json_or_pickle(path)
                except:
                    return _load_jsonl_by_line(path)
            return load_json_or_pickle(path)

        handlers = {
            ".csv": load_csv_csv,
            ".tsv": load_csv_csv,
            ".txt": load_txt,
            ".pkl": load_default,
            ".json": load_default,
            ".jsonl": load_default,
        }

        ext = os.path.splitext(fname)[-1]  # Get file extension
        load_fn = handlers.get(ext)

        if not load_fn:
            raise NotImplementedError(f"File type {ext} not supported")

        if do_memoize:
            load_fn = memoize(load_fn)

        return load_fn(fname)
    except Exception as e:
        raise f"Error {e} while loading {fname}"


def identify(x):
    """Return an hex digest of the input"""
    return xxhash.xxh64(pickle.dumps(x), seed=0).hexdigest()


def memoize(
    func,
    ignore_self=True,
    cache_dir=AV_CACHE_DIR,
    cache_type=".pkl",
    verbose=False,
    cache_key=None,
):
    """Cache result of function call on disk
    Support multiple positional and keyword arguments"""
    assert cache_type in [".pkl", ".json"]
    if os.environ.get("AV_MEMOIZE_DISABLE", "0") == "1":
        logger.info("Memoize is disabled")
        return func
    @wraps(func)
    def memoized_func(*args, **kwargs):
        try:
            arg_names = inspect.getfullargspec(func).args
            func_source = inspect.getsource(func)
            func_source = func_source.replace(" ", "")
            if cache_key is not None:
                logger.info(f"Use cache_key={kwargs[cache_key]}")
                func_id = identify((func_source), kwargs[cache_key])

            if len(arg_names) > 0 and arg_names[0] == "self" and ignore_self:
                func_id = identify((func_source, args[1:], kwargs))
            else:
                func_id = identify((func_source, args, kwargs))

            cache_path = os.path.join(
                cache_dir, "funcs", func.__name__ + "/" + func_id + cache_type
            )
            mkdir_or_exist(os.path.dirname(cache_path))
            if os.path.exists(cache_path):
                if verbose:
                    logger.info(f"Load from cache file: {cache_path}")
                result = load_json_or_pickle(cache_path)
            else:
                result = func(*args, **kwargs)
                # pickle.dump(result, open(cache_path, 'wb'))
                dump_json_or_pickle(result, cache_path)
            return result
        except (KeyError, AttributeError, TypeError, Exception) as e:
            print('============')
            import traceback
            traceback.print_exc()
            print('============')

            logger.warning(f"Exception: {e}, use default function call")
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


import functools


def imemoize_v2(keys):
    """
    Memoize a function into memory, the function recalculates only
    when its specified arguments change (determined by `keys`).
    """

    def decorator_imemoize_v2(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            assert isinstance(keys, (list, tuple))

            # Building a dictionary containing all arguments by their name
            arg_names = inspect.getfullargspec(func).args
            args_dict = dict(zip(arg_names, args))
            all_args = {**args_dict, **kwargs}

            # Extract the values of the specified keys only
            key_values = {key: all_args[key] for key in keys if key in all_args}
            if not key_values:
                return func(*args, **kwargs)

            # Generate a unique identifier for the combination of function and key values
            ident_name = identify((func.__name__, tuple(key_values.items())))

            # Attempt to retrieve the cached result
            try:
                result = ICACHE[ident_name]
            except KeyError:  # If not found, compute and store the result
                result = func(*args, **kwargs)
                ICACHE[ident_name] = result

            return result

        return wrapper

    return decorator_imemoize_v2


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


def multi_process(f, inputs, n_workers=16, desc="", verbose=True):
    if os.environ.get("DEBUG", "0") == "1":
        logger.info("DEBUGING set num worker to 1")
        n_workers = 1
    global _global_function_to_execute  # set the global variable to the function to be executed
    _global_function_to_execute = f

    logger.info("Multi processing {} | Num samples: {}", f.__name__, len(inputs))

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

    if hasattr(input, "to_dict"):
        input = input.to_dict()
    if key_ignore is not None:
        for key in key_ignore:
            input.pop(key, None)
    pprint.pprint(input, width=max_width, **kwargs)


import inspect


def get_arg_names(func):
    return inspect.getfullargspec(func).args


def memoize_v2(keys, cache_dir=AV_CACHE_DIR):
    def decorator_memoize_v2(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            assert isinstance(keys, (list, tuple))

            args_key_values = {}
            # merge args and kwargs
            for i, arg in enumerate(args):
                arg_name = get_arg_names(func)[i]

                args_key_values[arg_name] = arg
            for key, value in kwargs.items():
                args_key_values[key] = value

            values = []
            for key in keys:
                assert (
                    key in args_key_values
                ), f"Key {key} not found in {args_key_values.keys()}"
                v = args_key_values[key]
                values.append(v)
            if keys is None:
                return func(*args, **kwargs)

            key_id = identify(values)  # Assuming 'identify' generates a unique hash
            func_source = inspect.getsource(func)
            func_id = identify(func_source.replace(" ", ""))
            key_names = "_".join(keys)
            cache_path = osp.join(
                cache_dir, f"{func.__name__}_{func_id}", f"{key_names}_{key_id}.pkl"
            )
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
    local_rank = int(os.environ.get("LOCAL_RANK", "-1"))
    if local_rank == rank:
        return ipdb.set_trace


from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm


def multi_thread(func, inputs, workers=4, verbose=True):
    """
    Executes a function across multiple threads, distributing the inputs across the threads,
    with a progress bar indicating the completion status. Ensures results are ordered according
    to the order of inputs.

    Parameters:
    - func: The function to execute. This function should accept a single argument.
    - inputs: An iterable of inputs to be passed to the function.
    - workers: The number of threads to use. Default is 4.

    Returns:
    - A list of results obtained by applying the func to each item in inputs, with progress tracked via tqdm,
      ensuring that the output list is in the same order as the inputs.
    """
    # Initialize a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Use `submit` to start the operations and retain their order with futures
        futures = [executor.submit(func, inp) for inp in inputs]
        # Initialize an empty list to store results in order
        results = []

        if verbose:
            for future in tqdm(as_completed(futures), total=len(inputs), desc="Processing"):
                results.append(future.result())
        else:
            for future in as_completed(futures):
                results.append(future.result())

    # Since the futures are submitted and tracked in order, results are added in order.
    # However, `as_completed` will yield futures as they finish, so we adjust our approach below.

    # Instead of collecting results directly as they're completed, create an ordered list to match input order.
    ordered_results = [None] * len(inputs)
    # Map each future back to its original index
    for index, future in enumerate(futures):
        # Place the result into the corresponding position
        ordered_results[index] = future.result()
    
    return ordered_results



def print_table(data):
    # If the data is a string, attempt to parse it as JSON
    def __get_table(data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("String input could not be decoded as JSON")

        # If the data is a list, check if it contains dictionaries
        if isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                headers = list(
                    data[0].keys()
                )  # keys from the first dictionary as headers
                rows = [
                    list(item.values()) for item in data
                ]  # values of dictionaries as rows
                return tabulate(rows, headers=headers)
            else:
                raise ValueError("List must contain dictionaries")

        # If the data is a dictionary itself, display it as a table with two columns: keys and values
        if isinstance(data, dict):
            headers = ["Key", "Value"]
            rows = list(data.items())  # Convert items to list of tuples
            return print(tabulate(rows, headers=headers))

        # For any other case, raise an error
        raise TypeError(
            "Input data must be a list of dictionaries, a dictionary, or a JSON string"
        )

    table = __get_table(data)
    print(table)

class PydanticList(List[BaseModel]):
    def to_pandas(self):
        import pandas as pd
        return pd.DataFrame([_.model_dump_json() for _ in self])

def convert_to_builtin_python(input):
    if isinstance(input, dict):
        return {k: convert_to_builtin_python(v) for k, v in input.items()}
    elif isinstance(input, list):
        return [convert_to_builtin_python(v) for v in input]
    elif type(input) in [int, float, str, bool, type(None)]:
        return input
    elif isinstance(input, BaseModel):
        data = input.model_dump_json()
        return convert_to_builtin_python(data)
    else:
        raise ValueError(f"Unsupport type {type(input)}")