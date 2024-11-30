from gevent import monkey
monkey.patch_all() # 打补丁, 让gevent识别耗时操作

from gevent.pool import Pool
from core.db.mongo_pool import MongoPool
from core.proxy_validate.httpbin_validator import check_proxy
from settings import MAX_SCORE, TEST_PROXY_ASYNC_COUNT, RUN_TEST_INTERVAL_HOURS
from utils.log import logger
from queue import Queue
import schedule
import time


class ProxyTester:
    def __init__(self):
        """初始化方法"""
        # 数据库操作对象
        self.mongo_pool = MongoPool()
        # 协程池
        self.gevent_pool = Pool()
        # 用于传递proxy对象的队列
        self.queue = Queue()

    def run(self):
        """执行检测代理IP的过程的核心逻辑"""
        # 从数据库获取所有代理IP的proxy对象
        proxies = self.mongo_pool.find_all()
        # 遍历proxy对象
        for proxy in proxies:
            # 把要检测的proxy放入队列
            self.queue.put(proxy)
        # 根据配置的并发数量，创建协程池中的并发协程
        for _ in range(TEST_PROXY_ASYNC_COUNT):
            # 把检测一个proxy的方法加入协程池，并指定回调函数
            self.gevent_pool.apply_async(
                self.__check_one_proxy, callback=self.__check_callback
            )
        # 阻塞线程，使其等待队列中的任务全部完成
        self.queue.join()

    def __check_callback(self, temp):
        """回调函数
        不断回调自己从而实现循环（不断把检测proxy的方法加入协程池）
        """
        self.gevent_pool.apply_async(
            self.__check_one_proxy, callback=self.__check_callback
        )

    def __check_one_proxy(self):
        """检测一个Proxy的具体逻辑实现"""
        # 从队列中获取要检测的proxy
        proxy = self.queue.get()
        # 检测proxy
        proxy = check_proxy(proxy)
        # 如果speed=-1，表示不可用
        if proxy.speed == -1:
            # 分数减一
            proxy.score -= 1
            # 如果分数变为0，则从数据库中删除
            if proxy.score == 0:
                self.mongo_pool.delete_one(proxy)
                logger.info(f"删除代理：{proxy}")
            # 如果分数不为0，则将proxy更新到数据库中
            else:
                self.mongo_pool.update_one(proxy)
        else:
            # 如果speed!=-1，表示可用，则恢复默认最高分
            proxy.score = MAX_SCORE
            # 并更新到数据库中
            self.mongo_pool.update_one(proxy)
        # 通知队列当前任务已经完成，计数器要减一
        self.queue.task_done()
    
    @classmethod
    def start(cls):
        """作为启动代理检测模块的入口方法
        使用schedule模块，每隔一定的时间，执行一次检测任务
        """
        # 创建实例
        proxy_tester = cls()
        # 立马启动，否则需要等待一个周期才启动
        proxy_tester.run()
        # 根据配置文件的配置，指定实例的run方法执行的周期
        schedule.every(RUN_TEST_INTERVAL_HOURS).hours.do(proxy_tester.run)
        # 不断检测schedule的状态，周期抵达时激活执行
        while True:
            # 每隔1秒检测一次周期状态
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    ProxyTester.start()
