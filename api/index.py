from app import app

def handler(request):
    """Simple handler that forwards requests to Flask app."""
    return app 