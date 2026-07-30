import serial
import json
import time
from datetime import datetime

DATA_FILE = "/home/pi/data.json"
MAX_HISTORY = 200   # keep the last 200 readings for the chart

def connect_serial():
    while True:
        try:
            return serial.Serial("/dev/ttyACM0", 115200, timeout=1)
        except serial.SerialException:
            print("Uno not found, retrying in 5s...")
            time.sleep(5)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"count": 0, "history": []}

def save_data(data):
    # write to a temp file then rename - avoids the dashboard ever reading a half-written file
    tmp_path = DATA_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    import os
    os.replace(tmp_path, DATA_FILE)

ser = connect_serial()
data = load_data()

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line.isdigit():
            count = int(line)
            data["count"] = count
            data["history"].append({
                "count": count,
                "time": datetime.now().strftime("%H:%M:%S")
            })
            data["history"] = data["history"][-MAX_HISTORY:]
            save_data(data)
            print(f"Updated count: {count}")
    except serial.SerialException:
        print("Lost connection to Uno, reconnecting...")
        ser = connect_serial()
    time.sleep(0.5)
