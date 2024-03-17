import subprocess

def start_in_tmux(cmd, session_name, window_name, root_dir):
    """
    Starts a command in a new or existing tmux session and window.

    Args:
        cmd (str): The command to be executed.
        session_name (str): The name of the tmux session.
        window_name (str): The name of the tmux window.
        root_dir (str): The root directory where the command should be executed.

    Returns:
        None
    """
    CMD_UNSET_PROXY = "unset http_proxy; unset https_proxy; export CUDA_VISIBLE_DEVICES=4"
    cmd = f"cd {root_dir} && {CMD_UNSET_PROXY} && {cmd}"
    print(cmd)
    
    def run_tmux_command(command):
        subprocess.run(command, shell=True)
    
    def tmux_has_session(name):
        result = subprocess.run(['tmux', 'has-session', '-t', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    
    def tmux_list_windows(name):
        result = subprocess.run(['tmux', 'list-windows', '-t', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    
    if not tmux_has_session(session_name):
        run_tmux_command(f"tmux new-session -d -s {session_name} -n {window_name}")
        run_tmux_command(f"tmux send-keys -t {session_name}:0 '{cmd}' C-m")
    else:
        if window_name not in tmux_list_windows(session_name):
            run_tmux_command(f"tmux new-window -t {session_name} -n {window_name}")
            run_tmux_command(f"tmux send-keys -t {session_name}:{window_name} '{cmd}' C-m")
        else:
            print(f"Window {window_name} already exists in session {session_name}. Recreating window.")
            run_tmux_command(f"tmux kill-window -t {session_name}:{window_name}")
            run_tmux_command(f"tmux new-window -t {session_name} -n {window_name}")
            run_tmux_command(f"tmux send-keys -t {session_name}:{window_name} '{cmd}' C-m")

# Example usage
if __name__ == "__main__":
    start_in_tmux("echo Hello, World!", "my_session", "my_window", "/home/user/projects")
