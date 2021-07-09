import os
import shutil
from datetime import datetime, timedelta
import json

from post_dir import get_image_by_url


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


def order_dir_process_event(order_name, src_path):
    dir_path = f"{src_path}/{order_name}"
    if not os.path.exists(dir_path):
        return False
    sdk_log_path = f"{dir_path}/{order_name}_log.txt"
    ai_log_path = f"{dir_path}/log.txt"

    save_image_log_dir = "../ALLSKUIMAGE"
    if not os.path.exists(save_image_log_dir):
        os.mkdir(save_image_log_dir)
    sku_info = ["weight", "small", "nameCn", "name69", "groupname", "floor"]

    url_fore = "http://172.30.232.107:9986/dataset/"

    shopping_time_txt = open(f'{dir_path}/shopping_time.txt', "a+", encoding='UTF-8')

    shopping_cost_time = get_shopping_time_by_sdk_log(sdk_log_path)
    shopping_time_txt.write(str(shopping_cost_time) + '\n')

    res_flag = 0
    res_list = []
    res_dict = {}
    sku_dict = {}
    normal = "0"
    time = ""

    find_res = 0
    find_final_res = 0
    find_error_res = 0

    sku_group_name = {}

    ai_log_txt = open(ai_log_path, "r", encoding='UTF-8')
    sku_cloud_txt = open(f"{dir_path}/sku_cloud.txt", "w", encoding='UTF-8')
    sku_name_txt = open(f"{dir_path}/sku_name.txt", "w", encoding='UTF-8')
    result_txt = open(f"{dir_path}/result.txt", "w", encoding='UTF-8')
    time_result_txt = open(f"{dir_path}/time_result.txt", "w", encoding='UTF-8')
    name_url_txt = open(f"{dir_path}/name_url.txt", "w", encoding='UTF-8')

    for line in ai_log_txt.readlines():
        if isinstance(line, str):
            if line.find("[SkuInfo]") > -1:
                post = line.find("name:[")
                name = line[post + 6:].split("]")[0] if post > -1 else ""
                if not name.endswith("Md326"):
                    name = name + "Md326"
                sku_dict.update({name: {"name": name}})

                for info_name in sku_info:
                    post = line.find(info_name)
                    info_content = line[post + len(info_name) + 2:].split("]")[0] if post > -1 else ""
                    if info_name == "floor":
                        floor_temp = ""
                        for f in info_content.split():
                            floor_temp += f"{f},"
                        info_content = floor_temp[:-1]
                    sku_dict[name][info_name] = info_content
                if not os.path.exists(f"{save_image_log_dir}/{name}.png"):
                    get_image_by_url(sku_dict[name]["name69"], save_image_log_dir, name)

                sku_dict[name]["url"] = f"{url_fore}{name}.png"

                if sku_dict[name]["groupname"] not in sku_group_name:
                    sku_group_name[sku_dict[name]["groupname"]] = name

            elif line.find("Final_Global_Result") > -1:
                if find_res > 0:
                    res_dict.clear()
                find_res += 1
                find_final_res = 1
            elif find_final_res > 0 and line.find('Empty') < 0 and line.find("====================") < 0:
                res_name = line.split(' x ')[0]
                res_num = line.split(' x ')[1]
                if res_name in sku_group_name:
                    res_name = sku_group_name[res_name]
                res_dict[res_name] = res_num
            elif find_final_res > 0 and line.find("====================") > -1:
                find_final_res = 0
            elif line.find("Error_Global_Result") > -1:
                find_error_res = 1
            elif find_error_res > 0 and line.find('Empty') < 0 and line.find("====================") < 0:
                res_name = line.split(' x ')[0]
                res_num = line.split(' x ')[1]
                if res_name in sku_group_name:
                    res_name = sku_group_name[res_name]
                res_dict[res_name] = res_num
            elif find_error_res > 0 and line.find("====================") > -1:
                find_error_res = 0

            elif line.find('"ShoppingCartItems":') > -1:
                res_flag = 1
            elif res_flag == 1 and line.find('"goodsName":') > -1:
                res_list.append(line[-16:-3])
            elif res_flag == 1 and line.find('"goodsCnt"') > -1:
                res_list.append(f"{line[line.find(':') + 2:]}")
            elif line.find("]  - dstDirPath:") > -1:
                time = line.split(']')[0][1:]
            elif line.find("Allow_Customer_Edit") > -1:
                if int(line[-3]) != 0:
                    normal = "4"
            # elif normal == "4" and line.find('ErrorDesc') > -1:
            #     if line.split('"')[3] == '10003':
            #         normal = "0"

    if len(res_list) == 0:
        res_dict.clear()

    for snc in sku_dict:
        sku_name_txt.write(
            f'n=5   t=0     mins=1      maxs=0      g_extra=0       name={sku_dict[snc]["name"]}'
            f'     g={str(sku_dict[snc]["weight"])}      nameCn={sku_dict[snc]["nameCn"]}     69code={sku_dict[snc]["name69"]}       small={sku_dict[snc]["small"]}'
            f'      groupname={sku_dict[snc]["groupname"]}        floor={sku_dict[snc]["floor"]}\n')

        sku_cloud_txt.write(sku_dict[snc]["name"] + "\n")
        if (sku_dict[snc]["groupname"]):
            name_url_txt.write(
                f'{sku_dict[snc]["name"]}|{sku_dict[snc]["nameCn"]}|{sku_dict[snc]["url"]}|{sku_dict[snc]["groupname"]},{sku_dict[snc]["name69"]}|{sku_dict[snc]["floor"]}\n')
        else:
            name_url_txt.write(
                f'{sku_dict[snc]["name"]}|{sku_dict[snc]["nameCn"]}|{sku_dict[snc]["url"]}|{sku_dict[snc]["name69"]}|{sku_dict[snc]["floor"]}\n')

    time_result_txt.write(time + "\n")
    shopping_time_txt.write(normal + "\n")

    for name in res_dict:
        num = res_dict[name]
        result_txt.write(f"{name} {num}")
        time_result_txt.write(f"{name}|{num}")

    sku_cloud_txt.close()
    sku_name_txt.close()
    result_txt.close()
    ai_log_txt.close()
    time_result_txt.close()
    name_url_txt.close()
    shopping_time_txt.close()

    for file_name in os.listdir(dir_path):
        file_path = f"{dir_path}/{file_name}"
        # if file_name.endswith("jpg") or (file_name.find("MZ") > -1 and file_name.endswith("txt")):
        if file_name.endswith("jpg"):
            os.remove(file_path)
        elif file_name == "Negative" and os.path.isdir(file_path):
            shutil.rmtree(file_path)
    return True


def order_dir_process_detec(order_name, src_path):
    dir_path = f"{src_path}/{order_name}"
    if not os.path.exists(dir_path):
        return False
    try:
        cam_DR_file = open(f'{dir_path}/cam_DR.txt', "r", encoding='UTF-8')
        cam_TR_file = open(f'{dir_path}/cam_TR.txt', "r", encoding='UTF-8')
    except Exception as e:
        print(e)
        return False

    txt = open(f"{dir_path}/log.txt", "r", encoding='UTF-8')
    cam_DR_list = cam_DR_file.readlines()
    cam_TR_list = cam_TR_file.readlines()
    cam_DR_file.close()
    cam_TR_file.close()
    os.remove(f'{dir_path}/cam_DR.txt')
    os.remove(f'{dir_path}/cam_TR.txt')

    result_json_data = {"id": "", "template": "", "images": ""}

    result_json_data["id"] = order_name.split('_')[-1]
    FixedClass_list = []
    template_data = {}
    shelterClass_list = []
    shelterImage_list = []
    shelterClass_name = ""
    is_invalid_detect = 0
    # url_fore = "http://172.30.232.103:9986/dataset/"
    url_fore = "http://172.30.232.107:9986/dataset/"
    for i, line in enumerate(txt.readlines()):
        if isinstance(line, str):
            if line.find("[SkuInfo]") > -1:
                post = line.find("name:[")
                name = line[post + 6:].split("]")[0]
                if not name.endswith("Md326"):
                    name = name + "Md326"
                post = line.find("nameCn:[")
                nameCn = line[post + 8:].split("]")[0]
                template_data[name] = {"nameCn": nameCn, "url": f"{url_fore}{name}.png"}
            elif line.find("FindBadBBox_byPositionFixed") > -1:
                bFixedMisReg = int(line.strip().split(',')[1].split('=')[1][1])
                if bFixedMisReg:
                    FixedClass = line.strip().split(',')[0].split('=')[1][1:]
                    # print(f'FixedClass: {FixedClass} -> {bFixedMisReg}')
                    FixedClass_list.append(FixedClass)
                    # print(f"FixedClass: {FixedClass_list}")
            elif line.find("================== Invalid Detect ==================") > -1:
                is_invalid_detect = 1
            elif line.find("==================================================") > -1:
                is_invalid_detect = 0
            elif is_invalid_detect and line.find("Md326") > -1:
                shelterClass_name = line.strip().split(" ")[0]
            # elif is_invalid_detect and shelterClass_name and line.find("avg") > -1 and line.find("shelter") > -1:
            #     shelterClass_list.append(shelterClass_name)
            elif is_invalid_detect and shelterClass_name:
                if line.strip():
                    shelter_list = [n[1:] for n in line.strip().split("*") if n.find("shelter") > -1]
                    # TR_131_0.87_(16296)_0_81_84_194_(shelter1)
                    for name in shelter_list:
                        l = name.strip().split("_")
                        name = f"{l[0]}\({l[1]}\){l[4]}_{l[5]}_{l[6]}_{l[7]}_{shelterClass_name}"
                        shelterImage_list.append(name)

    txt.close()
    os.remove(f"{dir_path}/log.txt")
    result_json_data["template"] = template_data
    # print(result_json_data)

    FixedClass_list = list(set(FixedClass_list))
    shelterClass_list = list(set(shelterClass_list))
    shelterImage_list = list(set(shelterImage_list))
    # print(f"FixedClass_list: {FixedClass_list}")
    # print(f"shelterClass_list: {shelterClass_list}")
    # print(f"shelterImage_list: {shelterImage_list}")

    for file_name in os.listdir(dir_path):
        if file_name.endswith('ini') or file_name.endswith('mp4'):
            os.remove(f'{dir_path}/{file_name}')
            # print(f'os.remove {dir_path}/{file_name}')
        elif file_name.find('log.txt') > 0 or file_name.find('1stFrame') > -1 or file_name.find('calib') > -1 or \
                file_name.find('time') > -1 or file_name.find('gravity') > -1 or file_name.find(
            'DecodeFirstFrame') > -1:
            os.remove(f'{dir_path}/{file_name}')
            # print(f'os.remove {dir_path}/{file_name}')
        elif file_name == "Negative" and os.path.isdir(f"{dir_path}/{file_name}"):
            shutil.rmtree(f"{dir_path}/{file_name}")
        elif file_name.find("Negative") > -1 or file_name.find("EarlyDetect") > -1:
            os.remove(f'{dir_path}/{file_name}')
        elif file_name.find("record") > -1:
            os.remove(f'{dir_path}/{file_name}')
            result_json_data['images'] = []

            result_json_file = open(f'{dir_path}/result.json', "w", encoding='UTF-8')
            json.dump(result_json_data, result_json_file, indent=1)
            return True

    for shelter_image in shelterImage_list:
        cmd = f"rm -rf {dir_path}/{shelter_image}*"
        # print(cmd)
        os.system(cmd)

    dir_path_list = sorted(os.listdir(dir_path), key=lambda x: int(x[3:].split(')')[0]))
    images = []
    for file_name in dir_path_list:
        if file_name.endswith('.jpg'):
            # print(file_name)

            remove_image = 0
            for fixed_class in FixedClass_list:
                if file_name.find(fixed_class) > -1:
                    # print(f"Ready to remove: {dir_path}/{file_name}")
                    if os.path.exists(f'{dir_path}/{file_name}'):
                        os.remove(f'{dir_path}/{file_name}')
                        # print(f'os.remove {dir_path}/{file_name}')
                        remove_image = 1
            # for shelter_class in shelterClass_list:
            #     if file_name.find(shelter_class) > -1:
            #         remove_path = f'{dir_path}/{file_name}'
            #         # print(f"Ready to remove: {dir_path}/{file_name}")
            #         if os.path.exists(remove_path):
            #             os.remove(remove_path)
            #             # print(f'os.remove {dir_path}/{file_name}')
            #             remove_image = 1

            # print(f'remove_image: [{remove_image}]')
            if remove_image == 0:
                image = {}

                # "DR(177)129_205_175_86__prob_0.8_dis_0.76_【EarlyDetect】_【Negative】.jpg"
                if file_name.find("Negative") > -1:

                    rename_path = f'{dir_path}/{file_name}'
                    newname_path = f'{dir_path}/{file_name[:file_name.find("dis") + 8]}.jpg'
                    os.rename(rename_path, newname_path)
                    image["path"] = f'{file_name[:file_name.find("dis") + 8]}.jpg'
                    image["id"] = "anti_negative"
                else:
                    image["path"] = file_name
                    image["id"] = file_name.split('_')[4]
                frame_count = int(file_name[3].split(')')[0])
                frame_pos = file_name[:2]
                if frame_pos == "DR":
                    frame_ts = cam_DR_list[frame_count].split(',')[2].split('=')[1]
                else:
                    frame_ts = cam_TR_list[frame_count].split(',')[2].split('=')[1]
                image["ts"] = frame_ts
                # print(image)
                images.append(image)
    # print(len(images))
    # print(f"os.listdir({dir_path}) -> {len(os.listdir(dir_path))}")
    result_json_data['images'] = images

    result_json_file = open(f'{dir_path}/result.json', "w", encoding='UTF-8')
    json.dump(result_json_data, result_json_file, indent=1)
    return True
