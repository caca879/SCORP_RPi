# Abrasion Test - Live Dashboard (Raspberry Pi)

This sets up a Raspberry Pi to read the cycle count from the Arduino Uno
over USB serial and display it on a live, self-hosted web dashboard —
no third-party cloud service (like ThingSpeak) required.

## How it works

```
Uno --(USB serial)--> data_reader.py --(writes)--> data.json --(reads)--> dashboard.py (Flask) --(serves)--> browser
```

- `data_reader.py` reads the cycle count printed by the Uno and saves it
  (plus a rolling history) to a local `data.json` file.
- `dashboard.py` is a small Flask web server that reads `data.json` and
  serves a live-updating page showing the current count, a history chart,
  and a CSV download button.
- Both run continuously in the background via `systemd`, so they start
  automatically on boot and restart themselves if they ever crash.

## Setup (on the Raspberry Pi)

### 1. Update the system

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install required Python packages

```bash
pip3 install --break-system-packages pyserial flask requests
```

### 3. (If using an Argon ONE V3 case) Install the case control software

```bash
curl https://download.argon40.com/argon1.sh | bash
```

This enables proper fan control and the case's power button (safe
shutdown/reboot). Optional fan tuning:

```bash
sudo argonone-config
```

### 4. Create the project folder and scripts

```bash
mkdir -p /home/pi/abrasion-monitor
cd /home/pi/abrasion-monitor
```

Create `data_reader.py` and `dashboard.py` in this folder (see the
project's `raspberryPi/` folder in this repo for the current versions).
Make sure both scripts point to the same data file path, e.g.:

```python
DATA_FILE = "/home/pi/abrasion-monitor/data.json"
```

### 5. Test both scripts manually first

With the Uno connected via USB:

```bash
python3 data_reader.py
```

Confirm it prints `Updated count: X` as cycles complete, then `Ctrl+C`
to stop. Then:

```bash
python3 dashboard.py
```

Open `http://localhost:5000` (or the Pi's IP from another device on the
same network) to confirm the dashboard loads, then `Ctrl+C` to stop.

### 6. Set up systemd services so both run automatically

`/etc/systemd/system/data-reader.service`:

```ini
[Unit]
Description=Uno Serial Data Reader
After=network.target dev-ttyACM0.device
Wants=dev-ttyACM0.device

[Service]
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 /home/pi/abrasion-monitor/data_reader.py
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/dashboard.service`:

```ini
[Unit]
Description=Abrasion Test Dashboard
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/abrasion-monitor/dashboard.py
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start both:

```bash
sudo systemctl daemon-reload
sudo systemctl enable data-reader.service dashboard.service
sudo systemctl start data-reader.service dashboard.service
```

Check both are running:

```bash
sudo systemctl status data-reader.service
sudo systemctl status dashboard.service
```

## Why Tailscale?

The Pi's regular WiFi IP address (e.g. `192.168.20.189`) is **not stable** —
the network's DHCP server can hand it a different address whenever it
reconnects or its lease renews. That means a bookmarked link can silently
stop working, and the dashboard is only reachable at all while your device
is on the *same* WiFi network as the Pi (e.g. only on-campus).

[Tailscale](https://tailscale.com) solves both problems: it creates a
private VPN between your devices where the Pi gets a **fixed address that
never changes**, and that address works from **any network** your device
is connected to — home WiFi, mobile data, anywhere — not just the
network the Pi happens to be on. No port forwarding or router
configuration needed.

The tradeoff: anyone who wants to view the dashboard needs the Tailscale
app installed and added to the same private network — it's no longer
something a random person on the WiFi can stumble onto by typing an IP.
For a small team monitoring a long-running test, that's a reasonable
trade for "it always just works."

### Setting up Tailscale on the Pi

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

This prints a login link — open it in a browser and sign in. The Pi then
joins the private Tailscale network. Get its stable address:

```bash
tailscale ip -4
```

## For anyone who wants to view the dashboard

1. Install Tailscale on your own device (phone, laptop): https://tailscale.com/download
2. Ask the project owner to invite you to the Tailscale network (via
   the Tailscale admin console, using your email).
3. Sign in to the Tailscale app using the invited account.
4. Open a browser and go to:
   ```
   http://<pi-tailscale-ip>:5000
   ```
   (ask the project owner for the current Tailscale IP, found by running
   `tailscale ip -4` on the Pi)

Once connected, the dashboard shows the live cycle count, a rolling
history chart, and a button to download the full history as a CSV file.

## Troubleshooting

**Dashboard shows old data / stops updating**
Check that `data-reader.service` is still running:
```bash
sudo systemctl status data-reader.service
journalctl -u data-reader.service -n 50
```

**Can't reach the dashboard at all**
Confirm both services are active, and that you're connected to Tailscale
on the viewing device (not just relying on the regular WiFi IP, which may
have changed).

**`could not open port /dev/ttyACM0`**
The Uno isn't currently detected. Check the USB connection and run
`ls /dev/tty*` to confirm the port name matches what's in `data_reader.py`.
