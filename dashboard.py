from flask import Flask, jsonify, render_template_string, Response
import json
import csv
import io

app = Flask(__name__)
DATA_FILE = "/home/pi/data.json"

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Abrasion Test Monitor</title>
    <meta http-equiv="refresh" content="0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; text-align: center; background: #1a1a2e; color: #eee; padding: 40px; }
        h1 { font-size: 1.2em; color: #aaa; }
        .count { font-size: 5em; font-weight: bold; color: #4ade80; }
        canvas { max-width: 700px; margin: 30px auto; }
        .download-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: #4ade80;
            color: #1a1a2e;
            font-weight: bold;
            text-decoration: none;
            border-radius: 8px;
            font-size: 1em;
        }
        .download-btn:hover { background: #86efac; }
    </style>
</head>
<body>
    <h1>Abrasion Test - Cycle Count</h1>
    <div class="count" id="count">--</div>
    <canvas id="chart"></canvas>
    <br>
    <a href="/api/download" class="download-btn">Download History (CSV)</a>

    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        let chart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Cycle Count', data: [], borderColor: '#4ade80', tension: 0.2 }] },
            options: { scales: { y: { beginAtZero: true } } }
        });

        async function refresh() {
            const res = await fetch('/api/data');
            const data = await res.json();
            document.getElementById('count').innerText = data.count;
            chart.data.labels = data.history.map(h => h.time);
            chart.data.datasets[0].data = data.history.map(h => h.count);
            chart.update();
        }

        refresh();
        setInterval(refresh, 3000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/api/data")
def api_data():
    try:
        with open(DATA_FILE, "r") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"count": 0, "history": []})

@app.route("/api/download")
def download_csv():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"history": []}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Time", "Count"])
    for entry in data["history"]:
        writer.writerow([entry["time"], entry["count"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=abrasion_test_history.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
