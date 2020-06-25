import logging


def print_status(message, is_screen=True, is_log=True):
    if is_screen:
        print(message)
    if is_log:
        logging.info(message)


def load_text_obj(file_name):
    fp = open(file_name, "r", encoding="utf-8")
    while True:
        line = fp.readline()
        if not line:
            break
        yield line
