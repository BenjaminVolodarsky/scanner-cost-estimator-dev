import sys, time, threading

spinner_running = False

def spinner():
    frames = "|/-\\"
    i = 0
    while spinner_running:
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.flush()

def start_spinner():
    global spinner_running
    spinner_running = True
    t = threading.Thread(target=spinner)
    t.daemon = True
    t.start()

def stop_spinner():
    global spinner_running
    spinner_running = False
