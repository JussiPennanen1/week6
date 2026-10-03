import os
import time
import json
import logging
from flask import Flask, jsonify, request, g
import mysql.connector
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(message)s")

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'appuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'placeholder_password')
DB_NAME = os.getenv('DB_NAME', 'appdb')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request(response):
    duration_ms = round((time.time() - g.start_time) * 1000, 2)
    log_data = {
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
        "remote_addr": request.remote_addr
    }
    app.logger.info(json.dumps(log_data))
    return response

@app.route('/healthz')
def healthz():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": str(e)}), 503

@app.route('/api')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT NOW()")
        db_time = cur.fetchone()[0]
        
        cur.execute("UPDATE visits SET count = count + 1 WHERE id = 1")
        conn.commit()
        
        cur.execute("SELECT count FROM visits WHERE id = 1")
        visit_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "Hello from MySQL via Flask v1.0.1!",
            "db_time": str(db_time),
            "visits": visit_count
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/weather')
def get_weather():
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return jsonify({"error": "OPENWEATHER_API_KEY is not set"}), 500

    url = f"https://api.openweathermap.org/data/2.5/weather?q=Oulu&units=metric&appid={api_key}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "city": data.get("name"),
            "temperature_celsius": data.get("main", {}).get("temp"),
            "feels_like_celsius": data.get("main", {}).get("feels_like"),
            "humidity_percent": data.get("main", {}).get("humidity"),
            "condition": data.get("weather", [{}])[0].get("description")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)