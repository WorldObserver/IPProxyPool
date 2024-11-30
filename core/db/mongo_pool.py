import random
"""
代理池数据库模块 
- 作用: 用于对proxies集合进行数据库的相关操作
- 目标: 实现对数据库增删改查相关操作
- 步骤: 
  1. 定义MongoPool类
  2. 实现初始化方法, 建立数据连接, 获取要操作的集合
  3. 实现插入功能
  4. 实现修改功能
  5. 实现保存功能, 如果不存在就插入, 如果存在了就更新
  6. 实现查询功能: 根据条件进行查询, 可以指定查询数量, 按照分数降序然后速度升序排, 保证优质的代理IP在上面
  7. 实现删除功能: 根据代理的IP删除代理
  8. 实现根据协议类型 和 要访问网站的域名, 获取代理IP列表
  9. 实现根据协议类型 和 要访问完整的域名, 随机获取一个代理IP
"""
import pymongo
from model import Proxy
from settings import MONGO_URL, DATABASE, COLLECTION
from utils.log import logger

class MongoPool:
    def __init__(self):
        """初始化"""
        # 建立数据库连接
        self.client = pymongo.MongoClient(MONGO_URL)
        # 获取要操作的集合
        self.proxies = self.client[DATABASE][COLLECTION]
        

    def insert_one(self, proxy):
        """保存代理IP到数据库中"""

        # 检查代理IP是否存在
        count = self.proxies.count_documents({'_id': proxy.ip})
        # 如果代理IP不存在, 则插入
        if count == 0:
            dic = proxy.__dict__
            dic['_id'] = proxy.ip
            self.proxies.insert_one(dic)
            logger.info(f'insert success: {proxy}')
        # 如果代理IP存在, 则打印代理IP已经存在
        else:
            logger.warning(f'Proxy already existed: {proxy}')

    def update_one(self, proxy):
        """更新代理IP"""
        self.proxies.update_one({'_id': proxy.ip}, {'$set': proxy.__dict__})

    def delete_one(self, proxy):
        """删除代理IP"""
        self.proxies.delete_one({'_id': proxy.ip})

    def find_all(self):
        """查询所有代理IP"""
        cursor = self.proxies.find()
        for item in cursor:
            item.pop('_id')
            yield Proxy(**item)

    def find(self, conditions={}, count=0):
        """根据条件查询代理IP,可以指定查询数量,按照分数降序,然后速度升序,保证优质的代理IP在上面
        :param conditions: 查询条件
        :param count: 查询数量
        :return: 返回满足条件的代理IP列表
        """
        # 根据条件查询代理IP
        cursor = self.proxies.find(conditions, limit=count).sort([
            ('score', pymongo.DESCENDING), ('speed', pymongo.ASCENDING)
        ])

        # 将查询结果转换为列表
        proxy_list = list()
        for item in cursor:
            item.pop('_id')
            proxy_list.append(Proxy(**item))
        
        return proxy_list

    def get_proxies(self, protocol=None, domain=None, nick_type=0, count=0):
        """
        根据协议类型、要访问网站的域名和匿名程度, 获取代理IP列表，可以指定要获取的代理IP的个数
        :param protocol: 协议类型(http, https), 默认值为None, 表示http和https都支持
        :param domain: 要访问网站的域名, 默认值为None, 表示不指定域名
        :param count: 查询数量, 默认值为0, 表示不指定数量
        :param nick_type: 匿名程度(高匿:0, 匿名:1, 透明:2), 默认值为0, 表示高匿
        :return: 返回满足条件的代理IP列表
        """
        # 初始化查询条件
        conditions = {'nick_type': nick_type}

        # 根据协议类型设置查询条件
        # 如果协议类型为None, 则表示查询http和https都支持的代理IP, protocol的值为2
        if protocol is None:
            conditions['protocol'] = 2
        # 如果协议类型为http, 则表示查询支持http的代理IP, protocol的值为0或2
        elif protocol.lower() == 'http':
            conditions['protocol'] = {'$in': [0, 2]}
        # 如果协议类型为https, 则表示查询支持https的代理IP, protocol的值为1或2
        else:
            conditions['protocol'] = {'$in': [1, 2]}

        # 如果域名为None, 则表示不指定域名
        # 否则根据域名设置查询条件
        if domain:
            conditions['disable_domains'] = {'$nin': [domain]}

        # 调用find方法查询代理IP
        return self.find(conditions=conditions, count=count)
    
    def get_random_proxy(self, protocol=None, domain=None, nick_type=0, count=0):
        """根据协议类型、要访问网站的域名和匿名程度,随机获取一个代理IP
        :param protocol: 协议类型(http, https), 默认值为None, 表示http和https都支持
        :param domain: 要访问网站的域名, 默认值为None, 表示不指定域名
        :param nick_type: 匿名程度(高匿:0, 匿名:1, 透明:2), 默认值为0, 表示高匿
        :param count: 获取随机代理IP的范围, 默认值为0, 表示在所有满足条件的代理IP中随机获取一个
        :return: 返回一个满足条件的代理IP
        """
        # 调用get_proxies方法获取满足条件的代理IP列表
        proxy_list = self.get_proxies(protocol=protocol, domain=domain, nick_type=nick_type, count=count)
        # 如果代理IP列表不为空, 则随机返回一个代理IP
        if proxy_list:
            return random.choice(proxy_list)
        # 如果代理IP列表为空, 则返回None
        else:
            return None

    def disable_domain(self, ip, domain):
        """将指定域名添加到指定代理IP的不可用域名列表中"""
        # 检查指定代理IP的不可用域名列表中是否已经存在指定域名
        # 如果不存在，则添加进去
        if self.proxies.count_documents({'_id': ip, 'disable_domains': domain}) == 0:
            self.proxies.update_one({'_id': ip}, {'$push': {'disable_domains': domain}})

    def close(self):
        """关闭数据库连接"""
        self.client.close()

    def __del__(self):
        """关闭数据库连接"""
        try:
            self.close()
        except Exception as e:
            logger.error(f'Error closing MongoDB client: {e}')

if __name__ == '__main__':
    from model import Proxy

    mongo = MongoPool()

    proxy1 = Proxy('124.89.97.43', '80', protocol=1, score=10, nick_type=0, speed=0.38, disable_domains=['baidu.com'])
    proxy2 = Proxy('124.89.97.40', '80', protocol=2, score=12, nick_type=2, speed=0.37, disable_domains=['taobao.com']  )
    proxy3 = Proxy('124.89.97.44', '80', protocol=1, score=9, nick_type=0, speed=0.30, disable_domains=['google.com'])
    proxy4 = Proxy('124.89.97.45', '80', protocol=0, score=22, nick_type=1, speed=0.31, disable_domains=['jd.com'])

    mongo.disable_domain(proxy1.ip, 'baidu.com')
