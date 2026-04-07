import socket
import sys
import ssl

class URL:
    def __init__(self, url):
        # example url
        # http://example.org/index.html
        self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file"]
        # file:///C:\Users\YeasirKhandaker\personal\browserEngineering\dummy\first.txt
        # did not handle linux file system
        # may need to convert \ to / later on if want to have uniform convention across windows and linux
        if self.scheme == "file":
            if url[0] == "/":
                url = url[1:]
            self.path = url
            return
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url = url + "/"
        
        self.host, url = url.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

        self.path = "/" + url
    
    def request(self):
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # example request
        # GET /index.html HTTP/1.1
        # HOST: example.org
        # Connection: close
        # User-Agent: demo-browser
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "HOST: {}\r\n".format(self.host)
        request += "Connection: {}\r\n".format("close")
        request += "User-Agent: {}\r\n".format("demo-browser")
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