# coding=utf-8

# 图片验证码有效期，单位秒
PIC_CODE_EXPIRES_SECONDS = 120
#短息验证码有效期，单位分钟
SMS_CODE_EXPIRES_SECONDS = 5
# 七牛上传图片原路径
QINIU_URL_PREFIX = "http://p2duh9n87.bkt.clouddn.com"
# redis中保存的房屋区域过期时间，单位秒
REDIS_AREA_INFO_EXPIRES_SECONDES = 86400
# 房屋订单数最多的房屋数量
HOME_PAGE_MAX_HOUSES = 5
# REDIS中保存的房屋缓存信息过期时间
HOME_PAGE_DATA_DEDIS_EXPIRES_SECONDS = 86400
# 房屋列表页每页的容量
HOUSE_LIST_PAGE_CAPACITY = 4
# redis 中一次缓存房屋的页数
HOUSE_LIST_PAGE_CACHE_NUM = 2
