# -*- coding: utf-8 -*-
"""
Created by 18034 on 2024/5/8.
"""

import time
import redis
import loguru


class ProxyIPPool:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self, auto_clear=1):
        self.redis = redis.Redis(host='localhost', port=6379, db=15)
        self.auto_clear = auto_clear  # 此值为1,则每次在 新增/获取 代理时,都自动清除失效代理.

    # 新增代理
    def add_ip(self, ip_valid_time: dict):
        current_time = int(time.time())  # 当前时间戳
        new_dict = {ip: valid_time + current_time for ip, valid_time in ip_valid_time.items()}
        result = self.redis.zadd('ip_pool', new_dict)
        loguru.logger.success(f"新增代理{result}个\t{ip_valid_time}")
        if self.auto_clear:
            self.clear_ip()  # 清理过期ip
            self.count_ip()  # 统计有效ip个数

    # 清理过期代理
    def clear_ip(self):
        current_time = int(time.time())
        result = self.redis.zremrangebyscore('ip_pool', '-inf', current_time)
        loguru.logger.warning(f"清除失效代理{result}个")

    # 统计可用代理的个数
    def count_ip(self):
        current_time = int(time.time())
        result = self.redis.zcount('ip_pool', current_time, '+inf')
        loguru.logger.info(f"当前可用代理总个数为:{result}")

    # 获取一个最近将要过期的代理
    def get_ip(self, count=1, valid_time=0):
        current_time = int(time.time()) + valid_time  # 获取有效时长不小于validtime秒的代理
        result = self.redis.zrangebyscore('ip_pool', current_time, '+inf', 0, count)  # count 获取代理的个数
        result = [ip.decode() if ip else '' for ip in result]
        loguru.logger.info(f"获取到的可用代理如下:{result}")
        if self.auto_clear:
            self.clear_ip()
        return result

    # 根据ip:port 删除一个ip(若发现获取的代理,质量不好,可以不等到过期时间 直接提前删除)
    def del_ip(self, ip, need_print=1):
        result = self.redis.zrem('ip_pool', ip)
        if need_print == 1:
            loguru.logger.warning(f"清除低质量代理{result}个:{ip}")
        return result

    # 删除多个代理(调用self.del_ip方法,redis-zset 可一次删除多个元素,为了获得实际删除的ip,这里一个一个的删除)
    def del_ips(self, *ips):
        del_list = []
        for ip in ips:
            if self.del_ip(ip, need_print=0):
                del_list.append(ip)  # 如果为True 说明当前代理删除成功,否则删除失败
        loguru.logger.warning(f"清除低质量代理{len(del_list)}个:{del_list}")

        def __del__(self):
            print("关闭redis连接")

        self.redis.close()


if __name__ == '__main__':
    ip_pool = ProxyIPPool()
    ip_pool.add_ip({'122.45.46.12:21808': 60, '113.20.61.66:22989': 3, '195.165.56.45:4569': 60})
    time.sleep(5)  # 等待5秒,使第二个代理过期
    ip_pool.get_ip()
    ip_pool.del_ips('122.45.46.12:21808', '113.120.61.66:22989', '195.165.56.45:4569')
    # 第2个ip在等待5秒时已经过期,前面一步get_ip时会被自动删除的,此时手动执行删除命令,实际只删除掉两个ip
