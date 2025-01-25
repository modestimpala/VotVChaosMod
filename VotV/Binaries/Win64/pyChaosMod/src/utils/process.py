import psutil
import os

def is_already_running():
    current_process = psutil.Process()
    current_pid = current_process.pid
    current_create_time = current_process.create_time()
    time_tolerance = 2  # 2 seconds of wiggle room
    
    try:
        for process in psutil.process_iter(['name', 'pid', 'create_time']):  # Removed 'cmdline' from initial query
            if process.pid == current_pid:
                continue
                
            try:
                proc_name = process.name().lower()
                
                # Check for chaosbot.exe
                if proc_name == "chaosbot.exe":
                    if abs(current_create_time - process.create_time()) > time_tolerance:
                        return True
                
                # Check for python running chaosbot.py
                elif proc_name in ["python.exe", "python"]:
                    try:
                        cmdline = process.cmdline()  # Only get cmdline for Python processes
                        if len(cmdline) > 1 and "chaosbot.py" in cmdline[1].lower():
                            if abs(current_create_time - process.create_time()) > time_tolerance:
                                return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
                        continue
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
                continue
                
    except Exception as e:
        print(f"Warning: Error checking for running instances: {str(e)}")
        return False  # On error, allow the program to run
        
    return False