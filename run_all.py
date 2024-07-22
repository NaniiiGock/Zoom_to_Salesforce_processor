import subprocess
import threading
import sys

def run_flask_app(app_file, port):
    process = subprocess.Popen(
        [sys.executable, app_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"FLASK_APP": app_file, "FLASK_RUN_PORT": str(port)},
        universal_newlines=True
    )
    def stream_output(stream, prefix):
        for line in stream:
            print(f"{prefix} {line}", end='')
    
    threading.Thread(target=stream_output, args=(process.stdout, f"[{app_file}] OUT:")).start()
    threading.Thread(target=stream_output, args=(process.stderr, f"[{app_file}] ERR:")).start()
    
    return process

def main():

    
    apps = [
        ("main.py", 8082),
        ("helpers/MeetingPeopleExtractor.py", 8081),
        ("helpers/SalesforceConnector.py", 8080),
        ("models/OpenIAClient.py", 8083)
    ]
    
    processes = []
    
    try:
        for app_file, port in apps:
            process = run_flask_app(app_file, port)
            processes.append(process)
        for process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\nStopping all Flask applications...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait()
        
        print("All Flask applications have been stopped.")

if __name__ == "__main__":
    main()