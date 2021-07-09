import threading
import multiprocessing
import queue
import os
import shutil
import time
from enum import Enum
import sys
import math

from copy_dir import copy_order_dir
from process_dir import order_dir_process_event, order_dir_process_detec
from zip_dir import zip_order_dir
from post_dir import post_file_event, post_file_detec
from utils import *


# 1.Copy
# 2.process(event/detec)
# 3.zip
# 4.post

#
# queue_copy = queue.Queue()
# queue_process = queue.Queue()
# queue_zip = queue.Queue()
# queue_post = queue.Queue()
# queue_done = queue.Queue()


class ProcessType(Enum):
    EVENT = 0
    DETEC = 1


class CopyDir(object):
    def __init__(self, src_path, dst_path, name_):
        self.src_path = src_path
        self.dst_path = dst_path
        self._running = True
        self.name = name_
        self.processing = False

    def terminate(self):
        self._running = False

    def run(self, queue_cp, queue_process_, idx_):
        run_name = f"{self.name}_{idx_}"
        print(f"[{run_name}] Running [{queue_cp.qsize()}] ... [{datetime.now()}]")
        # while self._running and not queue_cp.empty():
        while True:
            if not self._running:
                print(f"[{run_name}] Quit. [{datetime.now()}]")
                break
            if queue_cp.empty():
                # print(f"\r[{run_name}] Queue({queue_cp.qsize()})  [{datetime.now()}]")
                time.sleep(0.1)
                continue
            order_name = queue_cp.get()
            # print(f"\r[{run_name}] Get {order_name}({get_date_from_device_order(order_name)}) [{datetime.now()}]")
            dt_ = datetime.now()
            res_ = copy_order_dir(order_name, self.src_path, self.dst_path)
            # print(f"\r[{run_name}] {order_name}({get_date_from_device_order(order_name)}) ({res_}) - "
            #       f"{(datetime.now() - dt_).microseconds / 1000} ms [{datetime.now()}]")
            if res_:
                queue_process_.put(order_name)
            queue_cp.task_done()


class ProcessDir(object):
    def __init__(self, src_path, name_, process_type=ProcessType.EVENT):
        self.src_path = src_path
        self._running = True
        self.name = name_
        self.process_type = process_type

    def terminate(self):
        self._running = False

    def run(self, queue_process_, queue_zip_, idx_):
        run_name = f"{self.name}_{idx_}"
        print(f"[{run_name}] Running ... [{datetime.now()}]")
        # while self._running:
        while True:
            if not self._running:
                print(f"[{run_name}] Quit. [{datetime.now()}]")
                break
            if queue_process_.empty():
                # print(f"\r[{run_name}] Queue({queue_process_.qsize()}) [{datetime.now()}]")
                time.sleep(0.1)
                continue
            order_name = queue_process_.get()
            # print(f"\r[{run_name}] Get {order_name}({get_date_from_device_order(order_name)}) [{datetime.now()}]")
            dt_ = datetime.now()
            if self.process_type == ProcessType.EVENT:
                process_res = order_dir_process_event(order_name, self.src_path)
            elif self.process_type == ProcessType.DETEC:
                process_res = order_dir_process_detec(order_name, self.src_path)
            else:
                print(f"Wrong type [{self.process_type}]")
                queue_process_.task_done()
                queue_process_.put(order_name)
                break
            # print(f"\r[{run_name}] {self.process_type} {order_name}({get_date_from_device_order(order_name)}) ({process_res}) - "
            #       f"{(datetime.now() - dt_).microseconds / 1000} ms [{datetime.now()}]")
            if process_res:
                queue_zip_.put(order_name)
            queue_process_.task_done()


class ZipDir(object):
    def __init__(self, src_path, name_):
        self.src_path = src_path
        self._running = True
        self.name = name_

    def terminate(self):
        self._running = False

    def run(self, queue_zip_, queue_post_, idx_):
        run_name = f"{self.name}_{idx_}"
        print(f"[{run_name}] Running ... [{datetime.now()}]")
        # while self._running:
        while True:
            if not self._running:
                print(f"[{run_name}] Quit. [{datetime.now()}]")
                break
            if queue_zip_.empty():
                # print(f"\r[{run_name}] Queue({queue_zip_.qsize()}) [{datetime.now()}]")
                time.sleep(0.1)
                continue
            order_name = queue_zip_.get()
            # print(f"\r[{run_name}] Get {order_name}({get_date_from_device_order(order_name)}) [{datetime.now()}]")
            dt_ = datetime.now()
            res_ = zip_order_dir(order_name, self.src_path)
            # print(f"[{run_name}] {order_name}({get_date_from_device_order(order_name)}) ({res_}) - "
            #       f"{(datetime.now() - dt_).microseconds / 1000} ms [{datetime.now()}]")
            if res_:
                queue_post_.put(order_name)
            queue_zip_.task_done()


class PostDir(object):
    def __init__(self, src_path, name_, process_type=ProcessType.EVENT):
        self.src_path = src_path
        self._running = True
        self.name = name_
        self.process_type = process_type

    def terminate(self):
        self._running = False

    def run(self, queue_post_, queue_done_, idx_):
        run_name = f"{self.name}_{idx_}"
        print(f"[{run_name}] Running ... [{datetime.now()}]")
        # while self._running:
        while True:
            if not self._running:
                print(f"[{run_name}] Quit. [{datetime.now()}]")
                break
            if queue_post_.empty():
                # print(f"\r[{run_name}] Queue({queue_post_.qsize()}) [{datetime.now()}]")
                time.sleep(0.1)
                continue
            order_name = queue_post_.get()
            # print(f"\r[{run_name}] Get {order_name}({get_date_from_device_order(order_name)}) [{datetime.now()}]")
            dt_ = datetime.now()
            zip_file_path = f"{self.src_path}/{order_name}.zip"
            if self.process_type == ProcessType.EVENT:
                res_ = post_file_event(zip_file_path)
            elif self.process_type == ProcessType.DETEC:
                res_ = post_file_detec(zip_file_path)
            else:
                print(f"Wrong type [{self.process_type}]")
                queue_post_.task_done()
                queue_post_.put(order_name)
                break
            key_ = "msg"
            if key_ in res_:
                res_ = res_[key_]
            print(f"[{run_name}] {order_name}({get_date_from_device_order(order_name)}) ({res_}) - "
                  f"{(datetime.now() - dt_).seconds} s [{datetime.now()}]")
            queue_post_.task_done()
            if not res_:
                print(f"[{run_name}] Post {order_name} FAIL! [{res_}]")
                queue_post_.put(order_name)
            else:
                queue_done_.put(order_name)
                dir_path = f"{self.src_path}/{order_name}"
                shutil.rmtree(dir_path)
                os.remove(zip_file_path)
                print(f"[{run_name}] rmtree {dir_path} remove {zip_file_path}")


# def check_task_all_done(task_num, class_list):
def check_task_all_done(queue_copy, queue_process, queue_zip, queue_post, queue_done, task_num, class_list):
    while True:
        if queue_done.qsize() == task_num:
            print(f"All tasks({task_num}) have been completed.")
            for c in class_list:
                c.terminate()
            time.sleep(1)
            print(f"Terminate all.")
            print(f"CheckTaskAllDone Quit. [{datetime.now()}]")
            # break
            return True
        else:
            print(f"COPY[{queue_copy.qsize()}]-PROCESS[{queue_process.qsize()}]"
                  f"-ZIP[{queue_zip.qsize()}]-POST[{queue_post.qsize()}]-DONE[{queue_done.qsize()}] [{datetime.now()}]")
            time.sleep(1)


def sync_process(name_list, src_path, dst_path, process_type=ProcessType.EVENT):
    for name in name_list:
        st = datetime.now()
        copy_order_dir(name, src_path, dst_path)
        order_dir_process_event(name, dst_path)
        zip_order_dir(name, dst_path)
        if process_type == ProcessType.EVENT:
            post_res = post_file_event(f"{dst_path}/{name}.zip")
        elif process_type == ProcessType.DETEC:
            post_res = post_file_detec(f"{dst_path}/{name}.zip")
        shutil.rmtree(f"{dst_path}/{name}")
        os.remove(f"{dst_path}/{name}.zip")
        print(f"{name} ({post_res}) {(datetime.now() - st)} s [{datetime.now()}]")
        # exit()
    return True


def async_process(name_list, src_path, dst_path, process_type=ProcessType.EVENT, thread_num=1):
    queue_copy = queue.Queue()
    queue_process = queue.Queue()
    queue_zip = queue.Queue()
    queue_post = queue.Queue()
    queue_done = queue.Queue()
    for name in name_list:
        queue_copy.put(name)
    class_list = []
    # thread_list = []
    cla_ = CopyDir(src_path, dst_path, f"copy")
    class_list.append(cla_)
    for i in range(1 * thread_num):
        thread_ = threading.Thread(target=cla_.run, args=(queue_copy, queue_process, i))
        thread_.start()
        # thread_list.append(thread_)

    cla_ = ProcessDir(dst_path, f"process", process_type)
    class_list.append(cla_)
    for i in range(1 * thread_num):
        thread_ = threading.Thread(target=cla_.run, args=(queue_process, queue_zip, i))
        thread_.start()
        # thread_list.append(thread_)

    cla_ = ZipDir(dst_path, f"zip")
    class_list.append(cla_)
    for i in range(1 * thread_num):
        thread_ = threading.Thread(target=cla_.run, args=(queue_zip, queue_post, i))
        # thread_ = threading.Thread(target=cla_.run, args=(queue_zip, queue_done, i))
        thread_.start()
        # thread_list.append(thread_)

    cla_ = PostDir(dst_path, f"post", process_type)
    class_list.append(cla_)
    for i in range(1 * thread_num):
        thread_ = threading.Thread(target=cla_.run, args=(queue_post, queue_done, i))
        thread_.start()
        # thread_list.append(thread_)

    # for t in thread_list:
    #     t.start()
    # for t in thread_list:
    #     t.join()
    print(f"Wait all task done ... [{datetime.now()}]")
    # check_task_all_done(len(name_list), class_list)
    check_task_all_done(queue_copy, queue_process, queue_zip, queue_post, queue_done, len(name_list), class_list)

    return True


def processing_center(
        src_path, dst_path, order_list=[], device_list=[], check_date=[], sync=True, multiprocess=0, thread_num=1
):
    print(f"create task ... [{datetime.now()}]")
    if order_list:
        name_list = order_list
    else:
        if not check_date:
            check_start_date, check_end_date = get_previous_24h_date()
        else:
            check_start_date = check_date[0]
            check_end_date = check_date[1]
        print(f"Check date: {check_start_date}-{check_end_date}")
        print(f"Check path: {src_path}")
        name_list = get_list_by_date(src_path, check_start_date, check_end_date)
        if device_list:
            name_list = get_list_by_device(name_list, device_list)
    # name_list = name_list[:15]
    task_num = len(name_list)
    print(f"Task num: {task_num}")
    if task_num == 0:
        return

    if multiprocess:
        cpu_count = multiprocessing.cpu_count()
        multiprocess_num = multiprocess if multiprocess < cpu_count // 4 else cpu_count // 4
        print(f"CUP CORE: {cpu_count}, MULTIPROCESS NUM: {multiprocess_num}")
        pool = multiprocessing.Pool(processes=multiprocess_num)
        sub_task_length = 1000
        sub_task_num = math.ceil(task_num / sub_task_length)
        for i in range(sub_task_num):
            if i < sub_task_num - 1:
                pool.apply_async(
                    sync_process if sync else async_process,
                    args=(name_list[i * sub_task_length: (i + 1) * sub_task_length], src_path, dst_path)
                )
            else:
                pool.apply_async(
                    sync_process if sync else async_process,
                    args=(name_list[i * sub_task_length:], src_path, dst_path)
                )
        pool.close()
        pool.join()
    else:
        if sync:
            sync_process(name_list, src_path, dst_path)
        else:
            async_process(name_list, src_path, dst_path)


def excute_process(input_, src_path_, dst_path_):
    check_date = get_check_date_by_sys_argv(input_)
    if not check_date:
        exit()
    print(f"Check time: {check_date[0]}-{check_date[1]}")
    date_list = get_date_list_by_check_date(check_date)
    print(date_list)
    order_list = ["353470090318708_MZ20210704175449233802681999433"]
    device_list = [
        '353470090517887',
        '353470090390095',
        '353470090371962',
        '353470090388008',
        '353470090643212',
        '353470090226752',
        '353470090387752',
        '353470090273762',
        '353470090374156',
        '353470090636059',
        '353470090389444',
        '353470090706423',
        '353470090332600',
        '353470090364413',
        '353470090271378',
        '353470090390343',
        '353470090745116',
        '353470090694983',
        '353470090523497',
        '353470090510395',
    ]

    for check_date in date_list:
        dt = datetime.now()
        date_src_path_ = f"{src_path_}/{check_date[0][:8]}/"
        processing_center(date_src_path_, dst_path_, check_date=check_date, sync=False, thread_num=1)
        # processing_center(date_src_path_, dst_path_, order_list=order_list, sync=True, thread_num=1)
        # processing_center(date_src_path_, dst_path_, check_date=check_date, device_list=device_list, sync=True, thread_num=1)
        print(f"\nprocessing_center time: {(datetime.now() - dt).seconds} s [{datetime.now()}]")


if __name__ == '__main__':
    src_path_ = "/Users/homey/Desktop/OrderStation/"
    # src_path_ = "/tar_data/"
    dst_path_ = "../data"
    excute_process(sys.argv, src_path_, dst_path_)
