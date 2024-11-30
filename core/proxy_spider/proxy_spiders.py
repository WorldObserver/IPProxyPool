"""针对不同的代理IP网站, 定义不同的具体爬虫类
只要继承BaseSpider类, 并以实现类属性的方式指定具体的url列表, 分组XPATH和详情XPATH, 
就可以实现一个新的爬虫类。其他的方法都自动从BaseSpider类中继承。
"""
from core.proxy_spider.base_spider import BaseSpider
from lxml import etree
from model import Proxy
from retrying import retry
import re
import json
from settings import TIMEOUT
from utils.http import get_request_headers
from utils.log import logger
import requests
import urllib3
urllib3.disable_warnings()

class Ip3366Spider(BaseSpider):
    """爬取ip3366网站的爬虫类"""
    # 列表页的url列表
    urls = [f"http://www.ip3366.net/free/?stype=1&page={i}" for i in range(1, 8)]
    # 分组XPATH
    group_xpath = "//*[@id='list']/table/tbody/tr"
    # 详情XPATH
    detail_xpath = {
        "ip": "./td[1]/text()",
        "port": "./td[2]/text()",
        "area": "./td[5]/text()",
    }

class ProxyListPlusSpider(BaseSpider):
    """爬取ProxyListPlus网站的爬虫类"""
    # 列表页的url列表
    urls = [f"https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-{i}" for i in range(1, 7)]
    # 分组XPATH
    group_xpath = '//*[@id="page"]/table[2]/tr[position() > 2]'
    # 详情XPATH
    detail_xpath = {
        "ip": "./td[2]/text()",
        "port": "./td[3]/text()",
        "area": "./td[5]/text()",
    }

class KuaidailiSpider(BaseSpider):
    """爬取快代理网站的爬虫类"""
    # 列表页的url列表
    urls = [f"https://www.kuaidaili.com/free/inha/{i}/" for i in range(1, 11)]

    # 快代理的请求偶发SSL错误，所以需要重写get_page_from_url方法
    # 设置超时时间，和重试次数
    @retry(stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
    def get_page_from_url(self, url):
        """请求url获取页面内容"""
        try:
            response = requests.get(url, headers=get_request_headers(), timeout=TIMEOUT, verify=False)
            return response.content
        except Exception as e:
            logger.exception(f"请求{url}失败, 错误信息为{e}")
            return None
    
    # 快代理的代理IP在页面中的布局结构和前两个爬虫不一样
    # 所以需要重写get_proxies_from_page方法, 用不一样的提取逻辑解析页面, 获取ip、port和area
    def get_proxies_from_page(self, page):
        """从页面中提取ip、port和area并返回封装的Proxy对象"""
        # 如果页面为空, 则记录日志并结束方法执行
        if page is None:
            logger.exception(f"获取页面失败")
            return
        # 解码传入的page参数(bytes类型), 获取页面内容
        html_str = page.decode()
        # 使用正则表达式提取包含代理IP信息的字符串
        ip_list_str = re.search(r'const fpsList = (\[.*?\]);', html_str, re.S).group(1)
        # 将字符串转换为json对象(包含代理IP信息的字典组成的列表)
        ip_list_json = json.loads(ip_list_str)
        # 遍历这个列表
        for item in ip_list_json:
            # 提取ip
            ip = item['ip']
            # 提取port
            port = item['port']
            # 提取area
            area = item['location']
            # 返回Proxy对象
            yield Proxy(ip, port, area=area)

if __name__ == '__main__':
    # spider = Ip3366Spider()
    # spider = ProxyListPlusSpider()
    spider = KuaidailiSpider()
    for proxy in spider.get_proxies():
        print(proxy)
