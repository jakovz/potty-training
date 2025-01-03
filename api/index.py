from flask import Flask
from app import app
import sys
import logging
from base64 import b64decode
import json

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def application(scope, receive, send):
    """ASGI application."""
    async def _send(event):
        await send(event)

    async def _receive():
        return await receive()

    return app.wsgi_app(scope, _receive, _send)

def handle_request(event):
    """Convert API Gateway event to WSGI response."""
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    query = event.get('queryStringParameters', {}) or {}
    body = event.get('body', '')
    
    if body and event.get('isBase64Encoded', False):
        body = b64decode(body)
    
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join(f'{k}={v}' for k, v in query.items()),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value

    response = {'statusCode': 200, 'headers': {}, 'body': ''}
    
    def start_response(status, response_headers, exc_info=None):
        status_code = int(status.split()[0])
        response['statusCode'] = status_code
        response['headers'].update(dict(response_headers))
    
    result = app(environ, start_response)
    response['body'] = b''.join(result).decode('utf-8')
    return response

def handler(event, context):
    """Lambda/Vercel handler function."""
    try:
        logger.info(f"Received event: {event}")
        response = handle_request(event)
        logger.info(f"Returning response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': {'Content-Type': 'text/plain'}
        } 