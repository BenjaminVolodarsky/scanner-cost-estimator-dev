import time, threading

spinner_running = False

def spinner_silent():
    # does nothing except wait — no printing
    while spinner_running:
        time.sleep(0.2)

def start_spinner():
    global spinner_running
    spinner_running = True
    t = threading.Thread(target=spinner_silent)
    t.daemon = True
    t.start()

def stop_spinner():
    global spinner_running
    spinner_running = False
