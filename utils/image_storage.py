#coding:utf-8

from qiniu import Auth, put_file, etag, urlsafe_base64_encode, put_data
import qiniu.config
import logging, qiniu

#需要填写你的 Access Key 和 Secret Key
access_key = '46PsQzcsXHDhhgXr9DrzI1sblIHW0GwqPK1rI2kU'
secret_key = 'Jo_UAeWC82IeocQNGcf9cQ5PTD-_1CiAHwc1meQs'



def storage(image_data):
    if not image_data:
        return None
    # try:
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'tornado-ihome'

    # 上传到七牛后保存的文件名
    # key = 'ihome_image'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name)

    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    ret, info = put_data(token, None, image_data)
    # except Exception as e:
    #     logging.error(e)
    #     # raise e
    # print(ret)
    # print type(ret)
    # print("*"*20)
    # print info
    # print type(info)
    # assert ret['key']
    return ret['key']

if __name__ == "__main__":
    file_name = raw_input("请输入上传的文件名：")
    with open(file_name, "rb") as file:
        file_data = file.read()
        key = storage(file_data)
        print key


        """
        file = open(file_name, "rb")
        file_data = file.read()
        storage(file_data)
        file.close()

        """