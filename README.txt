Multi-thread Web Server for COMP2322

Name: Lo Pui Yan
Student ID: 24030873d
----------------------

Overview
--------
This is a multi-threaded web server implemented by using Python using socket programming. 
It supports HTTP/1.1 persistent connections, conditional requests, and five response status codes.

Requirements
------------
- Python 3.6 or higher
- No external libraries required

How to Run
----------
1. Open a terminal in the project folder.
2. For adding files, put the files in the www folder. 
   Initially, there will be index.html, test.txt and test.png
3. Start the server by entering "python webserver.py" in the terminal. 
   By default, the server listens on http://127.0.0.1:8080.
4. To stop the server, press Ctrl+Pause.

Testing the Server
------------------
You can test the server using a web browser or command-line tools like curl in terminal.

Basic GET requests (running in browser):
  - http://127.0.0.1:8080/ (for accessing index.html)
  - http://127.0.0.1:8080/test.txt (for accessing test.txt)
  - http://127.0.0.1:8080/test.png (for accessing test.png)

HEAD request (running in terminal):
  curl -I http://127.0.0.1:8080/test.txt

404 Not Found (running in browser):
  Access a non-existent file, such as: http://127.0.0.1:8080/nonexist.html

403 Forbidden (path traversal) (running in terminial):
  curl --path-as-is "http://127.0.0.1:8080/../"

400 Bad Request (running the badReq_test.py):
  Send an incomplete request (missing blank line). 
  Example Python script for testing:
     import socket
     s = socket.socket()
     s.connect(("127.0.0.1", 8080))
     s.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n")
     print(s.recv(1024).decode())
     s.close()

304 Not Modified (conditional GET) (running in terminal):
  1. Get the Last-Modified time by entering curl -I http://127.0.0.1:8080/test.txt
  2. Using that time in If-Modified-Since by entering 
     curl -H "If-Modified-Since: Sat, 25 Apr 2026 02:16:52 GMT" http://127.0.0.1:8080/test.txt -v

Persistent connection (keep-alive) (running in terminal):
  curl -v http://127.0.0.1:8080/test.txt http://127.0.0.1:8080/index.html
  Look for "Reusing existing connection" in the output.

Non-persistent connection (Connection: close) (running in terminal):
  curl -H "Connection: close" http://127.0.0.1:8080/test.txt -v

Logging
-------
All requests are logged to "server.log" in the same directory. 
Each line contains Timestamp, Client IP, Requested path, HTTP status code. 

Example: [2026-04-25 10:00:01] 127.0.0.1 requested "/test.txt" 200

Project Structure
-----------------
  ├── webserver.py       # Main server code
  ├── README.txt
  └── www/               # Web root (create manually or auto-generated)
      ├── index.html
      ├── test.txt
      └── test.png
