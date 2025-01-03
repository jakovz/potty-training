from flask import Flask
import sys
import logging
import json
from app import app

# Configure logging to output to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handler(event, context):
    """Handle incoming Vercel serverless function requests."""
    try:
        logger.info(f"Received event: {event}")
        
        # Parse the event body if it exists
        body = event.get('body', '')
        if isinstance(body, str) and body:
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass

        # Create the WSGI environment
        environ = {
            'REQUEST_METHOD': event.get('httpMethod', 'GET'),
            'SCRIPT_NAME': '',
            'PATH_INFO': event.get('path', '/'),
            'QUERY_STRING': event.get('queryStringParameters', ''),
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': body,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        # Add headers
        headers = event.get('headers', {})
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value

        # Response data
        response_data = {
            'statusCode': 200,
            'body': '',
            'headers': {},
        }

        def start_response(status, response_headers, exc_info=None):
            status_code = int(status.split()[0])
            response_data['statusCode'] = status_code
            response_data['headers'] = dict(response_headers)

        # Get response from Flask app
        response = app(environ, start_response)
        
        # Handle response
        if response:
            response_body = b''.join(response)
            if isinstance(response_body, bytes):
                response_body = response_body.decode('utf-8')
            response_data['body'] = response_body

        logger.info(f"Returning response: {response_data}")
        return response_data

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': {
                'Content-Type': 'text/plain',
            }
        } 