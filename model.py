"""定义代理对象的数据模型"""
from settings import MAX_SCORE

class Proxy:
    def __init__(self, ip, port, protocol=-1, nick_type=-1, speed=-1, area=None, score=MAX_SCORE, disable_domains=None):
        """初始化代理对象。
        :param ip: 代理的IP地址。
        :param port: 代理IP的端口号。
        :param protocol: 代理IP支持的协议类型。http是0, https是1, https和http都支持是2。默认为-1。
        :param nick_type: 代理IP的匿名程度。高匿:0, 匿名:1, 透明:2。默认为-1。
        :param speed: 代理IP的响应速度,单位为秒。默认为-1。
        :param area: 代理IP所在地区。默认为None。
        :param score: 代理IP的评分,用于衡量代理的可用性。默认分值可以通过配置文件进行配置。在进行代理可用性检查时，每遇到一次请求失败就减1分，减到0的时候从池中删除。如果检查代理可用，就恢复默认分值。默认为MAX_SCORE。
        :param disable_domains: 不可用域名列表。有些代理IP在某些域名下不可用,但是在其他域名下可用。默认为空列表。
        """
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.nick_type = nick_type
        self.speed = speed
        self.area = area
        self.score = score
        self.disable_domains = disable_domains or []
    
    def __str__(self):
        return str(self.__dict__)
