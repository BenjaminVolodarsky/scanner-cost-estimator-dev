import sys, threading, time

spinner_active = False

def spinner():
    while spinner_active:
        for frame in "|/-\\":
            sys.stdout.write(f"\r⏳ Scanning... {frame}")
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write("\r✔ Scan complete!       \n")
    sys.stdout.flush()

def start_spinner():
    global spinner_active
    spinner_active = True
    t = threading.Thread(target=spinner)
    t.daemon = True
    t.start()
    return t

def stop_spinner():
    global spinner_active
    spinner_active = False
