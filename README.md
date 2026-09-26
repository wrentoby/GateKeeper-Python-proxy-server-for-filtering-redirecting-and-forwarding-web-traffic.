# GateKeeper-Python-proxy-server-for-filtering-redirecting-and-forwarding-web-traffic.
A multithreaded Python proxy server designed to monitor and manage web traffic by blocking selected websites, redirecting domains, forwarding requests, and logging network activity.

Features:
* HTTP request forwarding
* HTTPS `CONNECT` tunneling
* Website blocking
* Domain redirection
* Request logging
* Multithreaded client handling
* Simple and lightweight implementation using Python sockets

Technologies Used
* Python
* Socket Programming
* Multithreading
* HTTP/HTTPS
* TCP/IP

Configuration
You can modify the proxy settings directly in the Python file:
```python
HOST = "127.0.0.1"
PORT = 8888
BLOCKED_SITES = ["facebook.com", "youtube.com"]
REDIRECT_RULES = {
    "awwwards.com": "example.com"
}
```

Running the Proxy
Run:
```bash
python proxy.py
```
The proxy will start on:
```text
127.0.0.1:8888
```
Configure your browser or application to use this address as its HTTP/HTTPS proxy.

## ⚠
