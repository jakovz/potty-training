from flask import Flask
from app import app
import sys
import logging
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VercelHandler(BaseHTTPRequestHandler):
    def __init__(self, req, client_addr, server):
        self.req = req
        super().__init__(client_addr, server)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        try:
            # Get query parameters
            query_string = self.req.query or ''
            query_params = parse_qs(query_string)

            # Create environment for Flask app
            environ = {
                'REQUEST_METHOD': self.req.method,
                'PATH_INFO': self.req.path,
                'QUERY_STRING': query_string,
                'SERVER_NAME': 'vercel.app',
                'SERVER_PORT': '443',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https',
                'wsgi.input': self.req.body,
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
            }

            # Add headers
            for key, value in self.req.headers.items():
                key = key.upper().replace('-', '_')
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    key = f'HTTP_{key}'
                environ[key] = value

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

def handler(request):
    """Handle Vercel serverless function requests."""
    return VercelHandler(request, ('vercel.app', 443), None).handle_request() 