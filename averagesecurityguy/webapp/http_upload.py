#!/usr/bin/python
# -*- coding: utf-8 -*-

import BaseHTTPServer
import random

SERVER = '10.230.229.11'
PORT = 8080

def get_filename():
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    fn = ''.join([random.choice(chars) for i in xrange(12)])

    return fn


class PostHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        length = self.headers['content-length']
        data = self.rfile.read(int(length))

        fn = get_filename()
        with open(fn, 'w') as fh:
            fh.write(data.decode())

        self.send_response(200)

        return

    def do_GET(self):
        page = '''
        <h1>Upload a File</h1>
        <form action="/" method="post" enctype="multipart/form-data">
        <input type="file" name="file" placeholder="Enter a filename."></input><br />
        <input type="submit" value="Import">
        </form>
        '''

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page)


if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer((SERVER, PORT), PostHandler)
    print 'Starting server on {0}:{1}, use <Ctrl-C> to stop'.format(SERVER, PORT)
    server.serve_forever()
