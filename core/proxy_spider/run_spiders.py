"""
- 目标: 根据配置文件信息, 加载爬虫, 抓取代理IP, 进行校验, 如果可用, 写入到数据库中
- 思路: 
    - 在run_spider.py中, 创建RunSpider类
    - 提供一个运行爬虫的run方法, 作为运行爬虫的入口, 实现核心的处理逻辑
        - 根据配置文件信息, 获取爬虫对象列表.
        - 获取爬虫对象, 遍历爬虫对象的get_proxies方法, 获取代理IP
        - 检测代理IP(代理IP检测模块)
        - 如果可用,写入数据库(数据库模块)
        - 处理异常, 防止一个爬虫内部出错了, 影响其他的爬虫. 
    - 使用异步来执行每一个爬虫任务, 以提高抓取代理IP效率
        - 在init方法中创建协程池对象
        - 把处理一个代理爬虫的代码抽到一个方法
        - 使用异步执行这个方法
        - 调用协程的join方法, 让当前线程等待协程任务的完成. 
    - 使用schedule模块, 实现每隔一定的时间, 执行一次爬取任务
        - 定义一个start的类方法
        - 创建当前类的对象, 调用run方法
        - 使用schedule模块, 每隔一定的时间, 执行当前对象的run方法
"""
from gevent import monkey
monkey.patch_all()  # 打补丁, 让gevent识别耗时操作
import importlib
from settings import PROXIES_SPIDERS
from core.proxy_validate.httpbin_validator import check_proxy
from core.db.mongo_pool import MongoPool
from utils.log import logger
from gevent.pool import Pool
import schedule
import time
from settings import RUN_SPIDERS_INTERVAL_HOURS


class RunSpider:
    def __init__(self):
        """初始化方法
        获取数据库操作对象
        """
        self.mongo_pool = MongoPool()
        self.gevent_pool = Pool()

    def get_spider_from_settings(self):
        """根据配置文件信息, 返回爬虫对象列表"""
        for path in PROXIES_SPIDERS:
            # 根据配置字符串解析出爬虫模块名和爬虫类名
            module_name, cls_name = path.rsplit('.', maxsplit=1)
            # 动态加载爬虫模块
            module = importlib.import_module(module_name)
            # 从爬虫模块中获取爬虫对象
            spider_cls = getattr(module, cls_name)
            # 创建爬虫实例，并通过生成器方式返回
            spider = spider_cls()
            yield spider


    def __execute_one_spider_task(self, spider):
        """把处理一个爬虫的代码抽到这个方法中"""
        # 处理异常, 防止一个爬虫内部出错了, 影响其他的爬虫. 
        try:
            # 遍历爬虫对象的get_proxies方法, 获取代理IP对应的Proxy对象
            for proxy in spider.get_proxies():
                # 检测代理IP(代理IP检测模块)
                print(f'正在检测: {proxy}')
                proxy = check_proxy(proxy)
                # 如果代理IP可用（speed不为-1）,就存入数据库
                if proxy.speed != -1:
                    self.mongo_pool.insert_one(proxy)
        # 捕获异常,打印异常信息
        except Exception as e:
            logger.exception(e)


    def run(self):
        """提供一个运行爬虫的run方法, 作为运行爬虫的入口, 实现核心的处理逻辑
        """
        # 获取爬虫对象生成器
        spiders = self.get_spider_from_settings()
        # 遍历爬虫对象
        for spider in spiders:
            # 用异步协程的方式执行每个爬虫的任务
            self.gevent_pool.apply_async(self.__execute_one_spider_task, args=(spider, ))
        # 阻塞主线程使其等待所有协程任务执行完毕
        self.gevent_pool.join()

    
    @classmethod
    def start(cls):
        """作为启动入口的类方法
        使用schedule模块, 实现每隔一定的时间, 执行一次爬取任务
        """
        # 创建实例
        run_spider = cls()
        # 立马启动，否则需要等待一个周期才启动
        run_spider.run()
        # 指定实例的run方法执行的周期
        schedule.every(RUN_SPIDERS_INTERVAL_HOURS).hours.do(run_spider.run)
        # 不断检测schedule的状态，周期抵达时激活执行
        while True:
            # 每一秒检测一次周期状态
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    RunSpider.start()
