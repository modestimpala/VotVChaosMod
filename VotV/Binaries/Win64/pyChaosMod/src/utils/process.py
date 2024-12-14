import psutil


def is_already_running():
    current_process = psutil.Process()
    current_pid = current_process.pid
    current_create_time = current_process.create_time()
    time_tolerance = 2  # 2 seconds of wiggle room

    for process in psutil.process_iter(['name', 'pid', 'create_time', 'cmdline']):
        if process.pid == current_pid:
            continue
        try:
            if process.name().lower() == "chaosbot.exe":
                if current_create_time - process.create_time() > time_tolerance:
                    return True
            if process.name().lower() in ["python.exe", "python"]:
                cmdline = process.cmdline()
                if len(cmdline) > 1 and "chaosbot.py" in cmdline[1].lower():
                    if current_create_time - process.create_time() > time_tolerance:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False