from flask import Flask
from app import app as flask_app

# This is required for Vercel serverless deployment
def handler(request):
    return flask_app.wsgi_app(request.environ, lambda x, y: y) 