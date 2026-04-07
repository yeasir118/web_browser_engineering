import socket
import sys

class URL:
    def __init__(self, url):
        # example url
        # http://example.org/index.html
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
    
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, 80))

        # example request
        # GET /index.html HTTP/1.0
        # HOST: example.org
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "HOST: {}\r\n".format(self.host)
        request += "\r\n"
        s.send(request.encode("utf8"))

        # example response
        # HTTP/1.0 200 OK
        # Age: 545933
        # Cache-Control: max-age=604800
        # Content-Type: text/html; charset=UTF-8
        # Date: Mon, 25 Feb 2019 16:49:28 GMT
        # Etag: "1541025663+gzip+ident"
        # Expires: Mon, 04 Mar 2019 16:49:28 GMT
        # Last-Modified: Fri, 09 Aug 2013 23:54:35 GMT
        # Server: ECS (sec/96EC)
        # Vary: Accept-Encoding
        # X-Cache: HIT
        # Content-Length: 1270
        # Connection: close
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        assert "trasnfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()

        return content
    
def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)
    load(URL(sys.argv[1]))