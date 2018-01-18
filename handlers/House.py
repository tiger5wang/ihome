# coding:utf-8

import logging, json, math
import constants
from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import required_login
from utils.image_storage import storage
from utils.session import Session



class IndexHandler(BaseHandler):
    """主页信息"""
    def get(self):
        try:
            ret = self.redis.get("home_page_data")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            json_houses =ret
        else:
            try:
                # 查询数据库，返回房屋订单数目最多的5条数据（房屋订单通过hi_order_count来表示）
                sql = "select hi_house_id, hi_title, hi_order_count, hi_index_image_url from tor_house_info where hi_online_status=1 order by hi_order_count desc limit %s;"
                house_ret = self.db.query(sql, constants.HOME_PAGE_MAX_HOUSES)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="no data"))
            houses = []
            for l in house_ret:
                if not l["hi_index_image_url"]:
                    continue
                house = dict(
                    house_id = l["hi_house_id"],
                    title = l["hi_title"],
                    img_url = constants.QINIU_URL_PREFIX + "/" + l["hi_index_image_url"]
                )
                houses.append(house)
            json_houses = json.dumps(houses)
            try:
                self.redis.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES_SECONDS, json_houses)
            except Exception as e:
                logging.error(e)

        # 返回首页城区数据
        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            json_areas = ret
        else:
            try:
                sql = "select ai_area_id, ai_name from tor_area_info"
                area_ret = self.db.query(sql)
            except Exception as e:
                logging.error(e)
                area_ret = None
            areas = []
            if area_ret:
                for area in area_ret:
                    areas.append(dict(area_id=area["ai_area_id"], name=area["ai_name"]))
            json_areas = json.dumps(areas)
            try:
                self.redis.setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDES, json_areas)
            except Exception as e:
                logging.error(e)
        resp = '{"errcode":"0", "errmsg":"ok", "houses":%s, "areas":%s}' % (json_houses, json_areas)
        self.write(resp)


class MyHouseHandler(BaseHandler):
    """我的房源"""
    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        # 从数据库获取房屋信息
        try:
            sql = "select hi_house_id, hi_title, hi_price, hi_index_image_url, hi_ctime, ai_name from tor_house_info inner join tor_area_info on hi_area_id=ai_area_id where hi_user_id=%(user_id)s"

            ret = self.db.query(sql, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询错误"))
        # 将房屋信息整理成json形式，便于前端获取
        houses = []
        for h in ret:
            house = dict(
                house = h["hi_house_id"],
                title = h["hi_title"],
                price = h["hi_price"],
                area_name = h["ai_name"],
                img_url = constants.QINIU_URL_PREFIX + "/" + h["hi_index_image_url"] if h["hi_index_image_url"] else "",
                ctime = h["hi_ctime"].strftime("%Y-%m-%d")  #将返回的datetime类型转为为字符串
            )
            print house["img_url"]
            houses.append(house)
            # print("houses:%s" % houses)
        self.write(dict(errcode=RET.OK, errmsg="ok", houses=houses))


class AreaHandler(BaseHandler):
    """房源区域"""
    def get(self):
        # 先到redis 中查询数据，如果得到了数据，直接返回给用户
        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            """
            此时从redis中读取的数据ret是json格式字符串
            ret = "[]"
            需要回传的相应数据格式json，形如：
            ‘{"errcode":"0", "errmsg":"ok", "data":ret}’
            """
            logging.info("hit redis:area_info")
            # resp = '{"errcode":RET.OK, "errmsg":"ok", "data":ret}'
            # print resp.data[1].area_id
            ret = json.loads(ret)

            return self.write({"errcode":RET.OK, "errmsg":"ok", "data":ret})

        # 若redis中没有，则到MySQL数据库中查询区域信息
        sql = "select ai_area_id, ai_name from tor_area_info;"
        try:
            ret = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="没有数据"))
        # 保存转换好的区域 信息
        data = []
        for row in ret:
            area = {
                "area_id": row.get("ai_area_id", ""),
                "name": row.get("ai_name", "")
            }
            data.append(area)

        # 在返回给用户数据之前，先向redis中保存一份数据
        json_data = json.dumps(data)
        try:
            self.redis.setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDES,json_data)
        except Exception as e:
            logging.error(e)

        self.write(dict(errcode=RET.OK, errmsg="ok", data=data))


class HouseInfoHandler(BaseHandler):
    """房屋信息"""
    @required_login
    def post(self):
        """添加新房源"""
        # 获取信息
        """
                {
                    "title":"",
                    "price":"",
                    "area_id":"1",
                    "address":"",
                    "room_count":"",
                    "acreage":"",
                    "unit":"",
                    "capacity":"",
                    "beds":"",
                    "deposit":"",
                    "min_days":"",
                    "max_days":"",
                    "facility":["7","8"]
                }
        """
        user_id = self.session.data["user_id"]
        title = self.json_data.get("title")
        price = self.json_data.get("price")
        area_id = self.json_data.get("area_id")
        address = self.json_data.get("address")
        room_count = self.json_data.get("room_count")
        acreage = self.json_data.get("acreage")
        house_unit = self.json_data.get("unit")
        capacity = self.json_data.get("capacity")
        beds = self.json_data.get("beds")
        deposit = self.json_data.get("deposit")
        min_days = self.json_data.get("min_days")
        max_days = self.json_data.get("max_days")
        facility = self.json_data.get("facility")  # 对于房屋的设施，是列表类型
        # 校验参数
        if not all((user_id, title, price, area_id, address, room_count, acreage, house_unit, capacity, beds, deposit, min_days, max_days, facility)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        # 写入数据库，房屋信息
        sql = "insert into tor_house_info(hi_user_id, hi_title, hi_price, hi_area_id, hi_address, hi_room_count, hi_acreage, hi_house_unit, hi_capacity, hi_beds, hi_deposit, hi_min_days, hi_max_days) values (%(user_id)s, %(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s,%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s);"
        try:
            house_id = self.db.execute(sql,user_id=user_id, title=title, price=price, area_id=area_id, address=address, room_count=room_count, acreage=acreage, house_unit=house_unit, capacity=capacity, beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库存储错误"))
        # 写入数据库设施信息
        sql = "insert into tor_house_facility(hf_house_id, hf_facility_id) values"
        vals = []
        sql_val = []
        try:
            for facility_id in facility:
                sql_val.append("(%s, %s)")
                vals.append(house_id)
                vals.append(facility_id)
            sql += ",".join(sql_val)
            vals = tuple(vals)
            logging.info(sql)
            logging.info(vals)
            self.db.execute(sql,*vals)
        except Exception as e:
            logging.error(e)
            try:
                self.db.execute("delete from tor_house_info where hi_house_id=%s",house_id)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR,errmsg="no data save"))
        self.write(dict(errcode=RET.OK, errmsg="ok", house_id=house_id))

    def get(self):
        """显示房屋信息"""
        # 获取信息
        session = Session(self)
        user_id = session.data.get("user_id", "-1")
        house_id = self.get_argument("house_id")
        # 校验参数
        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        # 先从redis缓存中获取
        try:
            ret = self.redis.get("house_info_%s" % house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            # 此时从redis中获取的是缓存的json格式数据
            resp = '{"errcode":"0", "errmsg":"ok", "data":%s, "user_id":%s}' % (ret, user_id)
            return self.write(resp)
        # 查询数据库
        # 查询房屋基本信息
        try:
            sql = "select hi_title, hi_price, hi_address, hi_room_count, hi_acreage, hi_house_unit, hi_capacity, hi_beds, hi_deposit, hi_min_days, hi_max_days, ui_name, ui_avatar, hi_user_id from tor_house_info inner join tor_user_info on hi_user_id = ui_user_id where hi_house_id=%s"
            ret = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))
        # 用户查询的可能是不存在的房屋id，此时ret为None
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="查无此房"))
        data = dict(
            hid = house_id,
            user_id = ret["hi_user_id"],
            title = ret["hi_title"],
            price = ret["hi_price"],
            address = ret["hi_address"],
            room_count = ret["hi_room_count"],
            acreage = ret["hi_acreage"],
            unit = ret["hi_house_unit"],
            capacity = ret["hi_capacity"],
            beds = ret["hi_beds"],
            deposit = ret["hi_deposit"],
            min_days = ret["hi_min_days"],
            max_days = ret["hi_max_days"],
            user_name = ret["ui_name"],
            user_avatar = constants.QINIU_URL_PREFIX + "/" + ret["ui_avatar"] if ret.get("ui_avatar") else ""

        )
        # 查询房屋的图片信息
        sql = "select hi_url from tor_house_image where hi_house_id=%s"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None

        # 如果查询到图片
        images = []
        if ret:
            for image in ret:
                images.append(constants.QINIU_URL_PREFIX + "/" + image["hi_url"])
        data["images"] = images

        # 查询房屋的基本设施
        sql = "select hf_facility_id from tor_house_facility where hf_house_id=%s"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None

        # 如果查询到设施
        facilities = []
        if ret:
            for facility in ret:
                facilities.append(facility["hf_facility_id"])
        data["facilities"] = facilities
        # 查询评论信息
        sql = "select oi_comment, ui_name, oi_utime, ui_mobile from tor_order_info inner join tor_user_info on oi_user_id=ui_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        comments = []
        if ret:
            for comment in ret:
                comments.append(dict(user_name = comment["ui_name"] if comment["ui_name"] != comment["ui_mobile"] else "匿名用户", content = comment["oi_comment"], ctime = comment["oi_utime"].strftime("%Y-%m-%d  %H:%M:%S")))
        data["comments"] = comments
        # 存入到redis中
        json_data = json.dumps(data)
        try:
            self.redis.setex("house_info _%s" % house_id, constants.REDIS_AREA_INFO_EXPIRES_SECONDES, json_data)
        except Exception as e:
            logging.error(e)

        resp = '{"errcode":"0", "errmsg":"ok", "data":%s, "user_id":%s}' % (json_data, user_id)
        # self.write(dict(errcode=RET.OK, errmsg="ok", data=data))
        self.write(resp)


class HouseImageHandler(BaseHandler):
    """房屋照片"""
    @required_login
    def post(self):
        user_id = self.session.data["user_id"]
        house_id = self.get_argument("house_id")
        house_image = self.request.files["house_image"][0]["body"]
        # 调用封装好的上传七牛的storage方法上传图片
        img_name = storage(house_image)
        if not img_name:
            return self.write(dict(errcode=RET.THIRDERR ,errmsg="七牛上传错误"))
        try:
            # 保存图片到tor_house_image表中，并且设置房屋的主图片(tor_house_info表中的hi_index_image_url)
            # 将用户上传的第一张图片作为房屋的主图片
            sql = "insert into tor_house_image(hi_house_id, hi_url) values(%s,%s);" \
                  "update tor_house_info set hi_index_image_url=%s where hi_house_id=%s and hi_index_image_url is null;"

            self.db.execute(sql, house_id, img_name, img_name,house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="图片存储错误"))
        img_url = constants.QINIU_URL_PREFIX + img_name
        self.write(dict(errcode=RET.OK, errmsg="ok", url=img_url))


class HouseListHandler(BaseHandler):
    """房源列表页面(搜索页面)"""
    def get(self):

        """get方式用来获取数据库数据，本身的逻辑不会对数据库数据产生影响"""
        """
        传入参数说明
        start_date 用户查询的起始时间 sd     非必传   ""          "2017-02-28"
        end_date    用户查询的终止时间 ed    非必传   ""
        area_id     用户查询的区域条件   aid 非必传   ""
        sort_key    排序的关键词     sk     非必传   "new"      "new" "booking" "price-inc"  "price-des"
        page        返回的数据页数     p     非必传   1
        """
        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "1")

        # 校验参数
        # 判断日期的格式，sort_key , 字段的值， page的整数

        # 数据查询，和数据库的保存，缓存的设置
        # 涉及到表：tor_house_info , tor_user_info,            tor_order_info

        sql ="select distinct hi_title, hi_house_id, hi_price, hi_room_count, hi_address, hi_order_count, ui_avatar, hi_index_image_url, hi_ctime from tor_house_info inner join tor_user_info on hi_user_id=ui_user_id left join tor_order_info on hi_house_id=oi_house_id"

        sql_total_count = "select count(distinct hi_house_id) count from tor_house_info inner join tor_user_info on hi_user_id=ui_user_id left join tor_order_info on hi_house_id=oi_house_id"

        sql_where = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date in null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date

        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id

        if sql_where:
            sql += " where hi_online_status=1 and "
            sql += " and ".join(sql_where)

        # 有了where条件，先查询总条目数
        try:
            ret = self.db.get(sql_total_count, **sql_params)
        except Exception as e:
            logging.error(e)
            total_page = -1
        else:
            total_page = int(math.ceil(ret["count"]/float(constants.HOUSE_LIST_PAGE_CAPACITY)))
            page = int(page)
            if page > total_page:
                return self.write(dict(errcode=RET.OK, errmsg="ok", data=[], total_page=total_page))

        # 排序
        if "new" == "sort_key":  # 按最新上传时间排序
            sql += "order by hi_ctime desc"
        elif "booking" == "sort_key":  # 最受欢迎排序
            sql += "order by hi_order_count desc"
        elif "price_inc" == "sort_key":  # 价格由低到高
            sql += "order by hi_price asc"
        elif "price_des" == "sort_key":  # 价格由高到低
            sql += "order by hi_price desc"

        # 分页
        # limit 10  返回前10条
        # limit 20,3  从20 条开始，返回3条数据
        if 1 == page:
            sql += "limit %s" % constants.HOUSE_LIST_PAGE_CAPACITY
        else:
            sql += "limit %s,%s" % ((page-1)*constants.HOUSE_LIST_PAGE_CAPACITY, constants.HOUSE_LIST_PAGE_CAPACITY)
        logging.debug(sql)
        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        houses = []
        if ret:
            for l in ret:
                house = dict(
                    house_id = l["hi_house_id"],
                    title = l["hi_title"],
                    price = l["hi_price"],
                    room_count = l["hi_room_count"],
                    address = l["hi_address"],
                    order_count = l["hi_order_count"],
                    avatar = constants.QINIU_URL_PREFIX + "/" + l["ui_avatar"] if l.get("ui_avatar") else "",
                    image_url = constants.QINIU_URL_PREFIX + "/" + l["hi_index_image_url"] if l.get(
                        "hi_index_image_url") else ""
                )
                houses.append(house)
        self.write(dict(errcode=RET.OK, errmsg="ok", data=houses, total_page=total_page))


class HouseListRedisHandler(BaseHandler):
    """房源列表页面(搜索页面)"""
    def get(self):

        """get方式用来获取数据库数据，本身的逻辑不会对数据库数据产生影响"""
        """
        传入参数说明
        start_date 用户查询的起始时间 sd     非必传   ""          "2017-02-28"
        end_date    用户查询的终止时间 ed    非必传   ""
        area_id     用户查询的区域条件   aid 非必传   ""
        sort_key    排序的关键词     sk     非必传   "new"      "new" "booking" "price-inc"  "price-des"
        page        返回的数据页数     p     非必传   1
        """
        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "1")

        # 校验参数
        # 判断日期的格式，sort_key , 字段的值， page的整数

        # 先从redis中获取数据
        try:
            redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            ret = self.redis.hget(redis_key, page)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            logging.error(e)
            return self.write(ret)

        # 数据查询
        # 涉及到表：tor_house_info , tor_user_info,            tor_order_info

        sql ="select distinct hi_title, hi_house_id, hi_price, hi_room_count, hi_address, hi_order_count, ui_avatar, hi_index_image_url, hi_ctime from tor_house_info inner join tor_user_info on hi_user_id=ui_user_id left join tor_order_info on hi_house_id=oi_house_id"

        sql_total_count = "select count(distinct hi_house_id) count from tor_house_info inner join tor_user_info on hi_user_id=ui_user_id left join tor_order_info on hi_house_id=oi_house_id"

        sql_where = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date in null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date

        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id

        if sql_where:
            sql += " where "
            sql += " and ".join(sql_where)

        # 有了where条件，先查询总条目数
        try:
            ret = self.db.get(sql_total_count, **sql_params)
        except Exception as e:
            logging.error(e)
            total_page = -1
        else:
            total_page = int(math.ceil(ret["count"]/float(constants.HOUSE_LIST_PAGE_CAPACITY)))
            page = int(page)
            if page > total_page:
                return self.write(dict(errcode=RET.OK, errmsg="ok", data=[], total_page=total_page))

        # 排序
        if "new" == "sort_key":  # 按最新上传时间排序
            sql += "order by hi_ctime desc"
        elif "booking" == sort_key:  # 最受欢迎排序
            sql += "order by hi_order_count desc"
        elif "price_inc" == sort_key:  # 价格由低到高
            sql += "order by hi_price asc"
        elif "price_des" == sort_key:  # 价格由高到低
            sql += "order by hi_price desc"

        # 分页
        # limit 10  返回前10条
        # limit 20,3  从20 条开始，返回3条数据
        if 1 == page:
            sql += "limit %s" % (constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)
        else:
            sql += "limit %s,%s" % ((page-1)*constants.HOUSE_LIST_PAGE_CAPACITY, constants.HOUSE_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)

        logging.debug(sql)
        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        data = []
        if ret:
            for l in ret:
                house = dict(
                    house_id = l["hi_house_id"],
                    title = l["hi_title"],
                    price = l["hi_price"],
                    room_count = l["hi_room_count"],
                    address = l["hi_address"],
                    order_count = l["hi_order_count"],
                    avatar = constants.QINIU_URL_PREFIX + "/" + l["ui_avatar"] if l.get("ui_avatar") else "",
                    image_url = constants.QINIU_URL_PREFIX + "/" + l["hi_index_image_url"] if l.get(
                        "hi_index_image_url") else ""
                )
                data.append(house)

        # 对与返回的多页面数据进行分页处理
        # 首先取出用户想要获取的page页的数据
        current_page_data = data[:constants.HOUSE_LIST_PAGE_CAPACITY]
        house_data = {}
        house_data[page] =json.dumps(dict(errcode=RET.OK, errmsg="ok", data=current_page_data, total_page=total_page))
        # 将多取出来的数据分页
        i = 1
        while 1:
            page_data = data[i*constants.HOUSE_LIST_PAGE_CAPACITY: (i+1)*constants.HOUSE_LIST_PAGE_CAPACITY]
            if not page_data:
                break
            house_data[page+i] = json.dumps(dict(errcode=RET.OK, errmsg="ok",data=page_data, total_page=total_page))
            i += 1
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            self.redis.hmset(redis_key,house_data)
            self.redis.expire(redis_key, constants.REDIS_AREA_INFO_EXPIRES_SECONDES)
        except Exception as e:
            logging.error(e)

        self.write(house_data[page])





        # self.write(dict(errcode=RET.OK, errmsg="ok", data=data, total_page=total_page))











        # 返回值















