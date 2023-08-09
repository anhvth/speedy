from math import factorial
from speedy import multi_thread
import time

import threading
import time

# Shared resource (file) and a lock to manage access
shared_file = "shared_data.txt"
file_lock = threading.Lock()

# Function to simulate a time-consuming read/write task
def write_to_file(data):
    with file_lock:
        with open(shared_file, "a") as f:
            f.write(data + "\n")
        time.sleep(1)  # Simulate a time-consuming write

def read_from_file(*args, **kwargs):
    # with file_lock:
    with open(shared_file, "r") as f:
        content = f.read()
    time.sleep(1)  # Simulate a time-consuming read
    return content

# Create a list of data to write
data_to_write = ["Hello", "World", "Multi-Threading", "Example"]

# Write data to the file sequentially and measure time taken
start_time = time.time()
for data in data_to_write:
    write_to_file(data)
sequential_write_time = time.time() - start_time

# Create a list of dictionaries containing call arguments for multi-threading
call_args_list = [{"data": data} for data in data_to_write]

# Write data to the file using multi-threading and measure time taken
start_time = time.time()
multi_thread(write_to_file, call_args_list, pbar='tqdm', n_workers=2)
multi_thread_write_time = time.time() - start_time

# Read data from the file sequentially and measure time taken
start_time = time.time()
sequential_read_content = read_from_file()
sequential_read_time = time.time() - start_time

# Read data from the file using multi-threading and measure time taken
start_time = time.time()
multi_thread_results = multi_thread(read_from_file, call_args_list, pbar='tqdm', n_workers=4)
multi_thread_read_time = time.time() - start_time

# Print the time taken
print("Sequential Write Time:", sequential_write_time, "seconds")
print("Multi-thread Write Time:", multi_thread_write_time, "seconds")

print("Sequential Read Time:", sequential_read_time, "seconds")
print("Multi-thread Read Time:", multi_thread_read_time, "seconds")
