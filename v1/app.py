from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.error
import json
import os

app = Flask(__name__)

# ------------------------------------------------------------------
# Gemini API configuration
# Best practice: set the key as an environment variable instead of
# hard-coding it. Fallback default is kept so the demo still runs.
#   Windows   : set GEMINI_API_KEY=your_key_here
#   macOS/Linux: export GEMINI_API_KEY=your_key_here
# ------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6J2zy-76baFtmaB_w0Lpqe58eVyySh5wyRRViY97jjseQ"
)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

CAMPUS_CONTEXT = """
You are LPU GO, an intelligent campus wayfinding assistant for Lovely Professional University (LPU) in Phagwara, Punjab.
Here is the official campus structure and block data:
- Zone 1: Entrance Cluster (Blocks 01-08) - ~2 min from main NH-1 gate. Includes LIM, Campus Cafe, Auditorium, LIT Engineering/Pharmacy/Architecture, and Shri Baldev Raj Mittal Hospital.
- Zone 2: Hostel Row (Blocks 09-12, 43-47) - ~6 min from gate. Includes Girls Hostels 1-4 and Boys Hostels 1-4.
- Zone 3: Commerce & LIT Belt (Blocks 13-17, 39-42) - ~9 min from gate. Includes LIT Polytechnic, Business Block, Lovely Mall, Hotel Management, Mall-II, Staff Residences.
- Zone 4: Central Academic & Auditoria (Blocks 18-24) - ~12 min from gate. Includes Education Block, LSB, Girls Hostels 5-6, Auditoriums.
- Zone 5: Engineering & Admin Core (Blocks 25-38) - ~14 min from gate. Includes Engineering blocks, Chancellor Office, Administrative Blocks 31-32.
- Zone 6: North Campus (Blocks 51-55) - ~18 min from gate. Includes Boys Hostels 5-6 and Academic Blocks 1-3.

Answer user queries concisely and accurately based on this data. If someone types normal related words like "food", "hospital", "hostel", or block numbers, guide them correctly.
Keep answers under 70 words.
"""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def ask_gemini():
    data = request.get_json(silent=True) or {}
    user_query = (data.get('query') or '').strip()

    if not user_query:
        return jsonify({"answer": "Please type a question about the LPU campus."}), 400

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": f"{CAMPUS_CONTEXT}\n\nUser query: {user_query}"}]}
        ],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 256},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            answer = res_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"answer": answer.strip(), "source": "gemini"})

    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')
        app.logger.warning("Gemini HTTP %s: %s", e.code, detail[:300])
    except Exception as e:
        app.logger.warning("Gemini request failed: %s", e)

    # Graceful fallback so the demo never dies
    return jsonify({
        "answer": (
            f"LPU GO AI: I couldn't reach the Gemini service just now, but I can still help. "
            f"You asked about \u201c{user_query}\u201d \u2014 try the From & To route planner on the map, "
            f"or ask me about a specific block number (01-55)."
        ),
        "source": "fallback",
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)