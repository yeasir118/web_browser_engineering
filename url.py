import socket
import sys
import ssl

class URL:
    def __init__(self, url):
        # example url
        # http://example.org/index.html
        # http://example.org:8000/index.html
        # https://example.org/index.html
        # file:///C:\Users\YeasirKhandaker\personal\browserEngineering\dummy\first.txt
        # data:text/html,<h1>Hello world!</h1>
        # view-source:http://example.org
        self.scheme, url = url.split(":", 1)
        self.view_source = False

        assert self.scheme in ["http", "https", "file", "data", "view-source"]

        if self.scheme == "data":
            metadata, content = url.split(",", 1)
            self.path = content
            return
        
        if self.scheme == "file":
            url = url[3:]
            self.path = url
            return
        
        if self.scheme == "view-source":
            self.view_source = True
            self.scheme, url = url.split(":", 1)
        
        # assuming rest of the schemes follow "scheme://..." convention
        # so stripping the first two slashes
        url = url[2:]

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
        if self.scheme == "data":
            return self.path
        
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
    
def show(body, view_source=False):
    if view_source is True:
        for c in body:
            print(c, end="")
        return

    in_tag = False
    i = 0

    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
            i += 1
        elif c == ">":
            in_tag = False
            i += 1
        elif c == "&":
            j = i
            content = ""

            while j < len(body) and body[j] != ";":
                content += body[j]
                j += 1
            
            if j < len(body):
                content += ";"

                if content == "&lt;":
                    print("<", end="")
                elif content == "&gt;":
                    print(">", end="")
                else:
                    print(content, end="")
                
                i = j + 1
            else:
                print(c, end="")
                i += 1
        elif not in_tag:
            print(c, end="")
            i += 1
        else:
            i += 1

def load(url):
    body = url.request()
    show(body, url.view_source)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)
    load(URL(sys.argv[1]))