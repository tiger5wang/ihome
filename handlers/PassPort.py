#coding:utf-8

import logging
import re
import hashlib
from .BaseHandler import *
from utils.response_code import RET
from utils.session import Session
from utils.common import required_login



class IndexHandler(BaseHandler):
    def get(self):
        # self.application.db
        # self.application.redis
        logging.debug("debug")
        logging.info("info")
        logging.warning("warning")
        logging.error("error")

        self.write("hello world")


class RegisterHandler(BaseHandler):
    """注册"""
    def post(self):
        # 获取参数
        mobile = self.json_data.get("mobile")
        phoneCode = self.json_data.get("phoneCode")
        passwd = self.json_data.get("passwd")

        # 参数校验
        if not all((mobile, phoneCode, passwd)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数缺失"))
        if not re.match(r"^1\d{10}$",mobile):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="手机号格式错误"))
        if len(passwd) < 6:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="密码至少6位"))

        # 验证短信验证码是否正确
        try:
            real_phone_code = self.redis.get("sms_code_%s" % mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询短信验证码出错"))
        if phoneCode != real_phone_code:
            return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
        if not real_phone_code:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))

        # 验证通过,将信息保存到数据库中，同时验证手机号是否存在，判断的依据是数据库中mobile字段的唯一约束
        passwd = hashlib.sha1(passwd).hexdigest()
        try:
            sql = "insert into tor_user_info(ui_name, ui_mobile, ui_passwd) values(%(name)s,%(mobile)s,%(passwd)s)"
            user_id = self.db.execute(sql, name = mobile, mobile = mobile, passwd = passwd)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAEXIST, errmsg="手机号已经存在"))

        # 写session
        session = Session(self)
        session.data["user_id"] = user_id
        session.data["mobile"] = mobile
        session.data["name"] = mobile
        try:
            session.save()
        except Exception as e:
            logging.error(e)

        self.write(dict(errcode=RET.OK, errmsg="注册成功"))


class LoginHandler(BaseHandler):
    """登录"""
    def post(self):
        # 获取参数
        mobile = self.json_data.get("mobile")
        passwd = self.json_data.get("password")

        # 验证参数
        if not all((mobile, passwd)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数缺失"))
        if not re.match(r"^1\d{10}$",mobile):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="手机号格式错误"))

        # 检查手机号，密码是否正确
        try:
            sql = "select ui_user_id, ui_name, ui_mobile, ui_passwd from tor_user_info where ui_mobile = %(mobile)s"
            res = self.db.get(sql,mobile=mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="手机号错误1"))
            # return self.render("login.html")
        if not res:
            return self.write(dict(errcode=RET.DATAERR, errmsg="手机号错误"))
        if res["ui_passwd"] != unicode(passwd):
            return self.write(dict(errcode=RET.DATAERR, errmsg="密码错误"))

        # 生成session数据
        session = Session(self)
        session.data["user_id"] = res["ui_user_id"]
        session.data["mobile"] = res["ui_mobile"]
        session.data["name"] = res["ui_name"]
        try:
            session.save()
        except Exception as e:
            logging.error(e)
        return self.write(dict(errcode=RET.OK, errmsg="OK"))


class CheckLoginHandler(BaseHandler):
    """检查登录"""
    def get(self):
        if self.get_current_user():
            self.write({"errcode":RET.OK,"errmsg":"true", "data":{"name":self.session.data.get("name")}})
        else:
            self.write({"errcode":RET.SESSIONERR, "errmsg":"false"})





class LogoutHandler(BaseHandler):
    """退出"""
    @required_login
    def get(self):
        self.session.clear()
        self.write(dict(errcode=RET.OK, errmsg="OK"))