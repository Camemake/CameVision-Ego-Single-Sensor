#!/usr/bin/env python3
import socket
import time

HOST = "192.168.1.23"
PORT = 8554
URL = "rtsp://192.168.1.23:8554/live"


def rtsp(sock, body):
    sock.sendall(body.encode())
    sock.settimeout(5)
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\r\n\r\n" in data:
            head, rest = data.split(b"\r\n\r\n", 1)
            # content-length
            headers = head.decode("utf-8", "replace")
            cl = 0
            for line in headers.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    cl = int(line.split(":", 1)[1].strip() or 0)
            if len(rest) >= cl:
                return headers, rest[:cl], rest[cl:]
    return data.decode("utf-8", "replace"), b"", b""


def main():
    s = socket.create_connection((HOST, PORT), 6)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    h, b, extra = rtsp(
        s,
        "OPTIONS %s RTSP/1.0\r\nCSeq: 1\r\n\r\n" % URL,
    )
    print("OPTIONS\n", h, "\n")
    h, b, extra = rtsp(
        s,
        "DESCRIBE %s RTSP/1.0\r\nCSeq: 2\r\nAccept: application/sdp\r\n\r\n" % URL,
    )
    print("DESCRIBE\n", h, "\n", b.decode("utf-8", "replace"), "\n")
    h, b, extra = rtsp(
        s,
        "SETUP %s/streamid=0 RTSP/1.0\r\nCSeq: 3\r\nTransport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n\r\n"
        % URL,
    )
    print("SETUP\n", h, "\n")
    sess = "1"
    for line in h.splitlines():
        if line.lower().startswith("session:"):
            sess = line.split(":", 1)[1].strip().split(";")[0].strip()
    h, b, extra = rtsp(
        s,
        "PLAY %s RTSP/1.0\r\nCSeq: 4\r\nSession: %s\r\n\r\n" % (URL, sess),
    )
    print("PLAY\n", h, "\n")
    s.settimeout(3)
    got = extra
    t0 = time.time()
    interleaved = 0
    bytes_ = len(extra)
    while time.time() - t0 < 3:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        got += chunk
        bytes_ += len(chunk)
        interleaved += chunk.count(b"$")
    print("rtp_bytes", bytes_, "dollar_marks", interleaved, "first", got[:16])
    s.close()


if __name__ == "__main__":
    main()
