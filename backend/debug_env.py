#!/usr/bin/env python3
"""
Environment debugging script for Railway
"""

import os
import sys
import time

def main():
    print("=" * 80)
    print("RAILWAY ENVIRONMENT DEBUG")
    print("=" * 80)
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    print("\n--- ENVIRONMENT VARIABLES ---")
    for key, value in sorted(os.environ.items()):
        print(f"{key}={value}")
    
    print("\n--- DIRECTORY CONTENTS ---")
    for item in sorted(os.listdir('.')):
        print(f"  {item}")
    
    print("\n--- NETWORK BINDING TEST ---")
    port = os.environ.get('PORT', '8000')
    host = '0.0.0.0'
    print(f"Attempting to bind to {host}:{port}")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, int(port)))
        sock.listen(1)
        print(f"✅ Successfully bound to {host}:{port}")
        sock.close()
    except Exception as e:
        print(f"❌ Failed to bind to {host}:{port}: {e}")
    
    print("\n--- PROCESS INFO ---")
    print(f"Process ID: {os.getpid()}")
    print(f"User ID: {os.getuid()}")
    
    print("=" * 80)
    print("Debug complete. Keeping container alive for 60 seconds...")
    time.sleep(60)
    print("Exiting.")

if __name__ == '__main__':
    main() 