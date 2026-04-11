import socket
import sys
import ssl
import time
import gzip

# (scheme, host, port): socket
connections = {}

# (scheme, host, port): (content, max_age, cache_time)
cache = {}

MAX_ALLOWED_REDIRECTS = 3

class URL:
    def __init__(self, url, remaining_redirects=MAX_ALLOWED_REDIRECTS):
        self.remaining_redirects = remaining_redirects
        
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
        if self.remaining_redirects < 0:
            print(f"MAX NUMBER OF REDIRECTIONS EXCEEDED")
            return ""
        
        if self.scheme == "data":
            return self.path
        
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        
        key = (self.scheme, self.host, self.port)

        if key in cache:
            content, max_age, cache_time = cache.get(key)

            if max_age == "-1":
                return content
            
            max_age = int(max_age)

            current_time = time.time()
            cache_age = current_time - cache_time

            if cache_age <= max_age:
                print("Cache hit")
                return content
        
        if key in connections:
            s = connections[key]
        else:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            
            connections[key] = s

        # example request
        # GET /index.html HTTP/1.1
        # HOST: example.org
        # Connection: keep-alive
        # User-Agent: demo-browser
        # Accept-Encoding: gzip
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "HOST: {}\r\n".format(self.host)
        request += "Connection: {}\r\n".format("keep-alive")
        request += "User-Agent: {}\r\n".format("demo-browser")
        request += "Accept-Encoding: {}\r\n".format("gzip")
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
        response = s.makefile("rb")

        statusline = response.readline().decode("utf-8")
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline().decode("utf-8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        # assert "content-encoding" not in response_headers

        cache_control_directives = {}
        if "cache-control" in response_headers:
            directives = response_headers.get("cache-control").split(",")
            for directive in directives:
                if "=" in directive:
                    key, value = directive.split("=")
                    cache_control_directives[key.lower().strip()] = value.lower().strip()
                else:
                    cache_control_directives[directive.lower().strip()] = True

        # Redirection
        if int(int(status)/100) == 3:
            print(f"Redirect: {self.remaining_redirects}")
            
            redirect_location = response_headers.get("location", "")
            
            if redirect_location.startswith("/"):
                redirect_location = f"{self.scheme}://{self.host}{redirect_location}"
            
            load(URL(redirect_location, remaining_redirects=self.remaining_redirects-1))
            
            return ""

        transfer_encoding = response_headers.get("transfer-encoding", "").lower()
        content_length = int(response_headers.get("content-length", 0))
        connection_header = response_headers.get("connection", "").lower()
        
        if transfer_encoding == "chunked":
            body = b""
            while True:
                line = response.readline().strip()
                chunk_size = int(line, 16)
                
                if chunk_size == 0:
                    response.readline() # trailing CRLF after last chunk
                    break
                
                chunk = response.read(chunk_size)
                body += chunk
                response.readline() # skip CRLF after chunk
            content = body
        elif content_length > 0:
            content = response.read(content_length)
        else:
            content = response.read()
            s.close()
            connections.pop(key, None)

        if connection_header == "close":
            s.close()
            connections.pop(key, None)
        
        content_encoding = response_headers.get("content-encoding", "").lower() 
        if content_encoding == "gzip":
            content = gzip.decompress(content)
        
        content = content.decode("utf-8")

        if "no-store" not in cache_control_directives:
            current_time = time.time()
            cache[(self.scheme, self.host, self.port)] = (content, cache_control_directives.get("max-age", "-1"), current_time)

        return content
    
def lex(body, view_source=False):
    text = ""

    if view_source is True:
        for c in body:
            text += c
        return text

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
                    text += "<"
                elif content == "&gt;":
                    text += ">"
                else:
                    text += content
                
                i = j + 1
            else:
                text += c
                i += 1
        elif not in_tag:
            text += c
            i += 1
        else:
            i += 1
    
    return text

def load(url):
    body = url.request()
    text = lex(body, url.view_source)
    print(text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # print(f"Usage: {sys.argv[0]} <url>")
        # for i in range(3):
        #     load(URL("http://httpbin.org/anything"))
        # load(URL("http://example.org"))
        # load(URL("http://httpbin.org/stream/3"))
        for i in range(3):
            load(URL("http://example.org"))
        sys.exit(1)
    load(URL(sys.argv[1]))