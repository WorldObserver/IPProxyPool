import logging

# 代理池中代理IP的默认评分
MAX_SCORE = 50

# 日志的配置
LOG_LEVEL = logging.WARNING   # 默认等级
LOG_FMT = '%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 请求的超时时间，单位是秒
TIMEOUT = 10

# MongoDB
MONGO_URL = 'mongodb://localhost:27017'
DATABASE = 'proxies_pool'
COLLECTION = 'proxies'

# Spiders
PROXIES_SPIDERS = [
    # 'core.proxy_spider.proxy_spiders.Ip3366Spider',
    'core.proxy_spider.proxy_spiders.ProxyListPlusSpider',
    'core.proxy_spider.proxy_spiders.KuaidailiSpider',
]

# 运行爬虫模块的间隔时间(小时)
RUN_SPIDERS_INTERVAL_HOURS = 2

# 运行检测模块的间隔时间(小时)
RUN_TEST_INTERVAL_HOURS = 2

# 检测模块检测proxy的并发协程数量
TEST_PROXY_ASYNC_COUNT = 5

# 随机返回一个代理IP时，随机的范围
# 越小可用性越高（代理IP范围是根据分数降序和速度升序排序的），越大随机性越高
MAX_PROXIES_RANGE = 50

# Web API 模块端口
WEB_API_PORT = 16888
