from flask import Flask, render_template, request, jsonify
import urllib.request, urllib.error, json, os, shutil
from datetime import datetime

app = Flask(__name__)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BLOCKS_FILE = os.path.join(BASE_DIR, "blocks.json")
BACKUP_DIR  = os.path.join(BASE_DIR, "backups")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

CAMPUS_CONTEXT = """
You are LPU GO, a campus wayfinding assistant for Lovely Professional University (LPU), Phagwara.
Answer concisely from the block list. Handle words like "food", "hospital", "hostel" and block numbers.
Keep answers under 70 words.
"""


def load_blocks():
    with open(BLOCKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_blocks(data):
    if not isinstance(data, dict):
        return False, "root must be a JSON object"
    if not isinstance(data.get("zones"), list):
        return False, "missing or invalid 'zones' array"
    places = data.get("places")
    if not isinstance(places, list):
        return False, "missing or invalid 'places' array"

    seen = set()
    for i, p in enumerate(places):
        if not isinstance(p, dict):
            return False, f"places[{i}] must be an object"
        for key in ("id", "name", "lat", "lng"):
            if key not in p:
                return False, f"places[{i}] is missing '{key}'"
        if not isinstance(p["lat"], (int, float)) or not isinstance(p["lng"], (int, float)):
            return False, f"places[{i}] lat/lng must be numbers"
        if p["id"] in seen:
            return False, f"duplicate place id: {p['id']}"
        seen.add(p["id"])
    return True, None


@app.route("/api/blocks", methods=["GET"])
def get_blocks():
    try:
        return jsonify(load_blocks())
    except FileNotFoundError:
        return jsonify({"error": "blocks.json not found", "path": BLOCKS_FILE}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"blocks.json is not valid JSON: {e}"}), 500


@app.route("/api/blocks", methods=["POST"])
def save_blocks():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"ok": False, "error": "request body must be JSON"}), 400

    ok, err = validate_blocks(data)
    if not ok:
        return jsonify({"ok": False, "error": err}), 400

    if os.path.exists(BLOCKS_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(BLOCKS_FILE, os.path.join(BACKUP_DIR, f"blocks-{stamp}.json"))

    with open(BLOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return jsonify({"ok": True, "places": len(data["places"])})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask_gemini():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"answer": "Please type a question about the LPU campus."}), 400
    if not GEMINI_API_KEY:
        return jsonify({"answer": "LPU GO AI: no GEMINI_API_KEY set. Use the route planner on the map.",
                        "source": "no-key"})

    try:
        blocks = load_blocks()
        lines = "\n".join(f"- Block {p['id']}: {p['name']}" for p in blocks["places"])
        context = f"{CAMPUS_CONTEXT}\n\nCampus blocks:\n{lines}"
    except Exception:
        context = CAMPUS_CONTEXT

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    body = {"contents": [{"parts": [{"text": f"{context}\n\nUser query: {query}"}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 256}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read().decode("utf-8"))
            return jsonify({"answer": res["candidates"][0]["content"]["parts"][0]["text"].strip(),
                            "source": "gemini"})
    except Exception as e:
        app.logger.warning("Gemini failed: %s", e)
    return jsonify({"answer": f"Couldn't reach Gemini. Try the route planner on the map.", "source": "fallback"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)