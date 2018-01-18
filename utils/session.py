#coding:utf-8

import uuid
import json
import logging
import config

class Session(object):
    """"""
    def __init__(self,request_handler_obj):
        # 先判断用户是否已经有了session_id
        self.request_handler = request_handler_obj
        self.session_id = self.request_handler.get_secure_cookie("session_id")
        # 如果不存在，则生成一个
        if not self.session_id:
            self.session_id = uuid.uuid4().get_hex()
            self.data = {}
            self.request_handler.set_secure_cookie("session_id", self.session_id)

        # 如果存在session_id ，到redis中取出data
        else:
            try:
                json_data = self.request_handler.redis.get("sess_%s" % self.session_id)
            except Exception as e:
                logging.error(e)
                raise e
            if not json_data:
                self.data = {}
            else:
                self.data = json.loads(json_data)


    def save(self):
        json_data = json.dumps(self.data)
        try:
            self.request_handler.redis.setex("sess_%s" % self.session_id,config.session_expires, json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("save session failed")

    def clear(self):
        self.request_handler.clear_cookie("session_id")
        try:
            self.request_handler.redis.delete("sess_%s" % self.session_id)
        except Exception as e:
            logging.error(e)

