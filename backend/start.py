#!/usr/bin/env python3
"""
Startup script for the GraphRAG backend server.
Handles PORT environment variable properly for deployment platforms.
"""

import os
import sys
import subprocess

def main():
    # Get port from environment variable, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Validate port is numeric
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError(f"Port must be between 1-65535, got {port_int}")
    except ValueError as e:
        print(f"Error: Invalid port value '{port}': {e}")
        sys.exit(1)
    
    # Get host, default to 0.0.0.0 for deployment
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Determine which server to use
    use_gunicorn = os.environ.get('USE_GUNICORN', 'false').lower() == 'true'
    
    if use_gunicorn:
        # Use gunicorn for production
        cmd = [
            'gunicorn',
            'api:app',
            '--bind', f'{host}:{port}',
            '--worker-class', 'uvicorn.workers.UvicornWorker',
            '--workers', '1',
            '--timeout', '300',
            '--access-logfile', '-',
            '--error-logfile', '-'
        ]
    else:
        # Use uvicorn for development/simple deployment
        cmd = [
            'uvicorn',
            'api:app',
            '--host', host,
            '--port', str(port),
            '--access-log',
            '--timeout-keep-alive', '300'
        ]
    
    print(f"Starting server on {host}:{port}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)

if __name__ == '__main__':
    main() 