# coding:utf-8

import os
from handlers import PassPort, VerifyCode, Profile, House, Orders
from handlers.BaseHandler import StaticFileHandler


urls = [
    # (r"/",PassPort.IndexHandler),
    (r"/api/piccode",VerifyCode.PicCodeHandler),
    (r"/api/smscode",VerifyCode.SMSCodeHandler),
    (r"/api/register",PassPort.RegisterHandler),
    (r"/api/login",PassPort.LoginHandler),
    (r"/api/check_login",PassPort.CheckLoginHandler),
    (r"/api/logout",PassPort.LogoutHandler),
    (r"/api/profile",Profile.ProfileHandler),
    (r"/api/profile/avatar",Profile.AvatarHandler),
    (r"/api/profile/name",Profile.NameHandler),
    (r"/api/profile/auth",Profile.AuthHandler),
    (r"/api/house/index",House.IndexHandler),
    (r"/api/house/my",House.MyHouseHandler),
    (r"/api/house/area",House.AreaHandler),
    (r"/api/house/info",House.HouseInfoHandler),
    (r"/api/house/image",House.HouseImageHandler),
    (r"/api/house/list2",House.HouseListHandler),
    (r"/api/order",Orders.OrderHandler),
    (r"/api/order/my",Orders.MyOrdersHandler),
    (r"/api/order/accept",Orders.AcceptOrdersHandler),
    (r"/api/order/reject",Orders.RejectOrdersHandler),
    (r"/api/order/comment",Orders.CommentOrdersHandler),
    (r"/(.*)",StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__),"html"),default_filename="index.html")),

]