from app import app
import logging
import sys
import traceback

# Configure logging to output to stdout
logging.basicConfig(
    stream=sys.stdout,  # Ensure logs go to stdout for Vercel
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handler(request):
    """Handle incoming Vercel requests and forward them to Flask app."""
    try:
        from urllib.parse import urlencode
        
        # Log request details
        print(f"[DEBUG] Received request: {request.method} {request.path}")  # Direct print for Vercel
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request query params: {request.query_params}")

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
            'wsgi.errors': sys.stderr,
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
            logger.debug(f"Added header: {key}={value}")

        # Handle special headers
        if 'content-type' in request.headers:
            environ['CONTENT_TYPE'] = request.headers['content-type']
        if 'content-length' in request.headers:
            environ['CONTENT_LENGTH'] = request.headers['content-length']

        def start_response(status, headers):
            logger.info(f"Response status: {status}")
            logger.info(f"Response headers: {headers}")
            return None

        # Get response from Flask app
        logger.info("Calling Flask application")
        response = app(environ, start_response)
        
        # Convert response to Vercel-compatible format
        if isinstance(response, (list, tuple)) and len(response) > 0:
            body = response[0]
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            logger.info("Successfully processed response")
            return {
                'statusCode': int(environ.get('RESPONSE_STATUS', 200)),
                'body': body,
                'headers': {
                    'Content-Type': 'text/html',
                },
            }
        
        logger.error("Empty response from Flask application")
        return {
            'statusCode': 500,
            'body': 'Internal server error - Empty response',
            'headers': {
                'Content-Type': 'text/plain',
            },
        }
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        print(f"[ERROR] Exception in handler: {str(e)}")  # Direct print for Vercel
        traceback.print_exc()  # Print full traceback
        return {
            'statusCode': 500,
            'body': f'Internal server error: {str(e)}',
            'headers': {
                'Content-Type': 'text/plain',
            },
        } 