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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abrasion Test Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            background: #1B2A41;
            color: #E2F8F8;
            padding: 20px;
            margin: 0;
            min-height: 100vh;
        }
        h1 {
            font-size: clamp(1.4em, 5vw, 2em);
            color: #A9C8DE;
            margin-bottom: 8px;
        }
        .description {
            font-size: clamp(0.9em, 3vw, 1.1em);
            color: #A9C8DE;
            opacity: 0.8;
            max-width: 500px;
            margin: 0 auto 30px auto;
            line-height: 1.5;
        }
        .count-label {
            font-size: clamp(0.9em, 3vw, 1.1em);
            color: #A9C8DE;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .count {
            font-size: clamp(4em, 20vw, 7em);
            font-weight: bold;
            color: #F0623A;
            margin: 10px 0 30px 0;
            line-height: 1;
        }
        .chart-container {
            max-width: 700px;
            width: 100%;
            margin: 0 auto 30px auto;
            background: #2E4A6E;
            border-radius: 16px;
            padding: 20px;
        }
        .download-btn {
            display: inline-block;
            margin-top: 10px;
            padding: 16px 32px;
            background: #A9C8DE;
            color: #1B2A41;
            font-weight: bold;
            text-decoration: none;
            border-radius: 10px;
            font-size: clamp(1em, 3vw, 1.15em);
        }
        .download-btn:active { background: #E2F8F8; }
    </style>
</head>
<body>
    <h1>Abrasion Test Monitor</h1>
    <p class="description">
        Live cycle count from the solar panel brush abrasion rig.
        Updates automatically every 3 seconds.
    </p>

    <div class="count-label">Cycle Count</div>
    <div class="count" id="count">--</div>

    <div class="chart-container">
        <canvas id="chart"></canvas>
    </div>

    <a href="/api/download" class="download-btn">Download History (CSV)</a>

    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        let chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Cycle Count',
                    data: [],
                    borderColor: '#F0623A',
                    backgroundColor: 'rgba(240, 98, 58, 0.15)',
                    fill: true,
                    tension: 0.2,
                    pointBackgroundColor: '#F0623A'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { color: '#A9C8DE' }, grid: { color: '#1B2A41' } },
                    x: { ticks: { color: '#A9C8DE' }, grid: { color: '#1B2A41' } }
                },
                plugins: {
                    legend: { labels: { color: '#A9C8DE' } }
                }
            }
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
