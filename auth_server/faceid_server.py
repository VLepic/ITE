import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.log
from urllib.request import urlopen
import datetime as dt
import logging
from recognize_handler import RecognizeImageHandler
from LoginPasswordHandler import UPLoginHandler
from userinfohandler import UserInfoHandler
from changepasswordhandler import ChangePasswordHandler
from RegisterHandler import RegisterHandler
import bcrypt
import psycopg2
import os
import secrets
import base64


tornado.log.enable_pretty_logging()
app_log = logging.getLogger("tornado.application")



class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World")


class ReceiveImageHandler(tornado.web.RequestHandler):
    def post(self):
        # Convert from binary data to string
        received_data = self.request.body.decode()

        assert received_data.startswith("data:image/png"), "Only data:image/png URL supported"

        # Parse data:// URL
        with urlopen(received_data) as response:
            image_data = response.read()

        app_log.info("Received image: %d bytes", len(image_data))

        # Write an image to the file
        with open(f"images/img-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.png", "wb") as fw:
            fw.write(image_data)


application = tornado.web.Application([
    (r"/receive_image", ReceiveImageHandler),
    (r"/recognize", RecognizeImageHandler),
    (r"/login", UPLoginHandler),
    (r"/user_info", UserInfoHandler),
    (r"/change_password", ChangePasswordHandler),
    (r"/register", RegisterHandler),
    (r"/(.*)", tornado.web.StaticFileHandler, {"path": "static/", "default_filename": "index.html"}),
])

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
