#coding=utf-8
import os

# Application 配置参数
setting = dict(
    static_path = os.path.join(os.path.dirname(__file__),"static"),
    template_path = os.path.join(os.path.dirname(__file__),"template"),
    cookie_secret = 'fLZn3EIIT06vQasv8krDfOwqCIpFE0DIjbV10e0ai3o=',
    xsrf_cookies = True,
    debug = True,
)

# 数据库配置参数
mysql_options = dict(
    host="127.0.0.1",
    user="root",
    password="wanglaohu",
    database="tornado"
)

# Redis配置参数
redis_options = dict(
    host="127.0.0.1",
    port=6379
)

# log日志
log_level = "debug"
log_path = os.path.join(os.path.dirname(__file__),"logs/log")

session_expires = 86400