from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, abort
from functools import wraps
import jwt
from database import add_event, get_statistics
from datetime import datetime
import os
import sys
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')

# Configure logging
logging.basicConfig(
    stream=sys.stdout,  # Ensure logs go to stdout for Vercel
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

@app.route('/health')
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({
        "status": "healthy",
        "environment_vars": {
            "FLASK_ENV": os.getenv('FLASK_ENV'),
            "PYTHONPATH": os.getenv('PYTHONPATH'),
            # Don't log sensitive values
            "HAS_SECRET_KEY": bool(os.getenv('FLASK_SECRET_KEY')),
            "HAS_SUPABASE_URL": bool(os.getenv('SUPABASE_URL')),
        }
    })

# Add error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {error}", exc_info=True)
    return jsonify({
        "error": str(error),
        "stacktrace": str(sys.exc_info())
    }), 500

# Add this after app initialization
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    logger.debug('Response: %s', response.get_data())
    return response

if __name__ == '__main__':
    app.run() 