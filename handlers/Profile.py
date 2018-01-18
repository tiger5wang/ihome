# coding:utf-8

import logging
from .BaseHandler import BaseHandler
from utils.common import required_login
from utils.response_code import RET
from utils.image_storage import storage
import constants

class ProfileHandler(BaseHandler):
    """个人中心"""
    @required_login
    def get(self):
        user_id = self.session.data.get("user_id")
        try:
            sql = "select ui_name, ui_mobile, ui_avatar from tor_user_info where ui_user_id=%(user_id)s"
            res = self.db.get(sql, user_id=user_id)
            # print res
            name = res["ui_name"]
            mobile = res["ui_mobile"]
            avatar = res["ui_avatar"]
            # name = self.session.data.get("name")
            # mobile = self.session.data.get("mobile")
            # avatar = self.session.data.get("avatar")
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        self.write({"errcode":RET.OK,"errmsg":"true", "data":{"name":name, "mobile":mobile, "avatar":"%s/%s" %(constants.QINIU_URL_PREFIX,avatar)}})


class AvatarHandler(BaseHandler):
    """上传头像"""

    @required_login
    def post(self):
        files = self.request.files.get("avatar")
        if not files:
            return self.write(dict(errcode=RET.PARAMERR,errmsg="未传图片"))
        avatar = files[0]["body"]
        # 调用七牛上传图片
        try:
            file_name = storage(avatar)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.THIRDERR, errmsg="上传失败"))
        #从session数据中取出user_id
        user_id = self.session.data.get("user_id")
        # 保存图片名（即图片url)到数据库中
        sql = "update tor_user_info set ui_avatar=%(avatar)s where ui_user_id=%(user_id)s"
        try:
            row_count = self.db.execute_rowcount(sql,avatar=file_name, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="保存错误"))
        data = "%s/%s" % (constants.QINIU_URL_PREFIX, file_name)
        # print("url:%s" %data)
        print("avatar_row_count:%s" % row_count)
        self.session.data["avatar"] = data
        self.write(dict(errcode=RET.OK, errmsg="保存成功",data="%s/%s" % (constants.QINIU_URL_PREFIX, file_name)))


class NameHandler(BaseHandler):
    """上传用户名"""

    @required_login
    def post(self):
        # 获取用户id和用户名
        user_id = self.session.data.get("user_id")
        name = self.json_data.get("name")
        # 将更改的用户名保存到数据库中
        sql = "update tor_user_info set ui_name=%(name)s where ui_user_id=%(user_id)s"
        try:
            row_count = self.db.execute_rowcount(sql, name=name, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="保存错误"))
        print("name_row_count:%s" % row_count)
        self.session.data["name"] = name
        self.write(dict(errcode=RET.OK, errmsg="保存成功"))


class AuthHandler(BaseHandler):
    """实名认证"""
    @required_login
    def get(self):
        """获取信息"""
        # 获取用户id，根据id从数据库中取出real_name 和id_card
        user_id = self.session.data.get("user_id")
        sql = "select ui_real_name, ui_id_card from tor_user_info where ui_user_id=%(user_id)s"
        try:
            res = self.db.get(sql, user_id=user_id)
            real_name = res["ui_real_name"]
            id_card = res["ui_id_card"]
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))
        if not (real_name and id_card):
            return self.write(dict(errcode=RET.DATAERR, errmsg="信息不完整"))
        print("real_name:%s,id_card:%s" % (real_name, id_card))
        self.write(dict(errcode=RET.OK, errmsg="OK", data=dict(real_name=real_name, id_card=id_card)))

    @required_login
    def post(self):
        """提交信息"""
        # 获取用户id
        user_id = self.session.data.get("user_id")
        print user_id
        # 获取用户提交的信息
        real_name = self.json_data.get("real_name")
        id_card = self.json_data.get("id_card")
        # 将信息保存到数据库中
        sql = "insert into tor_user_info(ui_real_name, ui_id_card) values(%(real_name)s,%(id_card)s) where ui_user_id=%(user_id)s"
        try:
            execute_count = self.db.execute_rowcount(sql, real_name=real_name,id_card=id_card, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="保存错误"))
        print("auth_execute_count:%s" % execute_count)

        self.write(dict(errcode=RET.OK, errmsg="OK"))



















