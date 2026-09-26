import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 8888

BLOCKED_SITES = ["facebook.com", "youtube.com"]
REDIRECT_RULES = {
    "awwwards.com": "example.com"
}

# ---------- LOGGING FUNCTION ----------
def log(*args, **kwargs):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(ts, *args, **kwargs)

# ---------- RECEIVE ALL DATA ----------
def recv_all(sock, timeout=0.5):
    data = b""
    sock.settimeout(timeout)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    except Exception:
        pass
    return data

def normalize_host(host):
    return host.split(":")[0].lower()

# ---------- CHECK IF HOST IS BLOCKED ----------
def is_blocked(host):
    host = normalize_host(host)
    for blocked in BLOCKED_SITES:
        blocked = blocked.lower()
        if host == blocked or host.endswith("." + blocked):
            return True
    return False

# ---------- HANDLE CLIENT ----------
def handle_client(client_socket, client_address):
    request = recv_all(client_socket)
    if not request:
        client_socket.close()
        return

    try:
        request_str = request.decode(errors="ignore")
    except:
        request_str = ""

    # Extract host and method
    host = None
    first_line = request_str.split("\n")[0] if request_str else ""
    parts = first_line.split()
    method = parts[0] if len(parts) > 0 else ""

    # ---------- HTTPS (CONNECT) ----------
    if method.upper() == "CONNECT":
        host_port = parts[1] if len(parts) > 1 else ""
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 443
        host_norm = normalize_host(host)

        log("[CONNECT]", f"{client_address} -> {host_norm}:{port}")

        # Block HTTPS sites
        if is_blocked(host_norm):
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            client_socket.close()
            log("[BLOCKED]", f"{client_address} -> {host_norm}")
            return

        # HTTPS redirect notice
        for target, new_host in REDIRECT_RULES.items():
            if host_norm == target or host_norm.endswith("." + target):
                msg = (
                    "HTTP/1.1 200 Connection established\r\n\r\n"
                    f"<html><body><h1>Redirect Notice</h1>"
                    f"<p>You tried to access <b>{host_norm}</b></p>"
                    f"<p>Please visit <a href='http://{new_host}/'>{new_host}</a> instead.</p>"
                    "</body></html>"
                )
                client_socket.sendall(msg.encode())
                client_socket.close()
                log("[REDIRECT-HTTPS]", f"{client_address} {host_norm} -> {new_host}")
                return

        try:
            remote = socket.create_connection((host, port))
            client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            threading.Thread(target=tunnel, args=(client_socket, remote), daemon=True).start()
            threading.Thread(target=tunnel, args=(remote, client_socket), daemon=True).start()
        except Exception as e:
            log("[ERROR CONNECT]", e)
        return

    # ---------- HTTP REQUEST ----------
    for line in request_str.split("\n"):
        if line.lower().startswith("host:"):
            host = normalize_host(line.split(":", 1)[1].strip())
            break

    if not host:
        client_socket.close()
        return

    log("[REQUEST]", f"{client_address} {method} -> {host}")

    # ---------- BLOCK ----------
    if is_blocked(host):
        block_msg = (
            "HTTP/1.1 403 Forbidden\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n"
            "<html><body><h1>403 Forbidden</h1><p>Blocked by proxy</p></body></html>"
        )
        client_socket.sendall(block_msg.encode())
        client_socket.close()
        log("[BLOCKED]", f"{client_address} -> {host}")
        return

    # ---------- REDIRECT ----------
    for target, new_host in REDIRECT_RULES.items():
        if host == target or host.endswith("." + target):
            body = f"<html><body><h1>Redirected</h1><p>Redirecting to <a href='http://{new_host}/'>http://{new_host}/</a></p></body></html>"
            redirect_msg = (
                "HTTP/1.1 302 Found\r\n"
                f"Location: http://{new_host}/\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
                f"{body}"
            )
            client_socket.sendall(redirect_msg.encode())
            client_socket.close()
            log("[REDIRECT]", f"{client_address} {host} -> {new_host}")
            return

    # ---------- FORWARD ----------
    try:
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((host, 80))
        remote.sendall(request)
        response = recv_all(remote)
        client_socket.sendall(response)
        remote.close()
        client_socket.close()
        log("[FORWARDED]", f"{client_address} -> {host}")
    except Exception as e:
        log("[ERROR FORWARD]", e)

# ---------- DATA TUNNEL ----------
def tunnel(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.close()
        except:
            pass
        try:
            dst.close()
        except:
            pass

# ---------- MAIN SERVER ----------
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(100)

    print("="*60)
    print(" 🌐 SIMPLE PYTHON PROXY SERVER ")
    print("="*60)
    print(f"[*] Running on {HOST}:{PORT}\n")
    print("="*60, "\n")

    try:
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("Shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
