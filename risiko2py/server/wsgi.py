"""
WSGI entrypoint for production WSGI servers (gunicorn / uWSGI).
Example: gunicorn --bind 127.0.0.1:5000 wsgi:application
"""
from app import app as application
# application is the WSGI callable expected by most servers.
