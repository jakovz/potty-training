from flask import Flask
from app import app
import sys
import logging
import json
from io import BytesIO

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handler(request):
    """Handle Vercel serverless function requests."""
    try:
        # Create WSGI environment
        environ = {
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(request.body.encode() if isinstance(request.body, str) else request.body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'SERVER_SOFTWARE': 'Vercel',
            'REQUEST_METHOD': request.method,
            'PATH_INFO': request.path,
            'QUERY_STRING': request.query,
            'SERVER_NAME': 'vercel.app',
            'SERVER_PORT': '443',
        }

        # Add headers
        for key, value in request.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value

        # Response data
        response_data = {}
        
        def start_response(status, headers, exc_info=None):
            status_code = int(status.split(' ')[0])
            response_data['status_code'] = status_code
            response_data['headers'] = dict(headers)

        # Get response from Flask app
        response_body = b''.join(app(environ, start_response))
        
        return {
            'statusCode': response_data.get('status_code', 200),
            'headers': response_data.get('headers', {'Content-Type': 'text/html'}),
            'body': response_body.decode('utf-8')
        }

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': {'Content-Type': 'text/plain'}
        } 