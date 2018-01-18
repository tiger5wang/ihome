# coding:utf-8

import functools
# from handlers.BaseHandler import BaseHandler
from .response_code import RET
# from .session import Session

def required_login(fun):
    # 保证装饰的函数对象的__name__不变
    @functools.wraps(fun)
    def wrapper(request_handler_obj, *args, **kwargs):
        # 调用get_current_user()方法，如果登录则会又返回值，没有登录则返回值为空
        if request_handler_obj.get_current_user():
        # session = Session(request_handler_obj)
        # if session.data:
            fun(request_handler_obj, *args, **kwargs)
        else:
            request_handler_obj.write(dict(errcode=RET.SESSIONERR, errmsg="用户未登录"))
    return wrapper
