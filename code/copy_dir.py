import os
import shutil


def copy_order_dir(order_name, src_path, dst_path):
    raw_dir_path = f"{src_path}/{order_name}"
    if not os.path.exists(raw_dir_path):
        return False
    copy_dir_path = f"{dst_path}/{order_name}"
    if not os.path.exists(copy_dir_path):
        shutil.copytree(raw_dir_path, copy_dir_path)
        # print(f"copytree {raw_dir_path} -> {copy_dir_path}")
        log_file_path = f"{src_path}/{order_name}_log.txt"
        if os.path.exists(log_file_path):
            shutil.copy(log_file_path, f"{copy_dir_path}/{order_name}_log.txt")
    return True


if __name__ == '__main__':
    copy_order_dir("353470090183136_MZ202106030648343658364903692500", "../../tar", "./copy_dir")
