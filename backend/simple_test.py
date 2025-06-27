#!/usr/bin/env python3
"""
Ultra-simple HTTP server for Railway testing
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            response = {
                "message": "Simple test server is working!",
                "timestamp": datetime.now().isoformat(),
                "port": os.environ.get("PORT", "unknown")
            }
        elif self.path == '/health':
            response = {
                "status": "healthy",
                "port": os.environ.get("PORT", "unknown")
            }
        else:
            response = {"error": "Not found"}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def main():
    port = int(os.environ.get('PORT', '8000'))
    host = '0.0.0.0'
    
    print("=" * 60)
    print("SIMPLE TEST SERVER")
    print("=" * 60)
    print(f"Starting on {host}:{port}")
    print(f"PORT from env: {os.environ.get('PORT', 'NOT_SET')}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 60)
    
    server = HTTPServer((host, port), TestHandler)
    print(f"Server running on http://{host}:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == '__main__':
    main() 