#!/usr/bin/env python3
"""
Test startup script for debugging Railway deployment.
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
    
    # Use uvicorn with minimal test API
    cmd = [
        'uvicorn',
        'test_api:app',  # Use test_api instead of api
        '--host', host,
        '--port', str(port),
        '--access-log'
    ]
    
    print(f"Starting TEST server on {host}:{port}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
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