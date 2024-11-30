"""
实现通用爬虫
 -目标: 实现可以指定不同URL列表, 分组的XPATH和详情的XPATH, 从不同页面上提取代理的IP,端口号和区域的通用爬虫; 
 - 步骤:
     1. 在base_spider.py文件中,定义一个BaseSpider类
     2. 提供三个类成员变量:
         - urls: 代理IP网址的URL的列表
         - group_xpath: 分组XPATH, 获取包含代理IP信息标签列表的XPATH
         - detail_xpath: 组内XPATH, 获取代理IP详情的信息XPATH, 格式为: {'ip':'xx', 'port':'xx', 'area':'xx'}
     3. 提供初始方法, 传入爬虫URL列表, 分组XPATH, 详情(组内)XPATH
     4. 对外提供一个获取代理IP的方法 
         - 遍历URL列表, 获取URL
         - 根据发送请求, 获取页面数据
         - 解析页面, 提取数据, 封装为Proxy对象
         - 返回Proxy对象列表
"""
from lxml import etree
import requests
from utils.http import get_request_headers
from model import Proxy 
import random
import time


class BaseSpider:

    urls = []         # 代理IP网站的URL的列表
    group_xpath = ''  # 分组XPATH, 获取包含代理IP信息标签列表的XPATH
    detail_xpath = {} # 组内XPATH, 获取代理IP详情的信息XPATH, 格式为: {'ip':'xx', 'port':'xx', 'area':'xx'}

    def __init__(self, urls=[], group_xpath='', detail_xpath={}):
        """初始化方法, 传入爬虫URL列表, 分组XPATH, 详情(组内)XPATH
        只有在显示传入参数时, 才会使用传入的参数, 否则使用类成员变量的默认值
        """
        if urls:
            self.urls = urls
        if group_xpath:
            self.group_xpath = group_xpath
        if detail_xpath:
            self.detail_xpath = detail_xpath


    def get_page_from_url(self, url):
        """请求url获取页面内容"""
        response = requests.get(url, headers=get_request_headers())
        return response.content

    def _get_first_from_list(self, lis):
        """从列表中获取第一个元素, 如果列表为空, 则返回空字符串"""
        return lis[0] if len(lis) != 0 else ''

    def get_proxies_from_page(self, page):
        """从页面中提取ip、port和area并返回封装的Proxy对象"""
        # 使用lxml的etree模块解析页面
        html = etree.HTML(page)
        # 使用分组xpath提取包含代理IP信息标签列表
        trs = html.xpath(self.group_xpath)
        # 遍历分组标签列表
        for tr in trs:
            # 使用_get_first_from_list方法提取ip、port和area
            # 可以在没有提取到内容时返回空字符串，避免直接使用索引可能引发的报错
            # 提取ip
            ip = self._get_first_from_list(tr.xpath(self.detail_xpath['ip']))
            # 提取port
            port = self._get_first_from_list(tr.xpath(self.detail_xpath['port']))
            # 提取area
            area = self._get_first_from_list(tr.xpath(self.detail_xpath['area']))
            # 返回Proxy对象
            yield Proxy(ip, port, area=area)
        
        
    def get_proxies(self):
        """获取一个网站的所有代理IP的方法
        """
        # 遍历URL列表, 获取URL
        for url in self.urls:
            # 随机休眠1-3秒, 防止因频繁请求被封IP或返回异常数据
            time.sleep(random.uniform(1, 3))
            # 根据发送请求, 获取页面数据
            page = self.get_page_from_url(url)
            # 解析页面, 提取数据, 封装为Proxy对象
            # proxies = self.get_proxies_from_page(page)
            proxies = self.get_proxies_from_page(page)
            # 返回Proxy对象生成器
            yield from proxies


if __name__ == '__main__':
    config = {
        'urls': [f'http://www.ip3366.net/free/?stype=1&page={i}' for i in range(1, 4)],
        'group_xpath':"//*[@id='list']/table/tbody/tr",
        'detail_xpath': {
            'ip': './td[1]/text()',
            'port': './td[2]/text()',
            'area': './td[5]/text()'
        }
    }
    spider = BaseSpider(urls=config['urls'], group_xpath=config['group_xpath'], detail_xpath=config['detail_xpath'])
    for proxy in spider.get_proxies():
        print(proxy)
