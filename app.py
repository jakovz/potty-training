from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, abort
from functools import wraps
import jwt
from database import add_event, get_statistics
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'message': 'No authorization header'}), 401
            
        try:
            # Remove 'Bearer ' from the header
            token = auth_header.split(' ')[1]
            # Verify the token with Supabase public key
            # Note: In production, you should verify this token with Supabase
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Invalid token'}), 401
            
    return decorated

@app.route('/')
def index():
    anon_key = os.getenv('SUPABASE_ANON_KEY')  # Make sure to use the anon key
    if not anon_key:
        anon_key = os.getenv('SUPABASE_KEY')  # Fallback to SUPABASE_KEY if ANON_KEY not set
    
    return render_template('index.html',
                         supabase_url=os.getenv('SUPABASE_URL'),
                         supabase_key=anon_key,
                         current_time=datetime.now().isoformat())

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/icons/<path:filename>')
def icons(filename):
    return send_from_directory('static/icons', filename)

@app.route('/api/events', methods=['POST'])
@require_auth
def create_event():
    data = request.json
    timestamp = datetime.fromisoformat(data['timestamp'])
    result = add_event(data['type'], data['location'], timestamp)
    return jsonify({"status": "success"})

@app.route('/api/stats')
@require_auth
def get_stats():
    return jsonify(get_statistics())

@app.route('/auth/callback')
def auth_callback():
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) 