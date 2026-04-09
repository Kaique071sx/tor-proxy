import os
import json
import hashlib
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)

ADMIN_KEY = os.environ.get("ADMIN_KEY")
USERS_FILE = "users.json"
users = {}
users_lock = threading.Lock()

def load_users():
    global users
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    except:
        users = {}

def save_users():
    with users_lock:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

load_users()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    with users_lock:
        if username in users:
            return users[username]["password_hash"] == hash_password(password)
    return False

def check_traffic_limit(username, content_length):
    with users_lock:
        if username not in users:
            return False
        user = users[username]
        if user["bytes_limit"] is not None:
            if user["bytes_used"] + content_length > user["bytes_limit"]:
                return False
    return True

def add_traffic(username, bytes_count):
    with users_lock:
        if username in users:
            users[username]["bytes_used"] += bytes_count
            save_users()

@app.before_request
def handle_auth():
    if request.path.startswith("/admin"):
        auth = request.authorization
        if not auth or auth.username != "admin" or auth.password != ADMIN_KEY:
            return jsonify({"error": "Unauthorized"}), 401

@app.route("/")
def index():
    return jsonify({"service": "Tor Proxy API"})

@app.route("/fetch", methods=["POST"])
def fetch():
    auth = request.authorization
    if not auth or not authenticate(auth.username, auth.password):
        return Response("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Tor Proxy"'})

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing url"}), 400

    url = data["url"]
    method = data.get("method", "GET").upper()
    headers = data.get("headers", {})
    body = data.get("body")

    try:
        proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}
        if method == "GET":
            resp = requests.get(url, proxies=proxies, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, proxies=proxies, headers=headers, json=body, timeout=30)
        else:
            return jsonify({"error": f"Method {method} not supported"}), 400

        content_length = len(resp.content)
        if not check_traffic_limit(auth.username, content_length):
            return jsonify({"error": "Traffic limit exceeded"}), 403

        add_traffic(auth.username, content_length)
        return jsonify({"status_code": resp.status_code, "headers": dict(resp.headers), "content": resp.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users", methods=["GET"])
def list_users():
    with users_lock:
        safe = {u: {"bytes_used": users[u]["bytes_used"], "bytes_limit": users[u]["bytes_limit"], "created_at": users[u].get("created_at")} for u in users}
    return jsonify(safe)

@app.route("/admin/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "username and password required"}), 400

    username = data["username"]
    password = data["password"]
    bytes_limit = data.get("bytes_limit")

    with users_lock:
        if username in users:
            return jsonify({"error": "User already exists"}), 409
        users[username] = {
            "password_hash": hash_password(password),
            "bytes_used": 0,
            "bytes_limit": bytes_limit,
            "created_at": datetime.now().isoformat()
        }
        save_users()
    return jsonify({"message": "User created"}), 201

@app.route("/admin/users/<username>", methods=["DELETE"])
def delete_user(username):
    with users_lock:
        if username not in users:
            return jsonify({"error": "User not found"}), 404
        del users[username]
        save_users()
    return jsonify({"message": "User deleted"})

@app.route("/admin/users/<username>", methods=["PUT"])
def update_user(username):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    with users_lock:
        if username not in users:
            return jsonify({"error": "User not found"}), 404
        if "password" in data:
            users[username]["password_hash"] = hash_password(data["password"])
        if "bytes_limit" in data:
            users[username]["bytes_limit"] = data["bytes_limit"]
        if "bytes_used" in data:
            users[username]["bytes_used"] = data["bytes_used"]
        save_users()
    return jsonify({"message": "User updated"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)