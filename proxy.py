import datetime
import http.server
import http.client
from socketserver import ForkingMixIn
import urllib.parse

from redis import Redis


redis = Redis(host='redis', port=6379)


def parse_range(range_str):
    if not range_str.startswith('bytes='):
        return None

    range_str = range_str[len('bytes='):]

    start, end = range_str.split('-')

    if not start:
        start = 0


class ForkedHTTPServer(ForkingMixIn, http.server.HTTPServer):
    """ Handle requests in a separate process. """


class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def stats(self):
        now = datetime.datetime.utcnow().timestamp()
        start_time = float(redis.get('start_time'))
        bytes_transferred = int(redis.get('bytes'), 10)

        uptime = now - start_time
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        stats = "Uptime: {}\nBytes transferred: {}\n".format(
            str(datetime.timedelta(seconds=uptime)), bytes_transferred)
        self.wfile.write(bytes(stats.encode('utf-8')))
        self.wfile.flush()

    def do_DELETE(self):
        self.do_GET()

    def do_POST(self):
        self.do_GET()

    def do_HEAD(self):
        self.do_GET()

    def do_PUT(self):
        self.do_GET()

    def do_TRACE(self):
        self.do_GET()

    def do_CONNECT(self):
        self.do_GET()

    def do_GET(self):
        if self.path == '/stats':
            self.stats()
        else:
            url = urllib.parse.urlparse(self.path)

            query_data = urllib.parse.parse_qs(url.query)

            range_query = query_data.get('range', [''])[0]
            range_header = self.headers.get('Range')

            if range_query and range_header and range_query != range_header:
                self.send_error(416)

            body = b''
            conn = http.client.HTTPConnection(url.netloc)
            conn.request(self.command, self.path, url.params, self.headers)
            response = conn.getresponse()
            headers = response.headers

            body = response.read()
            if range_header:
                range_str = range_header
            elif range_query:
                range_str = range_query
                # XXX: perhaps we should remove 'range' from query string but
                # there is no guarantee that 'range' is not an acceptable
                # query string parameter to some website so we leave it in
                # for now.
            else:
                range_str = None

            if range_str:
                range_str = range_str[len('bytes='):]
                start, end = range_str.split('-')
                if not start:
                    start = '0'

                start = int(start, 10)

                if not end:
                    end = str(len(body))
                end = int(end, 10)
                headers['Content-Range'] = 'bytes {}-{}/{}'.format(
                    start, end, len(body))
                body = body[start:end]

            self.send_response(response.status, response.reason)
            for header, value in headers.items():
                self.send_header(header, value)
            self.end_headers()

            byte_count = int(redis.get('bytes'), 10) + len(body)
            redis.set('bytes', byte_count)
            self.wfile.write(bytes(body))


def run(server_class=ForkedHTTPServer,
        handler_class=ProxyHTTPRequestHandler):
    start_time = datetime.datetime.utcnow().timestamp()

    # store data to be shared with forked child processes in redis
    redis.set('start_time', start_time)
    redis.set('bytes', 0)
    server_address = ('', 8080)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


if __name__ == "__main__":
    run()
