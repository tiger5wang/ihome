# coding:utf-8
import json
import tornado.web
from tornado.web import RequestHandler
from utils.session import Session

class BaseHandler(RequestHandler):
    """handler基类"""

    # 成员方法当属性对待时，需要用@property装饰器
    @property
    def db(self):
        return self.application.db

    # 成员方法当属性对待时，需要用@property装饰器
    @property
    def redis(self):
        return self.application.redis


    def initialize(self):
        pass

    def set_default_headers(self):
        self.set_header("Content-Type","application/json; charset=utf-8")

    def prepare(self):
        self.xsrf_token
        if self.request.headers.get("Content-Type","").startswith("application/json"):
            self.json_data = json.loads(self.request.body)
        else:
            self.json_data = {}

    def write_error(self,status_code, **kwargs):
        pass

    def on_finish(self):
        pass

    def get_current_user(self):
        """判断用户是否登陆成功"""
        self.session = Session(self)
        return self.session.data


class StaticFileHandler(tornado.web.StaticFileHandler):
    """自定义静态文件处理类，
    在用户获取html页面时设置_xsrf的cookie"""
    def __init__(self, *args, **kwargs):
        super(StaticFileHandler, self).__init__(*args, **kwargs)
        self.xsrf_token

