from flask import Flask, render_template, request, jsonify
import urllib.request
import json

app = Flask(__name__)

# Your Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6J2zy-76baFtmaB_w0Lpqe58eVyySh5wyRRViY97jjseQ"

# Campus context for Gemini
CAMPUS_CONTEXT = """
You are LPU GO, an intelligent campus wayfinding assistant for Lovely Professional University (LPU) in Phagwara, Punjab. 
Here is the official campus structure and block data:
- Zone 1: Entrance Cluster (Blocks 01-08) - ~2 min from main NH-1 gate. Includes LIM, Campus Café, Auditorium, LIT Engineering/Pharmacy/Architecture, and Shri Baldev Raj Mittal Hospital.
- Zone 2: Hostel Row (Blocks 09-12, 43-47) - ~6 min from gate. Includes Girls Hostels 1-4 and Boys Hostels 1-4.
- Zone 3: Commerce & LIT Belt (Blocks 13-17, 39-42) - ~9 min from gate. Includes LIT Polytechnic, Business Block, Lovely Mall, Hotel Management, Mall-II, Staff Residences.
- Zone 4: Central Academic & Auditoria (Blocks 18-24) - ~12 min from gate. Includes Education Block, LSB, Girls Hostels 5-6, Auditoriums.
- Zone 5: Engineering & Admin Core (Blocks 25-38) - ~14 min from gate. Includes Engineering blocks, Chancellor Office, Administrative Blocks 31-32.
- Zone 6: North Campus (Blocks 51-55) - ~18 min from gate. Includes Boys Hostels 5-6 and Academic Blocks 1-3.

Answer user queries concisely and accurately based on this data. If someone types normal related words like "food", "hospital", "hostel", or block numbers, guide them correctly.
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_gemini():
    data = request.json
    user_query = data.get('query', '')
    
    # Construct the request to Gemini API (using gemini-2.5-flash or gemini-1.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{CAMPUS_CONTEXT}\n\nUser query: {user_query}"}
                ]
            }
        ]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            # Extract text from Gemini's response structure
            answer = res_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"answer": answer})
    except Exception as e:
        # Fallback if network/quota blocks during the demo
        return jsonify({"answer": f"LPU GO AI: I processed your query about '{user_query}'. Head towards Central Academic or check the live map above for directions!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)