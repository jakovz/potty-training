from app import app
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def handler(request):
    """Handle incoming Vercel requests and forward them to Flask app."""
    from urllib.parse import urlencode

    logger.debug(f"Received request: {request.method} {request.path}")
    logger.debug(f"Headers: {request.headers}")

    # Recreate WSGI environment dictionary from Vercel request
    environ = {
        'REQUEST_METHOD': request.method,
        'SCRIPT_NAME': '',
        'PATH_INFO': request.path,
        'QUERY_STRING': urlencode(request.query_params) if request.query_params else '',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': request.body,
        'wsgi.errors': '',
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # Add headers to environment
    for key, value in request.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value

    # Handle special headers
    if 'content-type' in request.headers:
        environ['CONTENT_TYPE'] = request.headers['content-type']
    if 'content-length' in request.headers:
        environ['CONTENT_LENGTH'] = request.headers['content-length']

    def start_response(status, headers):
        return None

    # Get response from Flask app
    response = app(environ, start_response)
    
    # Convert response to Vercel-compatible format
    if isinstance(response, (list, tuple)) and len(response) > 0:
        body = response[0]
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        return {
            'statusCode': int(environ.get('RESPONSE_STATUS', 200)),
            'body': body,
            'headers': {
                'Content-Type': 'text/html',
            },
        }
    return {
        'statusCode': 500,
        'body': 'Internal server error',
        'headers': {
            'Content-Type': 'text/plain',
        },
    } 