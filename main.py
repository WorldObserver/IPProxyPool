"""
启动整个代理池项目的入口模块
- 使用多进程的方式启动爬虫模块、检测模块、API服务模块三个进程
"""
from multiprocessing import Process
from core.proxy_spider.run_spiders import RunSpider
from core.proxy_test import ProxyTester
from core.proxy_api import ProxyApi

def run():
    """作为启动整个代理池项目的入口的函数"""
    # 创建进程列表
    process_list = list()
    # 创建爬虫进程
    process_list.append(Process(target=RunSpider.start))
    # 创建检测进程
    process_list.append(Process(target=ProxyTester.start))
    # 创建API服务进程
    process_list.append(Process(target=ProxyApi.start))

    # 遍历进程列表
    for process in process_list:
        # 设置进程为守护进程
        process.daemon = True
        # 启动进程
        process.start()

    # 遍历进程列表
    for process in process_list:
        # 阻塞主进程，使其等待子进程结束
        process.join()

if __name__ == '__main__':
    run()
