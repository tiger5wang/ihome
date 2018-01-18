# coding:utf-8

import logging, datetime, constants

from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import required_login

class OrderHandler(BaseHandler):
    """订单"""
    @required_login
    def post(self):
        """提交订单"""
        user_id = self.session.data["user_id"]
        house_id = self.json_data.get("house_id")
        start_date = self.json_data.get("start_date")
        end_date = self.json_data.get("end_date")
        # 检查参数
        if not all((house_id, start_date, end_date)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))
        # 检查房屋是否存在
        try:
            sql = "select hi_price, hi_user_id from tor_house_info where hi_house_id=%s"
            house = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get house error"))
        if not house:
            return self.write(dict(errcode=RET.NODATA, errmsg="no data"))
        # 预定的房间是否是预定者自己的
        if user_id == house["hi_user_id"]:
            return self.write(dict(errcode=RET.ROLEERR, errmsg="user is forbidden"))
        # 判断日期是否可以
        # start_date 与 end_date 两个参数是字符串， 需要转为datetime 类型进行比较
        # 比较 start_date 是否比end_date小
        days = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date, "%Y-%m-%d")).days
        if days<0:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="data params error"))
        # 确保用户预定的时间内，房屋没有被别人下单
        try:
            sql = "select count(*) counts from tor_order_info where oi_house_id=%(house_id)s and oi_begin_date<%(end_date)s and oi_end_date>%(start_date)s"
            ret = self.db.get(sql, house_id=house_id, start_date=start_date, end_date=end_date)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get date error"))
        if ret["counts"] > 0:
            return self.write(dict(errcode=RET.DATAERR, errmsg="datetime error"))
        amount = days * house["hi_price"]
        # 保存订单数据
        try:
            sql = "insert into tor_order_info(oi_user_id,oi_house_id,oi_begin_date,oi_end_date,oi_days,oi_house_price,oi_amount) values (%(user_id)s,%(house_id)s,%(begin_date)s,%(end_date)s,%(days)s,%(price)s,%(amount)s);" \
                  "update ih_house_info set hi_order_count=hi_order_count+1 where hi_house_id=%(house_id)s;"
            self.db.execute(sql, user_id=user_id, house_id=house_id, begin_date=start_date, end_date=end_date, days=days, price=house["hi_price"], amount=amount)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"save data error"})
        self.write({"errcode":RET.OK, "errmsg":"OK"})


class MyOrdersHandler(BaseHandler):
    """我的订单"""
    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        # 用户的身份，用户想要作为房客查询下单，还是想要查询作为房东被人下的单
        role = self.get_argument("role", "")
        try:
            # 查询房东订单
            if "landlord" == role:
                sql = "select oi_order_id,hi_title,hi_index_image_url,oi_begin_date,oi_end_date,oi_ctime,oi_days,oi_amount,oi_status,oi_comment from tor_order_info inner join tor_house_info on oi_house_id=hi_house_id where hi_user_id=%s order by oi_ctime desc;"
                ret = self.db.query(sql, user_id)
            else:
                sql = "select oi_order_id,hi_title,hi_index_image_url,oi_begin_date,oi_end_date,oi_ctime,oi_days,oi_amount,oi_status,oi_comment from tor_order_info inner join tor_house_info on oi_house_id=hi_house_id where oi_user_id=%s order by oi_ctime desc;"
                ret = self.db.query(sql, user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"get data error"})
        orders = []
        if ret:
            for l in ret:
                order = {
                    "order_id":l["oi_order_id"],
                    "title":l["hi_title"],
                    "img_url":constants.QINIU_URL_PREFIX + "/" + l["hi_index_image_url"] if l["hi_index_image_url"] else "",
                    "start_date":l["oi_begin_date"].strftime("%Y-%m-%d"),
                    "end_date":l["oi_end_date"].strftime("%Y-%m-%d"),
                    "ctime":l["oi_ctime"].strftime("%Y-%m-%d"),
                    "days":l["oi_days"],
                    "amount":l["oi_amount"],
                    "status":l["oi_status"],
                    "comment":l["oi_comment"] if l["oi_comment"] else ""
                }
                orders.append(order)
        self.write({"errcode":RET.OK, "errmsg":"OK", "orders":orders})


class AcceptOrdersHandler(BaseHandler):
    """接单"""
    @required_login
    def post(self):
        # 处理的订单编号
        order_id = self.json_data.get("order_id")
        user_id = self.session.data["user_id"]
        if not order_id:
            return self.write({"errcode":RET.PARAMERR, "errmsg":"params error"})

        try:
            # 确保房东只能修改属于自己的房子的订单
            sql = "update tor_order_info set oi_status=3 where oi_order_id=%(order_id)s and oi_house_id in (select hi_house_id from tor_house_info where hi_user_id=%(user_id)s) and oi_status=0"
            self.db.execute(sql, order_id=order_id,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"DB error"})
        self.write({"errcode":RET.OK, "errmsg":"OK"})


class RejectOrdersHandler(BaseHandler):
    """接单"""
    @required_login
    def post(self):
        # 处理的订单编号
        order_id = self.json_data.get("order_id")
        user_id = self.session.data["user_id"]
        reject_reason = self.json_data.get("reject_reason")
        if not all((order_id, user_id, reject_reason)):
            return self.write({"errcode":RET.PARAMERR, "errmsg":"params error"})

        try:
            # 确保房东只能修改属于自己的房子的订单
            sql = "update tor_order_info set oi_status=6,oi_comment=%(reject_reason)s where oi_order_id=%(order_id)s and oi_house_id in (select hi_house_id from tor_house_info where hi_user_id=%(user_id)s) and oi_status=0"
            self.db.execute(sql, reject_reason=reject_reason, order_id=order_id,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"DB error"})
        self.write({"errcode":RET.OK, "errmsg":"OK"})


class CommentOrdersHandler(BaseHandler):
    """接单"""
    @required_login
    def post(self):
        # 处理的订单编号
        order_id = self.json_data.get("order_id")
        user_id = self.session.data["user_id"]
        comment = self.json_data.get("comment")
        if not all((order_id, user_id, comment)):
            return self.write({"errcode":RET.PARAMERR, "errmsg":"params error"})

        try:
            # 确保房客只能修改属于自己的订单
            sql = "update tor_order_info set oi_status=4,oi_comment=%(comment)s where oi_order_id=%(order_id)s and oi_house_id in (select hi_house_id from tor_house_info where hi_user_id=%(user_id)s) and oi_status=3;"
            result = self.db.execute_rowcount(sql, comment=comment, order_id=order_id,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode":RET.DBERR, "errmsg":"DB error"})
        oi_status = self.db.get("select oi_status from tor_order_info where oi_order_id=%s", order_id)
        print("oi_status:%s" % oi_status)
        # 同步更新redis缓存中关于该房屋的评论信息，此处的策略是直接删除redis缓存中的该房屋数据
        try:
            sql = "select oi_house_id from tor_order_info where oi_order_id=%s"
            ret = self.db.get(sql, order_id)
            if ret:
                self.redis.delete("house_info_%s" % ret["oi_house_id"])

        except Exception as e:
            logging.error(e)
        print("redis删除成功")
        self.write({"errcode":RET.OK, "errmsg":"OK"})
