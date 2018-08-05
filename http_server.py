import socket
import sys
from io import StringIO
from contextlib import redirect_stdout


def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->
        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b"\r\n".join([
            b"HTTP/1.1 200 OK",
            b"Content-Type: " + mimetype,
            b"",
            body,
    ])


def parse_request(request):
    """
    Given the content of an HTTP request, returns the uri of that request.
    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    method, path, version = request.split("\r\n")[0].split(' ')

    if method != 'GET':
        raise NotImplementedError

    return path


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return b"\r\n".join([
        b"HTTP/1.1 405 Method Not Allowed",
        b"Content-Type: text/html",
        b"",
        b"Method Not Allowed."
    ])


def response_not_found():
    """Returns a 404 Not Found response"""
    return b"\r\n".join([
        b"HTTP/1.1 404 Not Found",
        b"Content-Type: text/html",
        b"",
        b"Page not found."
    ])
    

def resolve_uri(uri):
    """
    This method should return appropriate content and a mime type.
    If the requested URI is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.
    If the URI is a file, it should return the contents of that file
    and its correct mimetype.
    If the URI does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.
    Ex:
        resolve_uri('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")
        resolve_uri('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")
        resolve_uri('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")
        resolve_uri('/a_page_that_doesnt_exist.html') -> Raises a NameError
    """
    if uri == '/':
        content = b"images/\r\na_web_page.html\r\nmake_time.py\r\nsample.txt\r\n"
        mime_type = b"text/plain"

    elif uri == '/a_web_page.html':
        content = open("webroot/a_web_page.html", "rb").read()
        mime_type = b"text/html"

    elif uri == '/sample.txt':
        content = open("webroot/sample.txt", "rb").read()
        mime_type = b"text/plain"

    elif uri[:7] == '/images':
        if uri[8:] == '':
            content = b"JPEG_example.jpg\r\nsample_1.png\r\nSample_Scene_Balls.jpg\r\n"
            mime_type = b"text/plain"
        else:
            try:
                content = open("webroot/images/" + uri[8:], "rb").read()
                mime_type = b"image/" + {'jpg': 'jpeg', 'png': 'png'}[uri[-3:]].encode()
            except FileNotFoundError:
                raise NameError

    elif uri[-2:] == 'py':
        try:
            f = StringIO()
            with redirect_stdout(f):
                exec(open("webroot" + uri).read())
            content = f.getvalue().encode()
            mime_type = b"text/html"
        except FileNotFoundError:
            raise NameError
    else:
        raise NameError

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    path = parse_request(request)
                    try:
                        con, mime = resolve_uri(path)
                        response = response_ok(
                            body=con,
                            mimetype=mime
                        )
                    except NameError:
                        response = response_not_found()
                except NotImplementedError:
                    response = response_method_not_allowed()

                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return


if __name__ == '__main__':
    server()
    sys.exit(0)
