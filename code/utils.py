import os
from datetime import datetime, timedelta, timezone


def get_previous_24h_date():
    date_now = datetime.now().astimezone(timezone(timedelta(hours=8)))
    check_start_date = (date_now + timedelta(hours=-25)).strftime('%Y%m%d%H')
    check_end_date = (date_now + timedelta(hours=-1)).strftime('%Y%m%d%H')
    return check_start_date, check_end_date


def get_previous_day_date():
    date_now = datetime.now().astimezone(timezone(timedelta(hours=8)))
    check_start_date = (date_now + timedelta(days=-1)).strftime('%Y%m%d') + "00"
    check_end_date = date_now.strftime('%Y%m%d') + "00"
    return check_start_date, check_end_date


def get_check_date_by_sys_argv(sys_argv):
    if len(sys_argv) > 2:
        print(f"Too many parameters are not supported (>2)")
        exit()
    if len(sys_argv) == 1:
        check_start_date, check_end_date = get_previous_day_date()
        return [check_start_date, check_end_date]

    input_time_list = sys_argv[1].split("-")
    if len(input_time_list) > 2:
        print(f"The input format needs to be xx or xx-xx")
        return []
    if len(input_time_list) == 1:
        check_date = sys_argv[1]
        if not check_date.isdigit() or len(check_date) != 8:
            print("Please use 8 digits to indicate the date.")
            return []
        try:
            check_start_date = check_date + "00"
            check_end_date = (
                                     datetime.strptime(check_date, "%Y%m%d") + timedelta(days=1)
                             ).strftime('%Y%m%d') + "00"
        except Exception as e:
            print(f"Please use digits to indicate the normal date. Exception({e})")
            return []
    else:
        check_start_date = input_time_list[0]
        if not check_start_date.isdigit():
            print("Please use digits to indicate the date.")
            return []
        if len(check_start_date) == 8:
            check_start_date += "00"
        elif len(check_start_date) != 10:
            print("Please use 8 or 10 digits to indicate the date.")
            return []
        try:
            datetime.strptime(check_start_date, "%Y%m%d%H")
        except Exception as e:
            print(f"Please use digits to indicate the normal date. Exception({e})")
            return []
        check_end_date = input_time_list[1]
        if not check_end_date.isdigit():
            print("Please use digits to indicate the date.")
            return []
        if len(check_end_date) == 8:
            check_end_date += "00"
        elif len(check_end_date) != 10:
            print("Please use 8 or 10 digits to indicate the date.")
            return []
        try:
            datetime.strptime(check_end_date, "%Y%m%d%H")
        except Exception as e:
            print(f"Please use digits to indicate the normal date. Exception({e})")
            return []
    return [check_start_date, check_end_date]


def get_date_from_device_order(device_order):
    timestamp = device_order.split("_")[1][2:16]
    return datetime.strptime(timestamp, "%Y%m%d%H%M%S")


def get_diff_hours_between_date(star_date, end_date):
    diff_seconds = (end_date - star_date).total_seconds()
    diff_hours = diff_seconds / 60 ** 2
    return diff_hours


def on_same_day(star_date, end_date):
    return (24 - star_date.hour) > get_diff_hours_between_date(star_date, end_date)


def get_date_list_by_check_date(check_date):
    date_list = []
    check_start_date = datetime.strptime(check_date[0], "%Y%m%d%H")
    check_end_date = datetime.strptime(check_date[1], "%Y%m%d%H")
    while not on_same_day(check_start_date, check_end_date):
        start_date_ = check_start_date.strftime('%Y%m%d%H')
        check_start_date = check_start_date + timedelta(hours=(24 - check_start_date.hour))
        end_date_ = check_start_date.strftime('%Y%m%d%H')
        date_list.append([start_date_, end_date_])
    if get_diff_hours_between_date(check_start_date, check_end_date):
        date_list.append([check_start_date.strftime('%Y%m%d%H'), check_end_date.strftime('%Y%m%d%H')])
    return date_list


def get_list_by_date(src_path, check_start_date, check_end_date):
    if not os.path.exists(src_path) or not os.path.isdir(src_path):
        return []
    check_date_len = len(check_start_date) if len(check_start_date) < len(check_end_date) else len(check_end_date)
    name_list = sorted(
        [
            name for name in os.listdir(src_path) if
            os.path.isdir(f"{src_path}/{name}")
            and name.find('MZ') > -1
            and int(check_start_date) <= int(name.split("_")[1][2:2 + check_date_len]) < int(check_end_date)
        ]
        , key=lambda x: x.split("_")[1][2:20]
    )
    return name_list


def get_list_by_device(name_list, device_list):
    name_list = sorted(
        [
            name for name in name_list if
            name.split("_")[0] in device_list
        ]
        , key=lambda x: x.split("_")[1][2:20]
    )
    return name_list
