#!/usr/bin/env python3
"""
O.U.R.A.N.O.S – AI Vision Backend
===================================
Install:  pip install -r requirements.txt
Run:      python server.py
Open:     http://localhost:5000
"""
import os, json, traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Find the dashboard HTML (any name) ─────────────────────────────────────
def find_html():
    preferred = ['OURANOS_dashboard_ai.html', 'OURANOS_dashboard.html', 'index.html']
    for name in preferred:
        if os.path.isfile(os.path.join(BASE_DIR, name)):
            return name
    for f in os.listdir(BASE_DIR):
        if f.endswith('.html'):
            return f
    return None

# ─── Serve dashboard ────────────────────────────────────────────────────────
@app.route('/')
def index():
    html_file = find_html()
    if html_file:
        return send_from_directory(BASE_DIR, html_file)
    return (
        "<h2>❌ No HTML file found</h2>"
        f"<p>Put <code>OURANOS_dashboard_ai.html</code> in:<br><code>{BASE_DIR}</code></p>"
        "<p>Files currently here: " + ", ".join(os.listdir(BASE_DIR)) + "</p>"
    ), 404

# ─── Health / key-validation ────────────────────────────────────────────────
@app.route('/api/health', methods=['POST'])
def health():
    try:
        import anthropic
        data = request.get_json(force=True) or {}
        key  = data.get('apiKey', '').strip()
        if not key:
            return jsonify({'ok': False, 'error': 'No API key provided'}), 400
        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=5,
            messages=[{'role': 'user', 'content': 'Hi'}]
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

# ─── Vision analysis ────────────────────────────────────────────────────────
@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        import anthropic
        data      = request.get_json(force=True) or {}
        key       = data.get('apiKey',  '').strip()
        image_b64 = data.get('image',   '')
        prompt    = data.get('prompt',  '')
        model     = data.get('model',   'claude-opus-4-6')

        if not key:
            return jsonify({'error': 'No API key provided'}), 400
        if not image_b64:
            return jsonify({'error': 'No image data'}), 400
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        client  = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type':       'base64',
                            'media_type': 'image/jpeg',
                            'data':       image_b64
                        }
                    },
                    {'type': 'text', 'text': prompt}
                ]
            }]
        )

        raw   = message.content[0].text
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            parsed = json.loads(clean)
            return jsonify({'result': clean, 'parsed': parsed})
        except json.JSONDecodeError:
            return jsonify({'result': raw, 'parsed': None})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ─── Entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    html_file = find_html()
    print()
    print('=' * 52)
    print('  🛸  O.U.R.A.N.O.S  AI  Backend')
    print('  ──────────────────────────────')
    print(f'  Folder:    {BASE_DIR}')
    if html_file:
        print(f'  Serving:   {html_file}  ✅')
    else:
        print('  HTML file: ❌ NOT FOUND — put OURANOS_dashboard_ai.html here')
    print('  Dashboard  →  http://localhost:5000')
    print('  Analyze    →  POST /api/analyze')
    print('=' * 52)
    print()
    app.run(debug=False, port=5000, host='0.0.0.0')
