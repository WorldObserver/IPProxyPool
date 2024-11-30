"""
目标:
    为爬虫提供高可用代理IP的Web服务接口
步骤:
    1. 实现根据协议类型和域名, 提供随机的获取高可用代理IP的服务
    2. 实现根据协议类型和域名, 提供获取多个高可用代理IP的服务
    3. 实现给指定的IP上追加不可用域名的服务
实现:
    - 在proxy_api.py中, 创建ProxyApi类
    - 实现初始方法
        - 初始一个Flask的Web服务
    - 实现根据协议类型和域名, 提供随机的获取高可用代理IP的服务
        - 可用通过 protocol 和 domain 参数对IP进行过滤
        - protocol: 当前请求的协议类型
        - domain: 当前请求域名
    - 实现根据协议类型和域名, 提供获取多个高可用代理IP的服务
        - 可用通过protocol 和 domain 参数对IP进行过滤
    - 实现给指定的IP上追加不可用域名的服务
        - 如果在获取IP的时候, 有指定域名参数, 将不在获取该IP, 从而进一步提高代理IP的可用性
    - 实现run方法, 用于启动Flask的WEB服务
    - 实现start的类方法, 用于通过类名, 启动服务
"""

from flask import Flask
from flask import request
from core.db.mongo_pool import MongoPool
from settings import MAX_PROXIES_RANGE
from settings import WEB_API_PORT   
import json


class ProxyApi:
    def __init__(self):
        """初始化方法"""
        # 初始化Flask的Web服务
        self.app = Flask(__name__)
        # 初始化MongoDB数据库操作对象
        self.mongo_pool = MongoPool()

        # 根据协议类型和域名, 提供随机的高可用代理IP的服务
        @self.app.route("/random")
        def random():
            # 从请求参数中, 获取协议类型
            protocol = request.args.get("protocol")
            # 从请求参数中, 获取域名
            domain = request.args.get("domain")
            # 根据指定的协议和域名，从MongoDB数据库中, 随机获取一个高可用代理IP
            # 随机获取代理IP的范围，由配置文件中的MAX_PROXIES_RANGE指定
            proxy = self.mongo_pool.get_random_proxy(
                protocol=protocol, domain=domain, count=MAX_PROXIES_RANGE
            )

            # 如果获取到了代理IP
            if proxy:
                # 如果协议不为空，则返回协议://IP:端口
                if protocol:
                    return f"{protocol}://{proxy.ip}:{proxy.port}"
                else:
                    # 如果协议为空，则返回IP:端口
                    return f"{proxy.ip}:{proxy.port}"
            else:
                # 如果获取不到代理IP，则返回指定条件的代理IP不存在
                return "指定条件的代理IP不存在"

        # 根据协议类型和域名, 提供获取多个高可用代理IP的服务
        @self.app.route("/proxies")
        def proxies():
            # 从请求参数中, 获取协议类型
            protocol = request.args.get("protocol")
            # 从请求参数中, 获取域名
            domain = request.args.get("domain")
            # 根据指定的协议和域名，从MongoDB数据库中, 获取多个高可用代理IP
            # 获取代理IP的范围，由配置文件中的MAX_PROXIES_RANGE指定
            proxies = self.mongo_pool.get_proxies(
                protocol=protocol, domain=domain, count=MAX_PROXIES_RANGE
            )

            # 如果获取到了指定条件的代理IP的列表(proxy对象的形式)
            if proxies:
                # 将proxy对象列表转换为字典的列表，方便json序列化
                proxies = [proxy.__dict__ for proxy in proxies]
                # 返回json格式的代理IP列表
                return json.dumps(proxies, ensure_ascii=False, indent=2)
            else:
                # 如果获取不到指定条件的代理IP，则返回指定条件的代理IP不存在
                return "指定条件的代理IP不存在"

        # 给指定的IP上追加不可用域名的服务
        @self.app.route("/disable_domain")
        def disable_domain():
            # 从请求参数中, 获取IP
            ip = request.args.get("ip")
            # 从请求参数中, 获取域名
            domain = request.args.get("domain")

            # 如果IP参数为空, 返回提示信息
            if not ip:
                return "请提供IP"
            # 如果域名参数为空, 返回提示信息
            if not domain:
                return "请提供域名"

            # 如果指定的IP不存在, 返回提示信息
            if len(self.mongo_pool.find(conditions={"_id": ip})) == 0:
                return "指定的代理IP不存在"

            # 给指定的IP上追加不可用域名
            self.mongo_pool.disable_domain(ip=ip, domain=domain)
            # 返回追加不可用域名成功的信息
            return f"{ip} 禁用域名 {domain} 成功"

    def run(self):
        """启动Flask的Web服务"""
        self.app.run("0.0.0.0", port=WEB_API_PORT)

    @classmethod
    def start(cls):
        """作为启动整个Flask的Web服务的入口的类方法"""
        # 初始化ProxyApi类
        proxy_api = cls()
        # 启动Flask的Web服务
        proxy_api.run()


if __name__ == "__main__":
    ProxyApi.start()
