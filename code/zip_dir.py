import os
import zipfile


def zip_order_dir(order_name, src_path):
    order_path = f"{src_path}/{order_name}"
    zip_file_path = f'{order_path}.zip'
    if not os.path.exists(order_path) and os.path.isdir(order_path) and os.path.exists(zip_file_path):
        return False
    zip_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    for file in os.listdir(order_path):
        try:
            zip_file.write(f"{order_path}/{file}", f"{order_name}/{file}")
        except Exception as e:
            print(f"Zip {e} {order_path}/{file}", f"{order_name}/{file}")
    zip_file.close()
    return True


if __name__ == '__main__':
    import curses

    scr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    pad = curses.newpad(100, 100)
    #  These loops fill the pad with letters; this is
    # explained in the next section
    for y in range(0, 100):
        for x in range(0, 100):
            try:
                pad.addch(y, x, ord('a') + (x * x + y * y) % 26)
            except curses.error:
                pass

    #  Displays a section of the pad in the middle of the screen
    pad.refresh(0, 0, 5, 5, 20, 75)
