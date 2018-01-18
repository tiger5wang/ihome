#coding=utf-8

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado.options import define, options
import torndb
import redis
from config import *
from urls import urls

define("port",type=int,default=9000)

class Application(tornado.web.Application):
    """application实例类"""

    def __init__(self,*args, **kwargs):
        super(Application, self).__init__(*args,**kwargs)
        # 创建一个全局mysql实例供handler使用
        self.db = torndb.Connection(
            **mysql_options
        )
        # 创建一个全局redis实例
        self.redis = redis.StrictRedis(
            **redis_options
        )


def main():
    """主函数"""

    options.logging = log_level
    options.log_file_prefix = log_path
    tornado.options.parse_command_line()
    app = Application(
        urls,
        **setting
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()