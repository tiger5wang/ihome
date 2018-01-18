# coding=utf-8

import logging
import constants
import re
import random

from constants import PIC_CODE_EXPIRES_SECONDS
from .BaseHandler import BaseHandler
from utils.captcha.captcha import captcha
from utils.response_code import RET
from libs.yuntongxun.SendTemplateSMS import CCP


class PicCodeHandler(BaseHandler):
    """图片验证码"""
    def get(self):
        """获取图片验证码"""
        code_id = self.get_argument("codeid")
        prev_code_id = self.get_argument("pcodeid","")
        if prev_code_id:
            try:
                self.redis.delete("image_code_%s" % prev_code_id)
            except Exception as e:
                logging.error(e)
        # name 图片验证码名称
        # text 图片验证码文本
        # image 图片验证码二进制数据
        name,text,image = captcha.generate_captcha()
        # print image
        # print text
        try:
            self.redis.setex("image_code_%s" % code_id,constants.PIC_CODE_EXPIRES_SECONDS,text)
        except Exception as e:
            logging.error(e)
        else:
            self.set_header("Content-Type", "image/jpg")
            self.write(image)


class SMSCodeHandler(BaseHandler):
    """短信验证码"""
    def post(self):
        # 获取参数
        mobile = self.json_data.get("mobile")
        image_code_id = self.json_data.get("image_code_id")
        image_code_text = self.json_data.get("image_code_text")
        #参数校验
        if not all((mobile, image_code_id, image_code_text)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数缺失"))
        if not re.match(r"^1\d{10}$",mobile):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="手机号格式错误"))
        # 判断验证码
        try:
            real_code_text = self.redis.get("image_code_%s" % image_code_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR,errmsg="查询出错"))
        if not real_code_text:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))
        if real_code_text.lower() != image_code_text.lower():
            return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
        # 若验证通过
        # 生成4位随机验证码，并保存到redis库中
        sms_code = "%04d" % random.randint(0,9999)
        try:
            self.redis.setex("sms_code_%s" %mobile, constants.SMS_CODE_EXPIRES_SECONDS,sms_code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="生成短信验证码错误"))
        # 发送短信
        try:
            CCP.instance().sendTemplateSMS(mobile, [sms_code, constants.SMS_CODE_EXPIRES_SECONDS], 1)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.THIRDERR, errmsg="短信发送失败"))
        self.write(dict(errcode=RET.OK, errmsg="ok"))











