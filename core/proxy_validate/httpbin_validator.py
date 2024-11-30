import requests
import json
import time
from settings import TIMEOUT
from utils.http import get_request_headers
from utils.log import logger
from model import Proxy

def check_proxy(proxy):
    """检查代理IP是否可用"""
    # 根据要检查的proxy对象，设置requests模块的proxies参数
    proxies = {
        "http": f'http://{proxy.ip}:{proxy.port}',
        "https": f'https://{proxy.ip}:{proxy.port}'
    }

    # 检查http代理IP
    is_http, http_nick_type, http_speed = _check_http_proxy(proxies)
    # 检查https代理IP
    is_https, https_nick_type, https_speed = _check_http_proxy(proxies, is_http=False)

    # 如果http和https都支持，则设置协议类型为2
    if is_http and is_https:
        proxy.protocol = 2
        proxy.nick_type = http_nick_type  # 都支持则以http的匿名类型为准
        proxy.speed = http_speed          # 都支持则以http的速度为准
    # 如果只支持http，则设置协议类型为0
    elif is_http:
        proxy.protocol = 0
        proxy.nick_type = http_nick_type
        proxy.speed = http_speed
    # 如果只支持https，则设置协议类型为1
    elif is_https:
        proxy.protocol = 1
        proxy.nick_type = https_nick_type
        proxy.speed = https_speed
    # 如果都不支持，则设置协议类型、匿名类型、速度为-1
    # 表示该代理IP不可用
    else:
        proxy.protocol = -1
        proxy.nick_type = -1
        proxy.speed = -1
    
    # 返回检测后的proxy对象
    return proxy

def _check_http_proxy(proxies, is_http=True):
    """检查http或https代理IP是否可用"""
    # 初始化匿名类型和速度为-1   
    nick_type = -1
    speed = -1

    # 如果is_http为True, 则检查代理IP是否支持http
    if is_http:
        test_url = "http://www.httpbin.org/get"
    # 否则检查代理IP是否支持https
    else:
        test_url = "https://www.httpbin.org/get"
    
    # 设置超时时间(从配置文件导入配置)
    timeout = TIMEOUT
    # 获取随机请求头
    req_headers = get_request_headers()
    try:
        # 记录开始时间
        start = time.perf_counter()
        # 发送请求, 获取响应    
        response = requests.get(test_url, proxies=proxies, headers=req_headers, timeout=timeout)
        # 如果请求成功
        if response.ok:
            # 记录结束时间
            end = time.perf_counter()
            # 计算结束时间和开始时间的差值，即为代理IP的速度, 单位为秒，保留两位小数
            speed = round(end - start, 2)

            # 获取响应内容
            content = json.loads(response.text)
            # 获取响应头
            res_headers = content['headers']
            # 获取httpbin检测到的来源IP
            origin = content['origin']
            # 获取httpbin检测到的代理连接
            proxy_connection = res_headers.get('Proxy-Connection')

            # 判断代理IP的匿名类型
            # 如果origin中包含逗号, 则表示origin中包含两个IP, 说明httpbin检测到了代理IP的存在
            # 那么表明代理IP为透明代理, nick_type的值为2
            if ',' in origin:
                nick_type = 2
            # 否则：如果Proxy-Connection字段存在, 则表示代理IP为普通匿名代理, nick_type的值为1
            elif proxy_connection:
                nick_type = 1
            # 否则：表示代理IP为高匿名代理, nick_type的值为0
            else:
                nick_type = 0
            
            # 返回表示代理IP可用的布尔值True、匿名类型和速度
            return True, nick_type, speed
        # 如果请求失败，则返回表示代理IP不可用的布尔值False、匿名类型(-1)和速度(-1)
        else:
            return False, nick_type, speed
    except Exception as e:
        # 如果整个检测的过程出现异常，则返回表示代理IP不可用的布尔值False、匿名类型(-1)和速度(-1)
        return False, nick_type, speed

if __name__ == '__main__':
    proxy = Proxy(ip='5.58.97.89', port='61710')
    print(check_proxy(proxy))
