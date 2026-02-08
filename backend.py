from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, hashlib, time

app = Flask(__name__)
CORS(app)

BLOCKCHAIN_FILE = "blockchain.json"
WALLETS_FILE = "wallets.json"

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def create_block(data, prev_hash):
    block = {
        "timestamp": time.time(),
        "data": data,
        "prev_hash": prev_hash
    }
    block_str = json.dumps(block, sort_keys=True).encode()
    block["hash"] = hashlib.sha256(block_str).hexdigest()
    return block

@app.route("/create_wallet", methods=["POST"])
def create_wallet():
    wallets = load_json(WALLETS_FILE, {})
    wallet_id = "ECO-" + hashlib.sha1(str(time.time()).encode()).hexdigest()[:8].upper()
    wallets[wallet_id] = {"balance": 0}
    save_json(WALLETS_FILE, wallets)
    return jsonify({"wallet": wallet_id, "balance": 0})

@app.route("/submit_activity", methods=["POST"])
def submit_activity():
    data = request.json
    wallet = data.get("wallet")
    activity = data.get("activity")
    value = float(data.get("value", 0))

    if not wallet or value <= 0:
        return jsonify({"error": "Invalid input"}), 400

    if activity == "walking" and value > 40000:
        return jsonify({"error": "Unrealistic steps"}), 400
    if activity == "cycling" and value > 200:
        return jsonify({"error": "Unrealistic cycling distance"}), 400
    if activity == "running" and value > 300:
        return jsonify({"error": "Unrealistic running duration"}), 400

    if activity == "walking":
        calories = value * 0.05
        carbon = (value / 1300) * 0.12
    elif activity == "cycling":
        calories = value * 25
        carbon = value * 0.21
    else:
        calories = value * 11
        carbon = value * 0.15

    eco_score = round(calories + carbon * 200)
    tokens = round(eco_score / 10)

    wallets = load_json(WALLETS_FILE, {})
    wallets[wallet]["balance"] += tokens
    save_json(WALLETS_FILE, wallets)

    blockchain = load_json(BLOCKCHAIN_FILE, [])
    prev_hash = blockchain[-1]["hash"] if blockchain else "0"*64

    block = create_block({
        "wallet": wallet,
        "activity": activity,
        "value": value,
        "calories": calories,
        "carbon": carbon,
        "ecoScore": eco_score,
        "tokens": tokens
    }, prev_hash)

    blockchain.append(block)
    save_json(BLOCKCHAIN_FILE, blockchain)

    return jsonify({
        "calories": calories,
        "carbon": carbon,
        "ecoScore": eco_score,
        "tokens": tokens,
        "balance": wallets[wallet]["balance"]
    })

@app.route("/ledger", methods=["GET"])
def ledger():
    return jsonify(load_json(BLOCKCHAIN_FILE, []))

if __name__ == "__main__":
    app.run(debug=True)
