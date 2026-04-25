import socket
import threading
import os
import time
import email.utils
from datetime import datetime

HOST = ''
PORT = 8080
WWW = './www'
LOGFILE = 'server.log'

logLock = threading.Lock()

def logReq(addr, path, status_code):
    clientIP = addr[0]
    accessTime = time.strftime("%Y-%m-%d %H:%M:%S")
    logEntry = f"[{accessTime}] {clientIP} requested \"{path}\" {status_code}\n"
    with logLock:
        with open(LOGFILE, 'a') as f:
            f.write(logEntry)
    print(logEntry.strip())

def client(sock, addr):
    try:
        # Timeout when receiving data
        sock.settimeout(5)
        alive = True
        while alive:
            data = b''
            while True:
                try:
                    part = sock.recv(4096)
                    if not part:
                        break
                    data += part
                    if b'\r\n\r\n' in data or b'\n\n' in data:
                        break
                except socket.timeout:
                    break
            if not data:
                break

            # 400 Bad Request message for missing blank line
            if b'\r\n\r\n' not in data and b'\n\n' not in data:
                errMsg = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<h1>400 Bad Request</h1>"
                sock.send(errMsg.encode())
                logReq(addr, "", 400)
                break

            text = data.decode('utf-8', errors='ignore')
            line = text.splitlines()
            if not line:
                break
            reqLine = line[0]
            parts = reqLine.split()
            if len(parts) < 2:
                errMsg = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<h1>400 Bad Request</h1>"
                sock.send(errMsg.encode())
                logReq(addr, "", 400)
                break
            method, path = parts[0], parts[1]
            method = method.upper()

             # Parse headers
            header = {}
            for i in line[1:]:
                if ': ' in i:
                    key, value = i.split(': ', 1)
                    header[key] = value
                elif i == '':
                    break

            # Determine connection persistence
            connHeader = header.get('Connection', '').lower()
            if connHeader == 'close':
                alive = False
            else:
                alive = True

            # Error message for other method
            if method != 'GET' and method != 'HEAD':
                errMsg = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<h1>400 Bad Request</h1>"
                sock.send(errMsg.encode())
                logReq(addr, path, 400)
                break

            # Path traversal protection
            if '..' in path or path.startswith('/..'):
                errMsg = f"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n<h1>403 Forbidden</h1>"
                sock.send(errMsg.encode())
                logReq(addr, path, 403)
                break

            if path == '/' or path == '':
                path = '/index.html'

            filepath = WWW + path

            if os.path.isdir(filepath):
                filepath = os.path.join(filepath, 'index.html')

            # Error message for file not found
            if not os.path.exists(filepath):
                errMsg = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<h1>404 Not Found</h1>"
                sock.send(errMsg.encode())
                logReq(addr, path, 404)
                break
            if not os.access(filepath, os.R_OK):
                errMsg = f"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n<h1>403 Forbidden</h1>"
                sock.send(errMsg.encode())
                logReq(addr, path, 403)
                break

            stat = os.stat(filepath)
            lastModified = email.utils.formatdate(stat.st_mtime, usegmt=True)
            filetype = os.path.splitext(filepath)[1].lower()
            # Checking file type
            if filetype == '.html':
                conType = 'text/html'
            elif filetype == '.txt':
                conType = 'text/plain'
            elif filetype == '.jpg':
                conType = 'image/jpg'
            elif filetype == '.png':
                conType = 'image/png'
            else:
                conType = 'application/octet-stream'

            # 304 Not Modified handling
            if_modified_since = header.get('If-Modified-Since')
            if if_modified_since:
                try:
                    client_dt = email.utils.parsedate_to_datetime(if_modified_since)
                    client_ts = int(client_dt.timestamp())
                    file_ts = int(stat.st_mtime)
                    if file_ts <= client_ts + 1:
                        resp304 = f"HTTP/1.1 304 Not Modified\r\n"
                        resp304 += f"Connection: {'keep-alive' if alive else 'close'}\r\n\r\n"
                        sock.send(resp304.encode())
                        logReq(addr, path, 304)
                        continue
                except (TypeError, ValueError, OverflowError):
                    pass

            # response
            body = b''
            if method == 'GET':
                with open(filepath, 'rb') as f:
                    body = f.read()
                contLen = len(body)
            else:
                contLen = stat.st_size

            resp = "HTTP/1.1 200 OK\r\n"
            header_str = f"Content-Type: {conType}\r\n"
            header_str += f"Content-Length: {contLen}\r\n"
            header_str += f"Last-Modified: {lastModified}\r\n"
            header_str += f"Connection: {'keep-alive' if alive else 'close'}\r\n\r\n"

            sock.send(resp.encode())
            sock.send(header_str.encode())
            if method == 'GET' and body:
                sock.send(body)

            logReq(addr, path, 200)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    # Create and bind server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on port {PORT}")

    # main
    try:
        while True:
            sock, addr = server.accept()
            t = threading.Thread(target=client, args=(sock, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()