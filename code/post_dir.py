import requests
import json
from urllib3 import encode_multipart_formdata
from datetime import datetime, timedelta
import os


def post_file_event(file_path):
    data = {
        "is_check": "false",
        "file": (file_path.split("/")[-1], open(file_path, 'rb').read())
    }
    encode_data = encode_multipart_formdata(data)
    data = encode_data[0]
    headers = {"Content-Type": encode_data[1]}
    res_text = ""
    try:
        res_ = requests.post("http://218.85.80.141:9988/api/shopping", headers=headers, data=data)
        res_text = res_.text.encode("UTF-8")
        res_text = json.loads(res_text)
    except Exception as e:
        print(e)

    return res_text


def post_file_detec(file_path):
    data = {
        "is_check": "false",
        "file": (file_path.split("/")[-1], open(file_path, 'rb').read())
    }
    encode_data = encode_multipart_formdata(data)
    data = encode_data[0]
    headers = {"Content-Type": encode_data[1]}
    url_ = "http://218.85.80.141:9988/api/imagezip"
    res_text = ""
    try:
        res_ = requests.post(url_, headers=headers, data=data)
        res_text = res_.text.encode("UTF-8")
        res_text = json.loads(res_text)
    except Exception as e:
        print(e)
    return res_text


def post_sku_image(file_path):
    data = {
        "imgfile": (file_path.split("/")[-1], open(file_path, 'rb').read())
    }
    encode_data = encode_multipart_formdata(data)
    data = encode_data[0]
    headers = {"Content-Type": encode_data[1]}

    res_ = requests.post("http://218.85.80.141:9988/api/imageUpload", headers=headers, data=data)
    res_text = res_.text.encode("UTF-8")
    res_text = json.loads(res_text)
    return res_text


def get_token():
    token = ""
    url = "https://aischool.ruijie.com.cn/api/base/auth/token"
    headers = {"Content-Type": "application/json;charset=utf-8"}
    body = {"userName": "mdtest", "password": "123456"}
    payload = json.dumps(body)
    try:
        res = requests.post(url=url, headers=headers, data=payload)
        if res.status_code == 200:
            res_text = res.text.encode("UTF-8")
            res_text = str(res_text)[2:-1].replace('\\', '\\\\')
            res_text = json.loads(res_text)
            token = res_text["result"]["token"]
    except Exception as e:
        print(e)
        return token
    return token


def get_url_by_69code_name_token_post(code, name, token):
    logo_url = ""
    url = "https://aischool.ruijie.com.cn/api/featureLibrary/getTrainStatus"
    headers = {"Content-Type": "application/json;charset=utf-8",
               "X-Authorization": token}
    body = {"commodityCode": [code]}
    payload = json.dumps(body)
    try:
        res = requests.post(url=url, headers=headers, data=payload)
        if res.status_code == 200:
            res_text = res.text.encode("UTF-8")
            res_text = str(res_text)[2:-1].replace('\\', '\\\\')
            res_text = json.loads(res_text)

            code_list = res_text["data"][code]
            for info in code_list:
                commodityNameEn = info["commodityNameEn"]
                if commodityNameEn.find("Md326") > -1:
                    if commodityNameEn == name:
                        logo_url = info["logoUrl"]
                        break
                else:
                    if commodityNameEn == name.replace("Md326", ""):
                        logo_url = info["logoUrl"]
                        break
    except Exception as e:
        print(e)
        return logo_url
    return logo_url


def request_download(image_url, save_image_path):
    try:
        res = requests.get(image_url)
        with open(save_image_path, 'wb') as f:
            f.write(res.content)
        print(f"From {image_url} download image save to {save_image_path} done.")
    except Exception as e:
        print(e)
        print(f"From {image_url} download image save to {save_image_path} failed.")


def get_image_by_url(code, save_image_log_dir, name):
    token = get_token()
    if token:
        url = get_url_by_69code_name_token_post(code, name, token)
        if url:
            save_image_path = f"{save_image_log_dir}/{name}.png"
            request_download(url, save_image_path)
            save_image_path = f"{save_image_log_dir}/{name}.png"
            print(f"{save_image_path} download {os.path.exists(save_image_path)}.")
            print(f"Send {save_image_path} to server {post_sku_image(save_image_path)}")


def get_shopping_time_by_sdk_log(sdk_log_path):
    if not os.path.exists(sdk_log_path):
        return -1
    open_door_done_time, close_door_start_time = "", ""
    sdk_log = open(sdk_log_path, "r")
    for line in sdk_log.readlines():
        if line.find("- OpenDoorCallback Done [") > -1:
            open_door_done_time = line.split("[")[2].split("]")[0]
        if line.find("- CloseDoorCallback Start [") > -1:
            close_door_start_time = line.split("[")[2].split("]")[0]
    try:
        open_door_done_time_datetime = datetime.strptime(open_door_done_time, "%Y.%m.%d-%H:%M:%S")
        close_door_start_time_datetime = datetime.strptime(close_door_start_time, "%Y.%m.%d-%H:%M:%S")
    except Exception as e:
        print(f"get_shopping_time_by_sdk_log: {e}")
        return -1
    return (close_door_start_time_datetime - open_door_done_time_datetime).seconds


if __name__ == '__main__':
    # print(post_file_detec("./copy_/353470090181395_MZ202106030500047133248460530200.zip"))

    print(post_sku_image("./ALLSKUIMAGE/anmuxihuangtaoyanmai200mlMd326.png"))
