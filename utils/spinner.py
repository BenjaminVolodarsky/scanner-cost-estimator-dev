# utils/spinner.py
import sys, time, threading

_spinner_active = False

def _spin():
    frames = ["|", "/", "-", "\\"]
    i = 0
    while _spinner_active:
        sys.stdout.write(f"\r Scanning {frames[i % len(frames)]}")
        sys.stdout.flush()
        i += 1
        time.sleep(0.12)
    sys.stdout.write("\r")   # clear spinner on stop


def start_spinner():
    global _spinner_active
    _spinner_active = True
    t = threading.Thread(target=_spin)
    t.daemon = True
    t.start()


def stop_spinner():
    global _spinner_active
    _spinner_active = False
    time.sleep(0.15)  # allow final frame flush
