import random
import string
import time


def get_random_name():
    """
    生成随机名 
    :return: 
    """
    return "".join(random.sample(string.ascii_letters, 5)) + str(int(time.time()))