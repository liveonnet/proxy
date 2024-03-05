# 配置文件格式参考 https://www.v2fly.org/config/overview.html
# 改进：针对多个节点来源，同步依次获取变为异步同时获取(asncio.gather)
# 改进：随着来源增多，待测试节点数量达到几千，一个一个创建v2ray进程做测试比较慢，前置增加用asyncio.open_connection完成的简单连通性测试
# 改进：批量测试连通性时v2ray用到的配置文件从/tmp目录转到/dev/shm目录，因为后者实际是内存映射出的，达到配置文件实际不落盘的效果
# 改进：批量测试连通性时v2ray用到的配置文件从写入/dev/shm改为直接通过STDIN传给v2ray进程，不再体现在/dev/shm中
# 增加判断v2ray进程是否被杀，如果被杀则重新选择节点
# 20230804 使用uvloop替代默认事件循环
# 20230806 因为经常收到 future exception was never retrieved , 暂时去掉uvloop
# 20230810 改进节点选择，优先级美国>英国>其他
# 使用_filterBySimpleLow代替_filterBySimple以尝试加快过滤速度, 用`ulimit -n `增加单进程最大打开文件数
# 20230817 增加_host2ip，用于根据域名获取ip地址，测试连通性时用获取到的ip地址，生成配置文件时用ip地址替代域名，修复了以前不能连接地址本身是域名的节点的bug
# 20230818 测试连通性时同时打开的进程数可配置;去掉定点更新节点的方式，完全靠连通性测试自主决定何时更新节点
# 20230905 特殊处理网站内容时捕捉所有异常避免程序崩溃
# 20230918 节点结构的source在排重后变为包含它的来源url列表。统计时，多来源的有效节点，在其所有来源url中都计为有效
# 20231012 增加对mibei页面的解析，找出最近放出的免费节点
# 20231013 接受命令行参数-t, 进入测试模式；增加几个站点的支持
# 20231018 去掉Node结构中的extra，增加站点支持
# 20231024 增加对tolinkshare的支持, 改进 https://wanshanziwo.eu.org/ss/sub 开通数据的特殊处理
# 20231031 增加备选节点数量，缩短节点测试的时间间隔
# 20231031 1秒内按多次CTRL+C才认为是要退出程序, 避免误操作退出
# 20231101 改进 preexec_ignore_sigint，增加setpgrp
# 20231106 ghproxy.com被墙，暂时改为gh-proxy.com
# 20231109 完善_parseProto中的注释，完善特殊处理, 完善bas64解码失败时尝试加padding
# 20231110 完善特殊处理，修改vless配置生成, do_newvless代替do_vless看看效果
# 20231110 vless 支持 reality 测试未通过，配置文件的outboundsSetting和win上的一样，但是linux下无法通过测试
# 20231113 完善http返回429时的重试机制
# 20231114 增加类LaunchProxyMix以便实现不同类型代理的进程创建过程, 添加对hysteria v1/v2的支持，其中v2因无实际服务器而暂时无法测试
# 20231115 测试hysteriav2
# 20231116 wanshanziwo.eu.org下线，注释掉相关代码, 添加函数b64d以统一添加补全功能，do_newvless正式取代do_vless
# 20231117 因为aiohttp通过hysteria2代理访问网站时会报错(orangepi上测试)，换用httpx做链接测试; 减少重试次数以加快代理寻找过程；使用异步worker加快代理测试
# 20231121 代理开启本地无密码socks5 10808端口服务，方便测试和git使用
# 20231122 优化：启动节点时马上进行测试，避免失效节点在初次启动时不能马上被排除
# 20231124 raw.fastgit.org替换gh-proxy.com, 监测当前节点健康度时verify=False
# 20231209 raw.githubusercontent.com替换raw.fastgit.org
# 20231213 raw.fastgit.org替换raw.githubusercontent.com
# 20230102 增加支持 https://github.com/freenodes/freenodes/
# 20230104 支持 Barabama/FreeNodes/ 节点内容
#          以纯真ip库为判断依据过滤一部分地区的节点
# 20230105 完善安国别统计相关逻辑，不再按alias过滤，使用赋值表达式简化代码
# 20230108 代理开启proxy_port+1无密码服务，方便pac使用；目前hysteria/2还不支持多http监听
#          暂时只使用10个来源的节点，减少评估时间
# 20231010 启用uvloop
# 20240109 代理开启proxy_port+1无密码服务，方便pac使用；目前hysteria/2还不支持多http监听; 暂时只使用10个来源的节点，减少评估时间
# 20240122 改进httpx的pool设置；增加端口号校验
# 20240124 统一处理clash yaml格式
# 20240201 程序结构大改, 并改名为get_proxy, 原来的make_proxy暂时保留。以前是依次执行获取节点、排重、从host取ip，根据地区过滤、socket连接简单过滤、实际连接测试，最后找出所有可用节点，并输出统计信息，然后选择一个节点启用，随着节点数增加，目前至少要等近十分钟才能执行完毕有节点可用，并且备选节点用光后需要重新处理，又要等待近10分钟才能用上。现在改为各步骤并行处理，找到第一个可用节点后马上启用，一般半分钟到一分钟就有节点可用，并且备用节点快用光时就重新获取可用节点，期间不影响当前节点使用且再无需等待新可用节点。代价是无法做统计。
# 20240218 添加节点；完善支持测试模式；可用节点达到10个则清空任务队列避免获取过多节点
# 20240220 过滤慢速节点，检查时间后面输出ping值
# 20240226 增加ipv6地址的判断和支持，v6的ip不参与按地区过滤，改进日志，增强vless支持, 命令行参数支持指定日志输出级别
# 20240227 改进日志, 增加节点, 最后一次节点访问重试时尝试通过http代理进行
# 20240228 Node结构增加保存地区信息用于展示, 改进日志，清理无用代码, 修正Node结构比较大小时未判断score是否为None的bug
# 20240229 增加节点, 改进测试模式下的日志输出
# 20240301 调整日志，改进vless生成配置的逻辑, 改进代码, 缩短测试当前节点的时间间隔
# 20240305 改进vless配置, uniq_node以天为间隔做节点排重，launcher改变test_mode参数名为measure_mode, 代理日志输出到/dev/shm目录


import binascii
from base64 import b64decode, b64encode
from datetime import datetime, timedelta
from contextlib import AsyncContextDecorator
from collections import Counter, OrderedDict
from itertools import chain, compress
from string import ascii_lowercase
from operator import attrgetter
import pprint
import signal
import aiohttp
# https://github.com/aio-libs/aiohttp/discussions/6044#discussioncomment-1432443
# https://github.com/aio-libs/aiohttp/discussions/6044
# #from aiohttp_socks import ProxyType, ProxyConnector
import asyncio
# 使用uvloop的话，通过http代理访问https网址时还是有警告
setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)
import uvloop
import sys
import io
import os
import os.path
from random import choice, sample, shuffle
import shlex
import subprocess
from subprocess import TimeoutExpired
from time import time
import ssl
import certifi
from collections import defaultdict
import json
from pathlib import PurePath
from copy import deepcopy
from urllib.parse import urlparse, unquote_plus, parse_qs, urlunparse, quote, unquote
from dataclasses import dataclass
import socket
import codecs
import re
import argparse
import selectors
import ipaddress
import jsonpickle
import yaml
import httpx
import anyio
from qqwry import QQwry
from dns.asyncresolver import Resolver
import dns.resolver
from functools import partial
from logging import INFO, DEBUG
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_random, retry_if_result, before_sleep_log, retry_if_exception_type, TryAgain
from loguru import logger
from get_proxy_conf import port_range
from get_proxy_conf import proxies, headers, conf_tpl
from get_proxy_conf import proxy_host, proxy_port, proxy_user, proxy_pass
from get_proxy_conf import test_wait_seconds
from get_proxy_conf import v2ray_path, hysteria_path, hysteria2_path, conf_basepath
from get_proxy_conf import inboundsSetting, outboundsSetting_vmess, outboundsSetting_ss, outboundsSetting_trojan, outboundsSetting_vless
from get_proxy_conf import settingHysteria , settingHysteria2
from get_proxy_conf import qqwry_path
pp = pprint.PrettyPrinter(indent=2, width=80, compact=True, sort_dicts=False)
event_exit = asyncio.Event()
CTRL_C_TIME: float = 0  # 记录最近一次按Ctrl+C的时间

mylogger, trace, debug, info, succ, warn, error, critical = None, None, None, None, None, None, None, None

@dataclass
class Node(object):
    '''代表节点的数据类
    '''
    proto: str
    uuid: str = ''
    ip: str = ''
    v4: bool = True
    port: int = 0
    param: str|list|dict = None  # 包含协议需要的
    alias: str = ''
    source: str = None  # 标明来源
    area: str = None  # 根据ip得出的地区

    # 用于连通性测试
    real_ip: str = ''  # ip字段为域名时，连通性测试前需要获取对应ip地址. 如果ip=real_ip说明ip是地址，如果real_ip为空说明ip是域名但无法解析出地址，如果real_ip不为空且real_ip!=ip说明ip是域名且能解析出地址
    score: int|None = None
    score_unit: str = 'ms'

    def __repr__(self):
        if self.proto == 'hysteria2' or self.proto == 'hy':
            return f'<N h2:{self.ip}:{self.port}>'
        else:
            return f'<N {self.proto[:2]}:{self.ip}:{self.port}>'

    def __hash__(self):
        return hash((str(self), self.uuid, json.dumps(self.param)))

    def __lt__(self, other):
        if self.score and other.score:
            return self.score < other.score
        elif self.score:
            return False
        else:
            return True

    def __le__(self, other):
        return self.score <= other.score

def signal_handler(sig: int):
    if sig == signal.SIGINT:
        global CTRL_C_TIME
        t = time()
        if CTRL_C_TIME and t - CTRL_C_TIME < 1:
            if not event_exit.is_set():
                warn('exit flag set')
                event_exit.set()
        else:
            CTRL_C_TIME = t
            warn('press agian in 1s to exit')


def preexec_ignore_sigint():
    '''https://stacktuts.com/how-to-stop-sigint-being-passed-to-subprocess-in-python
    '''
    # Ignore SIGINT in the child process
    debug(f'subprocess ignore SIGINT')
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # 在进程创建之初设置忽略ctrl+c，但不保证有效，因为后续子进程可能再次设置自己的信号处理
    os.setpgrp()  # 建立单独的进程组，避免父进程的ctrl+c传递进来


def b64d(s: str|bytes, url: str='', show: bool=True) -> str|None:
    '''解码base64
    支持添加'='来重试

    `s` 要尝试解码的数据
    `url` 数据来源
    `show` 是否打印出错信息
    '''
    rslt = None
    if isinstance(s, bytes):
        _s = s.decode()
    else:
        _s = s
    _s = _s.rstrip('\r\n')
    for _i in range(4):
        try:
            rslt = b64decode(_s + '='*_i, validate=True)
            break
        except:
            pass
    if rslt is None:
        if show:
            if len(s) >= 500:
                debug(f'64decode failed s[:100]={s[:100]} {url=}')
            else:
                debug(f'64decode failed {s=} {url=}')
    else:
        if isinstance(rslt, bytes):
            try:
                rslt = rslt.decode()
            except UnicodeDecodeError as e:
                if len(rslt) > 500:
                    debug(f'decode bytes failed {e=} rslt[:100]={rslt[:100]}, {url=}')
                else:
                    debug(f'decode bytes failed {e=} {rslt=} {url=}')
                rslt = None
    return rslt


class Ip2Area(object):
    '''查纯真ip库，根据ip获取地区信息
    '''
    p = re.compile('中国|北京|上海|重庆|天津|本机|局域|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|内蒙古|广西|西藏|宁夏|新疆|香港|澳门', re.U)
    pCountry = re.compile('中国|欧盟|蒙古|朝鲜|韩国|日本|菲律宾|越南|老挝|柬埔寨|缅甸|泰国|马来西亚|文莱|新加坡|印度尼西亚|东帝汶|尼泊尔|不丹|孟加拉国|印度|巴基斯坦|斯里兰卡|马尔代夫|哈萨克斯坦|吉尔吉斯斯坦|塔吉克斯坦|乌兹别克斯坦|土库曼斯坦|阿富汗|伊拉克|伊朗|叙利亚|约旦|黎巴嫩|以色列|巴勒斯坦|沙特阿拉伯|巴林|卡塔尔|科威特|阿拉伯联合酋长国|阿曼|也门|格鲁吉亚|亚美尼亚|阿塞拜疆|土耳其|塞浦路斯|芬兰|瑞典|挪威|冰岛|丹麦|法罗群岛|爱沙尼亚|拉脱维亚|立陶宛|白俄罗斯|俄罗斯|乌克兰|摩尔多瓦|波兰|捷克|斯洛伐克|匈牙利|德国|奥地利|瑞士|列支敦士登|英国|爱尔兰|荷兰|比利时|卢森堡|法国|摩纳哥|罗马尼亚|保加利亚|塞尔维亚|马其顿|阿尔巴尼亚|希腊|斯洛文尼亚|克罗地亚|波斯尼亚和墨塞哥维那|意大利|梵蒂冈|圣马力诺|马耳他|西班牙|葡萄牙|安道尔|埃及|利比亚|苏丹|突尼斯|阿尔及利亚|摩洛哥|亚速尔群岛|马德拉群岛|埃塞俄比亚|厄立特里亚|索马里|吉布提|肯尼亚|坦桑尼亚|乌干达|卢旺达|布隆迪|塞舌尔|乍得|中非|喀麦隆|赤道几内亚|加蓬|刚果共和国|刚果民主共和国|圣多美及普林西比|毛里塔尼亚|西撒哈拉|塞内加尔|冈比亚|马里|布基纳法索|几内亚|几内亚比绍|佛得角|塞拉利昂|利比里亚|科特迪瓦|加纳|多哥|贝宁|尼日尔|加那利群岛|赞比亚|安哥拉|津巴布韦|马拉维|莫桑比克|博茨瓦纳|纳米比亚|南非|斯威士兰|莱索托|马达加斯加|科摩罗|毛里求斯|留尼旺|圣赫勒拿|澳大利亚|新西兰|巴布亚新几内亚|所罗门群岛|瓦努阿图|密克罗尼西亚|马绍尔群岛|帕劳|瑙鲁|基里巴斯|图瓦卢|萨摩亚|斐济群岛|汤加|库克群岛|关岛|新喀里多尼亚|法属波利尼西亚|皮特凯恩岛|瓦利斯与富图纳|纽埃|托克劳|美属萨摩亚|北马里亚纳|加拿大|美国|墨西哥|格陵兰|危地马拉|伯利兹|萨尔瓦多|洪都拉斯|尼加拉瓜|哥斯达黎加|巴拿马|巴哈马|古巴|牙买加|海地|多米尼加共和国|安提瓜和巴布达|圣基茨和尼维斯|多米尼克|圣卢西亚|圣文森特和格林纳丁斯|格林纳达|巴巴多斯|特立尼达和多巴哥|波多黎各|英属维尔京群岛|美属维尔京群岛|安圭拉|蒙特塞拉特|瓜德罗普|马提尼克|荷属安的列斯|阿鲁巴|特克斯和凯科斯群岛|开曼群岛|百慕大|哥伦比亚|委内瑞拉|圭亚那|法属圭亚那|苏里南|厄瓜多尔|秘鲁|玻利维亚|巴西|智利|阿根廷|乌拉圭|巴拉圭|台湾', re.U)
    pPreferredArea = re.compile('美国|日本|亚太地区|台湾|韩国|英国|德国|荷兰|瑞典|新加坡|澳大利亚|菲律宾|乌克兰|俄罗斯', re.U)

    def __init__(self, qqwry_path: str):
        self.q = QQwry()
        self.q.load_file(qqwry_path)

    def getArea(self, ip: str) -> str:
        return self.q.lookup(ip)[0] if ip else ''

    def isMainland(self, ip: str) -> bool:
        '''标识是否为大陆地区，标中国、本机、局域网的也当成大陆地区
        '''
        return True if self.p.search(self.getArea(ip)) else False

    def isPreferredArea(self, ip: str) -> (bool, str):
        '''是否为优先使用的地区
        '''
        if m := self.pPreferredArea.match(self.getCountry(ip)):
            return (True, m.group(0))
        else:
            return (False, None)

    def getCountry(self, ip: str) -> str:
        '''将国家地区精简为国家 例如 `美国华盛顿` 精简为 `美国`
        欧盟、台湾也算
        '''
        if m := self.pCountry.match(area := self.getArea(ip)):
            return m.group(0)
        return area

    def clear(self):
        self.q.clear()


class aobject(object):
    '''支持异步构造函数
    '''

    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass


class ProxySupportMix(object):
    '''提供异步session和连接池的基类
    使用aiohttp
    '''

    def __init__(self):
        self.headers = headers
        self.timeout = aiohttp.ClientTimeout(total=60.0, connect=10.0, sock_connect=15.0, sock_read=30.0)
        self.sslcontext = ssl.create_default_context(cafile=certifi.where())
        self.connector = aiohttp.TCPConnector(force_close=True, limit=500, limit_per_host=0, enable_cleanup_closed=True, loop=None, ssl=self.sslcontext)
        self.client = aiohttp.ClientSession(headers=headers, timeout=self.timeout, connector=self.connector, connector_owner=True)

    async def clean(self):
        try:
            #debug(f'close connector')
            await self.connector.close()
        except:
            pass
        await asyncio.sleep(0.250)
        try:
            #debug(f'close client')
            await self.client.close()
        except:
            pass


class LaunchProxyMix(object):
    '''封装不同代理的进程启动逻辑
    '''
    def __init__(self):
        super().__init__()

    async def launch_proxy(self, node: Node, measure_mode: bool = False, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        '''`measure_mode` 为True时尝试通过命令行传入配置

        返回启动的进程和对应的配置文件路径，如果是命令行传入配置，则配置文件路径为空
        '''
        proto = node.proto
        match proto:
            case 'vmess' | 'vless' | 'ss' | 'trojan':
                return await self._launch_v2ray(node, measure_mode, port)
            case 'hysteria':
                return await self._launch_hysteria(node, measure_mode, port)
            case 'hysteria2':
                return await self._launch_hysteria2(node, measure_mode, port)
            case _:
                error(f'unknown proto {proto} !!!')
                return None, ''


    async def _launch_v2ray(self, node: Node, measure_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''
        if not measure_mode:
            # kill running one
            os.system("kill `ps xf| grep -v grep | grep v2ray | awk '{print $1}'` > /dev/null 2>&1")

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if measure_mode:
            settings['inbounds'].pop()  # 删除http2
            settings['inbounds'].pop()  # 删除socks
            settings['inbounds'][0]['listen'] = '127.0.0.1'
            settings['inbounds'][0]['port'] = port
            settings['inbounds'][0]['settings']['auth'] = 'noauth'
            settings['inbounds'][0]['settings']['accounts'] = []
            settings['routing'] = {
                "domainStrategy": "AsIs",
                "domainMatcher": "mph",
                "rules": [],
                "balancers": []
            }
#-#
#-#            trace(f'{node} --> {pp.pformat(settings["outbounds"])}')
#-#            filepath_tmp = PurePath('/dev/shm/', f"{node.proto}_{node.ip}_x.json").as_posix()
#-#            with open(filepath_tmp, 'w') as fo:
#-#                fo.write(jsonpickle.dumps(settings, indent=2))
#-#                trace(f'file saved. {filepath_tmp}')

            args = shlex.split(f'{v2ray_path} run')
            p = await asyncio.create_subprocess_exec(*args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
# #            p = await asyncio.create_subprocess_exec(*args, stdin=asyncio.subprocess.PIPE)
            try:
                p.stdin.write(json.dumps(settings).encode('utf8'))  # 配置内容通过STDIN传入
                if p.stdin.can_write_eof():
                    p.stdin.write_eof()
            except Exception as e:
                warn(f'error launching proxy: {e}')
        else:
            filepath = PurePath(conf_basepath, f"{node.proto}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
            debug(f'conf file saved. {filepath}')
            # launch new process
            args = shlex.split(f'{v2ray_path} run -config {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/dev/shm/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

        await asyncio.sleep(test_wait_seconds)
        return p, filepath


    async def _launch_hysteria(self, node: Node, measure_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if measure_mode:  # 评估模式下无密码, 不输出日志到文件
            settings['http']['listen'] = f'127.0.0.1:{port}'
            del settings['http']['user']
            del settings['http']['password']
            filepath = PurePath(conf_basepath, f"{node.proto}_{hash(node)}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
#            debug(f'conf file saved. {filepath}')

            args = shlex.split(f'{hysteria_path} client --no-check -c {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdin=None, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        else:
            os.system("kill `ps xf| grep -v grep | grep hysteria-linux-arm | awk '{print $1}'` > /dev/null 2>&1") # kill running one
            filepath = PurePath(conf_basepath, f"{node.proto}_{hash(node)}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
            debug(f'conf file saved. {filepath}')
            # launch new process
            args = shlex.split(f'{hysteria_path} client --no-check -c {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/dev/shm/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

        await asyncio.sleep(test_wait_seconds)
        return p, filepath

    async def _launch_hysteria2(self, node: Node, measure_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if measure_mode == True:  # 评估模式下无密码, 不输出日志到文件
            settings['http']['listen'] = f'127.0.0.1:{port}'
            del settings['http']['username']
            del settings['http']['password']
            del settings['http']['realm']
            filepath = PurePath(conf_basepath, f"{node.proto}_{hash(node)}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
# #            debug(f'conf file saved. {filepath}')

            args = shlex.split(f'{hysteria2_path} client --disable-update-check -c {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdin=None, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
# #            p = await asyncio.create_subprocess_exec(*args, stdin=None, stdout=None, stderr=asyncio.subprocess.STDOUT)  # debug only
        else:
            os.system("kill `ps xf| grep -v grep | grep hysteria2-linux-arm | awk '{print $1}'` > /dev/null 2>&1") # kill running one
            filepath = PurePath(conf_basepath, f"{node.proto}_{hash(node)}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
            debug(f'conf file saved. {filepath}')
            # launch new process
            args = shlex.split(f'{hysteria2_path} client --disable-update-check -c {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/dev/shm/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

        await asyncio.sleep(test_wait_seconds)
        return p, filepath


class ProxyTest(ProxySupportMix, AsyncContextDecorator, LaunchProxyMix):
    '''代理可用性测试
    '''

    def __init__(self, port_range=range(4000, 4098), nr_try=3, min_resp_count=1, interval=5, timeout=5, urls=None, unit='ms'):
        super().__init__()
        self.port_range = port_range  # 测试可用的端口范围
        self.port_range = list(self.port_range)
        self.nr_try = nr_try  # 每个代理测试次数
        self.nr_min_succ = min_resp_count  # 每个代理测试连通的阈值，达到阈值认为代理可用
        self.timeout = timeout # 连接超时
        self.o_limits = httpx.Limits(max_keepalive_connections=30, max_connections=None, keepalive_expiry=5)
        self.o_timeout = httpx.Timeout(connect=8.0, read=5.0, write=5.0, pool=2.0)
        self.interval = interval  # 代理每次测试之间的休眠时间
# #        self.urls = urls or ['https://www.google.com/', 'https://www.youtube.com/' ]  # 用于连通测试的目标站点，能访问到认为是连通
        self.urls = urls or ['https://www.youtube.com/', ]  # 用于连通测试的目标站点，能访问到认为是连通
        self.unit = unit  # 计量单位

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.clean()
        return False


    def _init_score(self):
        return 9999999 if self.unit == 'ms' else 0

    def _score(self, ms: int, length: int, best: int):
        if self.unit == 'ms':
            return min(best, ms)
        if self.unit == 'Bps':
            ms = float(ms or 1000)
            speed = int(length / ms * 1000)
            return max(speed, best)
        return best

    async def _popen_conn(self, node: Node, port: int, client: httpx.AsyncClient) -> tuple[int, int]:
        '''httpx实现
        '''
        score = self._init_score()
        nr_succ = 0

        p, config_path = await self.launch_proxy(node, True, port)
        url = choice(self.urls)
        try:
            for i in range(self.nr_try):
                try:
                    begin = time()
                    resp = await client.head(url)
                    latency = int((time() - begin) * 1000)
                    nr_succ += 1
# #                    if test_mode:
# #                        trace(f'{node} times: {i + 1} score:{latency}ms')
                    score = self._score(latency, 0, score)
                    if nr_succ >= self.nr_min_succ:  # 达到阈值提前退出
                        break
                except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                        break
                except (ssl.SSLError, ssl.SSLZeroReturnError, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError, httpx.ProxyError, anyio.EndOfStream) as e:
# #                    debug(f'{node} not available {e}')
                    break  # 提前退出
                except ConnectionAbortedError as e:
                    debug(f'{node} not available: ConnectionAbortedError {e}')
                    break  # 提前退出
                except ConnectionRefusedError as e:
                    debug(f'{node} not available: ConnectionRefusedError {e}')
                    break  # 提前退出
                except ConnectionResetError as e:
                    debug(f'{node} not available: ConnectionResetError {e}')
                    break  # 提前退出
                except asyncio.TimeoutError as e:
                    #debug(f'{node} timeout')
                    if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                        break
                except BaseException as e:
                    debug(f'{node} available test failed: {str(e)} {type(e)}')
                    if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                        break
                await asyncio.sleep(self.interval)
        finally:
            try:
                if p:
                    p.kill()
            except ProcessLookupError:
                pass
            try:
                await p.communicate()
            except ProcessLookupError:
                pass
            try:
                if os.path.exists(config_path):
# #                    if not PurePath(config_path).name.startswith('hysteria2'):
                    os.remove(config_path)
                    pass  # debug only
            except:
                pass

# #        debug(f'test {node} got {score=}, {nr_succ=}')
        return score, nr_succ


    async def _http_connect(self, node: Node, proxy_auth: aiohttp.BasicAuth|None = None) -> tuple[int, int]:
        score = self._init_score()
        nr_succ = 0
        url = choice(self.urls)

        # https://github.com/encode/httpx/discussions/2350  httpx.URL() does not parse url correctly with curly brackets in password
        p = httpx.Proxy(httpx.URL(f'http://{proxy_host}:{proxy_port}/', username=proxy_user, password=proxy_pass))

        client = httpx.AsyncClient(headers=headers, verify=False, timeout=self.timeout, proxies=p)
        for i in range(self.nr_try):
            try:
                begin = time()
                resp = await client.head(url)
                latency = int((time() - begin) * 1000)
                nr_succ += 1
                #debug(f'{node} times: {i + 1} score:{latency}ms')
                score = self._score(latency, 0, score)
                if nr_succ >= self.nr_min_succ:  # 达到阈值提前退出
                    break
            except Exception as e:
# #                debug(f'{node} {i+1}/{self.nr_try} test failed: {type(e)} {e}')
                print('W', end='', file=sys.stderr, flush=True)
                if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                    break
            await asyncio.sleep(self.interval)
        await client.aclose()
        return score, nr_succ


class NodeConfig(object):
    '''根据节点数据生成ProxyNode
    '''

    def __init__(self):
        super().__init__()
        self.genConfig = {'vmess': self.do_vmess,
                          'trojan': self.do_trojan,
                          'ss': self.do_ss,
                          'vless': self.do_vless,
                          'hysteria': self.do_hysteria,
                          'hysteria2': self.do_hysteria2,
                          }

    def doInboundSetting(self):
        setting = deepcopy(inboundsSetting)
        # http with auth
        setting[0]['port'] = proxy_port
        setting[0]['settings']['accounts'][0]['user'] = proxy_user
        setting[0]['settings']['accounts'][0]['pass'] = proxy_pass
        # http without auth
        setting[2]['port'] = proxy_port + 1
        return setting

    def do_vmess(self, node: Node) -> tuple[dict, dict]:
        assert node.proto == 'vmess'
        arg = node.param
        outboundsSetting = deepcopy(outboundsSetting_vmess)
        outboundsSetting[0]['settings']['vnext'][0]['address'] = arg['add'] if 'add' in arg else (node.ip if node.ip else node.real_ip)  #node.real_ip #arg['add']
        outboundsSetting[0]['settings']['vnext'][0]['port'] = int(arg['port'])
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['id'] = arg['id']
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['alterId'] = int((arg['aid'] or '0') if 'aid' in arg else 64)
        outboundsSetting[0]['streamSettings']['wsSettings']['path'] = arg['path']
        outboundsSetting[0]['streamSettings']['wsSettings']['headers'] = {} if not arg['host'] else {'Host': arg['host'], }
        outboundsSetting[0]['streamSettings']['security'] = arg.get('tls', 'none')
        setting = deepcopy(conf_tpl)
        setting['inbounds'] = self.doInboundSetting()
        setting['outbounds'] = outboundsSetting
        return setting

    def do_ss(self, node: Node) -> tuple[dict, dict]:
        assert node.proto == 'ss'
        outboundsSetting = deepcopy(outboundsSetting_ss)
        outboundsSetting[0]['settings']['servers'][0]['address'] = node.real_ip #node.ip
        outboundsSetting[0]['settings']['servers'][0]['method'] = node.param['method']
        outboundsSetting[0]['settings']['servers'][0]['password'] = node.param['password']
        outboundsSetting[0]['settings']['servers'][0]['port'] = node.port
        setting = deepcopy(conf_tpl)
        setting['inbounds'] = self.doInboundSetting()
        setting['outbounds'] = outboundsSetting
        return setting

    def do_vless(self, node: Node):
        assert node.proto == 'vless'
        arg = node.param
        outboundsSetting = deepcopy(outboundsSetting_vless)
        outboundsSetting[0]['settings']['vnext'][0]['address'] = node.ip  # node.real_ip #node.ip
        outboundsSetting[0]['settings']['vnext'][0]['port'] = node.port
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['id'] = node.uuid
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['alterId'] = 0
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['email'] = ''.join(sample(ascii_lowercase, 4))+'@'+''.join(sample(ascii_lowercase,2))+'.'+''.join(sample(ascii_lowercase,3))
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['encryption'] = arg.get('encryption', "none")
        outboundsSetting[0]['settings']['vnext'][0]['users'][0]['flow'] = arg.get('flow', '')

        network = arg.get('type', '')
        outboundsSetting[0]['streamSettings']['network'] = network
        security = arg.get('security', '')
        outboundsSetting[0]['streamSettings']['security'] = security

        match security:
            case 'tls':
                outboundsSetting[0]['streamSettings']['tlsSettings'] = {
                    'serverName': arg.get('sni', node.ip),
                        'allowInsecure': False,
# #                        'fingerprint': arg.get('fp', ''),
                        'show': False,
                    }
                if 'alpn' in arg:
                    outboundsSetting[0]['streamSettings']['tlsSettings']['alpn'] = unquote(arg['alpn']).split(',')
# #                    outboundsSetting[0]['streamSettings']['tlsSettings']['allowInsecure'] = False
# #                    outboundsSetting[0]['streamSettings']['tlsSettings']['show'] = False
            case 'reality':
# #                if 'reality-opts' in arg and arg['reality-opts']:
                # 参考 https://github.com/XTLS/Xray-examples/blob/main/VLESS-TCP-XTLS-Vision-REALITY/config_client.jsonc
                outboundsSetting[0]['streamSettings']['realitySettings'] = {
                    'fingerprint': arg.get('fingerprint', arg.get('fp', 'chrome')),
                    'serverName': arg.get('sni') or node.ip,
                    'show': False,
                    'publicKey': arg.get('public-key', arg.get('pbk', '')),
                    'shortId': arg.get('short-id', arg.get('sid', '')),
                    'spiderX': unquote(arg.get('spx', '')),
                    }
                if 'public-key' not in arg and 'pbk' not in arg:
                    warn(f'key \'public-key\'/\'pbk\' not found in {node}, {arg=} {node.source=}')
                if 'short-id' not in arg and 'sid' not in arg:
                    error(f'key \'short-id\'/\'sid\' not found in {node}, {arg=} {node.source=}')
            case '' | 'none' | 'None' | None:
                del outboundsSetting[0]['streamSettings']['security']
# #                warn(f'security is empty in vless, {node}, {node.param=}, {node.source=}')
            case _:
                warn(f'unknown {security=} in vless, {node}, {node.param=}, {node.source=}')

        match network:
            case 'tcp':
                pass
# #                warn(f'not implement for {network=}, {node}, {node.param=}, {node.source=}')
            case 'ws':
                outboundsSetting[0]['streamSettings']['tlsSettings'] = {
                    'serverName': arg.get('sni', node.ip),
                    }
                outboundsSetting[0]['streamSettings']['wsSettings'] = {
                    'path': arg['path'],
                    'headers': {
                        'Host': arg.get('host', ''),
                        }
                    }
            case 'grpc':
                outboundsSetting[0]['streamSettings']['grpcSettings'] = {
                    'serviceName': unquote(arg.get('serviceName', '')),
                    'multiMode': True if arg.get('mode') == 'multi' else False,
                    'idle_timeout': 60,
                    'health_check_timeout': 20,
                    'permit_without_stream': False,  # True,
                    'initial_windows_size': 0,  # 35536, 
                    }
            case '' | 'none' | 'None' | None:
                del outboundsSetting[0]['streamSettings']['network']
# #                warn(f'network is empty in vless, {node}, {node.param=}, {node.source=}')
            case _:
                warn(f'unknown {network=} in vless, {node}, {node.param=}, {node.source=}')

        setting = deepcopy(conf_tpl)
        setting['inbounds'] = self.doInboundSetting()
        setting['outbounds'] = outboundsSetting
        return setting


    def do_trojan(self, node: Node) -> tuple[dict, dict]:
        assert node.proto == 'trojan'
        outboundsSetting = deepcopy(outboundsSetting_trojan)
        outboundsSetting[0]['settings']['servers'][0]['address'] = node.real_ip #node.ip
        outboundsSetting[0]['settings']['servers'][0]['port'] = node.port
        outboundsSetting[0]['settings']['servers'][0]['password'] = node.param['password']
        if 'allowInsecure' in node.param:
            outboundsSetting[0]['streamSettings']['tlsSettings']['allowInsecure'] = True if node.param['allowInsecure'] else False
        setting = deepcopy(conf_tpl)
        setting['inbounds'] = self.doInboundSetting()
        setting['outbounds'] = outboundsSetting
        return setting


    def do_hysteria(self, node: Node) -> tuple[dict, dict]:
        assert node.proto == 'hysteria'
        arg = node.param
        settings = deepcopy(settingHysteria)
        if 'ports' in arg:
            settings['server'] = f'{arg["server"]}:{arg["ports"]}'
        else:
            settings['server'] = f'{arg["server"]}:{arg["port"]}'
        settings['server_name'] = arg['name']
        settings['alpn'] = arg['alpn']
        settings['auth_str'] = arg['auth']
        settings['insecure'] = arg.get('tls_insecure', True)
        settings['disable_mtu_discovery'] = arg['disable_mtu_discovery']
        settings['up_mbps'] = arg['bandwidth_up']
        settings['down_mbps'] = arg['bandwidth_down']
        settings['fast_open'] = arg['fastopen']
        settings['hop_interval'] = 120
        settings['obfs'] = arg['obfs']
        return settings

    def do_hysteria2(self, node: Node) -> tuple[dict, dict]:
        assert node.proto == 'hysteria2'
        arg = node.param
        settings = deepcopy(settingHysteria2)
        settings['server'] = f'{arg["server"]}:{arg["port"]}'
        settings['server_name'] = arg['name']
        settings['auth'] = arg['auth']
        settings['tls']['sni'] = arg.get('sni', '')
#        settings['tls']['insecure'] = arg['insecure']
        if 'obfs' in arg and arg['obfs'] != 'none':
            settings['obfs']['type'] = arg.get('obfs', 'salamander')
            if arg['obfs'] == 'salamander':
                settings['obfs']['salamander']['password'] = arg['obfs_password']
            else:
                error(f'unknown obfs type {arg["obfs"]}')
        else:
            del settings['obfs']

        return settings


class NodeProcessor(ProxySupportMix, LaunchProxyMix):
    '''节点处理类
    '''

    def __init__(self):
        super().__init__()


    def _my_before_sleep(self, log_text, max_retry, retry_state):
        debug(f'retrying in {retry_state.next_action.sleep:.1f}s {retry_state.attempt_number}/{max_retry}: {log_text}')


    async def _getNodeData(self, url: str) -> str|None:
        content = None
        max_retry = 5
        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(max_retry + 1), wait=wait_random(min=1, max=6), before_sleep=partial(self._my_before_sleep, url, max_retry)):
                with attempt:
                    if attempt.retry_state.attempt_number == max_retry + 1:
                        proxy_auth = aiohttp.BasicAuth(proxy_user, proxy_pass)
                        debug(f'getting {url} using proxy {attempt.retry_state.attempt_number}/{max_retry}...')
                        r = await self.client.get(url, timeout=10, proxy=proxies['http://'], proxy_auth=proxy_auth, ssl=False)
                    else:
                        r = await self.client.get(url, timeout=10, ssl=True)
                    async with r:
                        if r.status == 200:
                            content = await r.text()
                        elif r.status == 404:
                            debug(f'{r.status=} fetching {url=}')
                        elif r.status == 429:
                            raise TryAgain
                        else:
                            error(f'{r.status=} fetching {url=}')
        except RetryError:
            error(f'retry exceed, skip {url}')
        except Exception as e:
            mylogger.opt(exception=True).error(f'got error downloading {url}', diagnose=False, backtrace=False)
#            error(f'got {e} downloading {url}')

        return content


    @staticmethod
    def _parseProto(l_str: list[str], url: str) -> list[Node]:
        """通用的协议解析.
        由于来源格式不统一，有些不走这个函数
        """
        #pp = pprint.PrettyPrinter(indent=4)
        l_node = []
        for _node in l_str:
            #debug(f'{"=" * 30}\n{_node=}')
            m = urlparse(_node)
            _proto = m.scheme
            match _proto:
                case 'vmess':  # json(key: <id><add><path><port><host><aid><tls><ps>)
                    tmp = b64d(m.netloc + m.path, url)
                    if not tmp:
                        debug('vemss base64 parse failed {_node=} {url=}')
                        continue
                    try:
                        _param = json.loads(tmp)
                    except Exception as e:
                        warn(f'parse vmess, {e} {url=} {_node=}')
                    else:
                        if 'path' not in _param:
                            #warn(f'no path param ? {_param=} {m=}')
                            _param['path'] = '/'
                        if 'host' not in _param:
                            _param['host'] = ''
                        try:
                            l_node.append(Node(proto=_proto, param=_param, uuid=_param['id'], ip=_param['add'], port=int(_param['port']), alias=_param.get('ps', _param['add']), source=url))
                        except Exception as e:
                            warn(f'got error when add vmess node {e} {_param=} {url=}')
                case 'ssr':  # 不支持ssr
                    pass
                case 'tuic':  # 不支持tuic
                    pass
                case 'trojan': # <password>@<ip>:<port>?security=<>&sni=<>&type=<>&headerType=<>#<alias>
                    try:
                        _idx1 =m.netloc.rfind(':')
                        assert _idx1 != -1
                        _port = m.netloc[_idx1 + 1 :]
                        _idx2 = m.netloc.find('@')
                        assert _idx2 != -1
                        _tmp = m.netloc[:_idx2]
                        _ip = m.netloc[_idx2 + 1 : _idx1]
                        if _ip.find('[') != -1 and _ip.find(']') != -1:
                            _ip = _ip[1:-1]
                            debug(f'got ipv6 {_ip}, {_node} from {url=}')
                        _uuid = _tmp.decode() if type(_tmp) is bytes else _tmp
                        _extra = parse_qs(m.query) if m.query else {}
                        _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                        _extra['password'] = _uuid
                        _alias = unquote_plus(m.fragment)
                        #debug(f'{_proto=} {_uuid=} {_ip_port=} {_extra=} {_alias=}')
                        if type(_uuid) is bytes:
                            debug(f'trojan:{_node}')
                        l_node.append(Node(proto=_proto, uuid='', ip=_ip, port=int(_port), param=_extra, alias=_alias, source=url))
                    except Exception as e:
                        warn(f'got error when parse trojan node {e} {_node=} {url=}')
                case 'ss':  # base64(<method>:<password>)@<ip>:<port>#<alias>
                    _uuid = None
                    # 先判断是否整体为base64编码
                    _s = b64d(m.netloc.encode(), url, False)
                    if not _s:  # 非整体base64编码
                        _tmp, _ip_port = m.netloc.rsplit('@', 1)
                        try:
                            _ip, _port = _ip_port.rsplit(':', 1)
                            if _ip.find('[') != -1 and _ip.find(']') != -1:  # ipv6
                                _ip = _ip[1:-1]
                        except ValueError as e:
                            warn(f'skip one ss node cause got ValueError: {e} {_ip_port=} {_node=} {url=}')
                            continue
                        if _tmp.count('-') != 4:
                            _uuid = b64d(_tmp, url)
                            _uuid = _uuid.decode() if type(_uuid) is bytes else _uuid
                            if not _uuid:
# #                                debug(f'_uuid no need decode, {_node=} {url=}')
                                _uuid = _tmp.decode() if type(_tmp) is bytes else _tmp
                            elif type(_uuid) is bytes:
                                warn(f'skip one node cause Decode failed: {_uuid=} {_node=} {url=}')
                                continue
                        else:
                            _uuid = _tmp.decode() if type(_tmp) is bytes else _tmp

                        try:
                            _method, _password = _uuid.split(':', 1)
                            _extra = parse_qs(m.query) if m.query else {}
                            _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                            _extra['method'] = _method
                            _extra['password'] = _password
                            _alias = unquote_plus(m.fragment)
                            #debug(f'{_proto=} {_uuid=} {_ip_port=} {_extra=} {_alias=}')
                            #debug(f'ss:{_node}')
                            l_node.append(Node(proto=_proto, uuid='', ip=_ip, port=int(_port), param=_extra, alias=_alias, source=url))
                        except Exception as e:
                            debug(f'error parse {e}, {_node=}, {url=}')
                    else:  #  整体base64编码
                        try:
                            _method, _password, _ip, _port = re.split(':|@', _s, 3)
                            _param = {
                                    'method': _method,
                                    'password': _password,
                                    }
                            l_node.append(Node(proto=_proto, uuid='', ip=_ip, port=int(_port), param=_param, alias='', source=url))
#                            debug(f'add simple ss node {_s} {m}')
                        except Exception as e:
                            warn(f'error parse {e}, {_node=}, {url=}')

                case 'vless':  # <uuid>@<ip>:<port>?encryption=<>&security=<>&sni=<>&type=<>&host=<>&path=<>#<alias>
                    try:
                        _idx1 =m.netloc.rfind(':')
                        assert _idx1 != -1
                        _port = m.netloc[_idx1 + 1 :]
                        _idx2 = m.netloc.find('@')
                        assert _idx2 != -1
                        _uuid = m.netloc[:_idx2]
                        _ip = m.netloc[_idx2 + 1 : _idx1]
                        if _ip.find('[') != -1 and _ip.find(']') != -1:
                            _ip = _ip[1:-1]
# #                            debug(f'got ipv6 address {_ip=}: {_node}, {url=}')
                        _extra = parse_qs(m.query) if m.query else {}
                        _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                        _alias = unquote_plus(m.fragment)
                        if 'path' not in _extra:
                            _extra['path'] = '/'
                        if 'security' not in _extra:
                            _extra['security'] = None
                        if 'type' not in _extra:
                            _extra['type'] = 'tcp'
                            trace(f'parse vless, \'type\' fill to \'tcp\' in {_node=}, {url=}')
                        l_node.append(Node(proto=_proto, uuid=_uuid, ip=_ip, port=int(_port), param=_extra, alias=_alias, source=url))
                    except Exception as e:
                        warn(f'got error when add vless node {e} {_node=} {url=}')
                case 'hysteria':  # <ip>:<port>?auth=<>&insecure=<>&upmbps=<>&downmbps=<>&alph=<>&obfs=<>&protocol=<>&fastopen=<>#<name>
                    try:
                        _ip, _port = m.netloc.rsplit(':', 1)
                        _alias = unquote(m.fragment)
                        _extra = parse_qs(m.query) if m.query else {}
                        _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                        _param = {
                                'name': _alias,
                                'server': _ip,
                                'port': int(_port),
                                'tls_sni': _extra.get('sni', ''),
                                'tls_insecure': _extra['insecure'],
                                'alpn': _extra['alpn'],
                                'auth': _extra['auth'],
                                'protocol': _extra['protocol'],
                                'bandwidth_down': _extra['downmbps'],
                                'bandwidth_up': _extra['upmbps'],
                                'obfs': _extra.get('obfs', ''),
                                'fastopen': _extra.get('fastopen', False),
                                'disable_mtu_discovery': _extra.get('disable_mtu_discovery', True),
                                }
                        l_node.append(Node(proto=_proto, uuid=_param['auth'], ip=_param['server'], port=int(_param['port']), param=_param, alias=_param['name'], source=url))
                    except Exception as e:
                        warn(f'got error when add hysteria node: {e} {m=} {url=}')
                case 'hysteria2' | 'hy2':  # <auth>@<server>:<port>/?insecure=<>&sni=<>#<name>
                    try:
                        _auth, _server, _port = re.split(':|@', m.netloc, 2)  # TODO: 支持ipv6
                        _extra = parse_qs(m.query) if m.query else {}
                        _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                        _extra['insecure'] = True if ('insecure' not in _extra) or (_extra['insecure'] == 1 or _extra['insecure'] == True) else False
                        _extra['auth'] = _auth
                        _extra['server'] = _server
                        _extra['port'] = _port
                        _extra['name'] = m.fragment
                        if 'obfs' not in _extra:
                            _extra['obfs'] = _extra.get('obfs_type', 'salamander')
                        if 'obfs_password' not in _extra:
                            _extra['obfs_password'] = _extra['obfs-password'] if 'obfs-password' in _extra else ''
                        if 'sni' not in _extra and 'peer' in _extra:
                            _extra['sni'] = _extra['peer']
                        l_node.append(Node(proto='hysteria2', uuid=_auth, ip=_server, port=int(_port), param=_extra, alias=m.fragment, source=url))
                    except Exception as e:
                        warn(f'got error when add hysteria2 node: {e} {m=} {url=}')
                case '':
                    pass
                case _:
                    warn(f'unknown {_proto=} {_node=}, {url=}')

        return l_node


    async def _tmpDetectFreeNodeFileName(self) -> list[str]:  # TODO: 20240301不用了, 过段时间删
        """临时加上，用来尝试获取非固定的文件名
        """
        l_url = []
        today = datetime.today()
        yesterday = today + timedelta(days=-1)
        beforeyesterday = yesterday + timedelta(days=-1)
        for _day in [today, yesterday, beforeyesterday]:
            url = f'https://freenode.me/wp-content/uploads/{_day.year}/{_day.month:02d}/{_day.month:02d}{_day.day:02d}{{}}.txt'
            l_cor = [self.client.head(url.format(x if x else ''), timeout=3, ssl=False) for x in range(1)]
            #l_cor.append(self.client.head(f'https://freenode.me/wp-content/uploads/{_day.year}/{_day.month:02d}/{_day.month:02d}{_day.day:02d}.txt', timeout=3, ssl=False))
            l_rslt = await asyncio.gather(*l_cor, return_exceptions=True)
            for r in l_rslt:
                if isinstance(r, aiohttp.ClientResponse):
                    if r.status == 200:
                        debug(f'detected {r.url}')
                        l_url.append(str(r.url))

        #debug(f'detected freenode.me url: {l_url}')
        if not l_url:
            warn(f'no file detected !!!')
        return l_url

    async def _tmpDetectMiBeiFileName(self) -> list[str]:
        l_url = []
        today = datetime.today()
        url = 'https://www.mibei77.com/search/label/jiedian'
        if not (content := await self._getNodeData(url)):
            return l_url
        if m := re.search("<article class='blog-post hentry index-post post-0'>.+?<a href='([^']+)' .+?>.+?</article>", content, re.M|re.U|re.S):
            today_url = m.group(1)
            debug(f'{today_url=}')
            if content := await self._getNodeData(today_url):
                if m := re.search('http://mm\.mibei77\.com/\d{6}/.+?\.txt', content):
                    node_url = m.group()
                    l_url.append(node_url)
                    debug(f'detected {node_url}')
                else:
                    error(f'not detect for {url} {today_url}')
            else:
                warn(f'can\'t get content from {today_url}')
        else:
            error(f'latest post not found for {url}')

        return l_url

    async def _tmp_freevpnx(self, q_out):
        url = 'https://url.cr/api/user.ashx?do=freevpn&ip=127.0.0.1&uuid=67ee96e3-70c5-4741-9105-60d7fd8c42b3'
        l_node = []
        if content := await self._getNodeData(url):
            content = re.sub('(\r\n){2,}', '\n', content)
            l_tmp = content.split('\n')
            debug(f'got {len(l_tmp)} record(s) from {url}')
            l_node = self.__class__._parseProto(l_tmp, url)
            for _node in l_node:
                await q_out.put(_node)

    async def _tmp_ssfree(self, q_out):
        url = 'https://view.ssfree.ru/'
        l_node = []
        if not (content := await self._getNodeData(url)):
            warn(f'no node data found from {url}')
            return l_node
        if m := re.search('data-clipboard-text="(.+?)"', content):
            data = m.group(1)
            if data.startswith('vmess://'):  # 更正地址
                try:
                    _tmp = json.loads(b64decode(data[8:]))
                    if _tmp['add'] !=  'aop.ssfree.ru':
                        _tmp['add'] = 'aop.ssfree.ru'
                        #debug(f'add changed to {_tmp["add"]}')
                        data = data[:8] + b64encode(json.dumps(_tmp).encode()).decode()
                except Exception as e:
                    warn(f'got excepton when process data: {e}')
            l_tmp = [data, ]
            debug(f'got {len(l_tmp)} record(s) from {url}')
            l_node = self.__class__._parseProto(l_tmp, url)
            for _node in l_node:
                await q_out.put(_node)
        else:
            warn(f'no node data found from {url}')

    async def _tmp_tolinkshare(self, q_out):
        l_node = []
        url = 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/tolinkshare/freenode/main/README.md'
        if content := await self._getNodeData(url):
            l = re.findall('```(.+?)```', content, re.U|re.M|re.S)
            if l:
                l_tmp = list(filter(None, chain.from_iterable((x.split('\n') for x in l))))  # filter用于过滤空行
                debug(f'got {len(l_tmp)} record(s) from {url}')
                l_node = self.__class__._parseProto(l_tmp, url)
                for _node in l_node:
                    await q_out.put(_node)

    async def _tmp_vpnnet(self, q_out):
        l_node = []
        url = 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/VpnNetwork01/vpn-net/main/README.md'
        if content := await self._getNodeData(url):
            if l := re.findall('```(.+?)```', content, re.U|re.M|re.S):
                l_tmp = list(filter(None, chain.from_iterable((x.split('\n') for x in l))))  # filter用于过滤空行
                debug(f'got {len(l_tmp)} record(s) from {url}')
                l_node = self.__class__._parseProto(l_tmp, url)
                for _node in l_node:
                    await q_out.put(_node)

    async def _parseNodeData(self, name: str, url: str, data: str=None) -> list[Node]:
        if url:
            #debug(f'getting {url}')
            if not (r := await self._getNodeData(url)):
                warn(f'{name} no node data got from {url}')
                return []
        elif data:
            r = data
        else:
            warn('{name} url and data both empty !')
            return []

        # 特殊处理
        if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/yudou66.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/blues.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/halekj.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/master/sub/proxies.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vmess.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Japan/config.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/United%20States/config.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Germany/config.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Singapore/config.txt' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Austria/config.txt':
            r = b64encode(r.encode())

        # 特殊处理
        if url == 'https://mareep.netlify.app/sub/merged_proxies_new.yaml':
            full_content = yaml.load(r, yaml.FullLoader)
            proxies = full_content.get('proxies')
            l_node = []
            for _x in proxies:
                _proto = _x['type']
                match _proto:
                    case 'tuic':  # 20231115 略过tuic协议
                        continue
                    case 'hysteria':
                        _param = {
                                'name': _x['name'],
                                'server': _x['server'],
                                'port': _x['port'],
                                'tls_sni': _x.get('sni', ''),
                                'tls_insecure': _x['skip-cert-verify'],
                                'alpn': _x['alpn'][0],
                                'auth': _x['auth_str'] if 'auth_str' in _x else _x['auth-str'],
                                'protocol': _x.get('protocol', 'udp'),
                                'bandwidth_up': _x['up'],
                                'bandwidth_down': _x['down'],

#                                'pinSHA256': _x.get('sha265', None),
                                #'obfs_type': _x.get('obfs_type', 'salamander'),
#                                    'obfs_salamander_password': b64decode(_x.get('obfs', '')).decode(),
                                #'obfs_salamander_password': _x.get('obfs', ''),
                                'obfs': _x.get('obfs', ''),
                                'fastopen': _x.get('fast-open', False),
                                'disable_mtu_discovery': _x.get('disable_mtu_discovery', True),
                                }
                        l_node.append(Node(proto=_proto, uuid=_param['auth'], ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                    case 'hysteria2':
                        _param = {
                                'server': _x['server'],
                                'name': _x['name'],
                                'port': _x['port'],
                                'auth': _x['password'],
                                'fastopen': _x.get('fast-open', True),
                                'sni': _x.get('sni', ''),
                                'tls_insecure': _x['skip-cert-verify'],
                                }
                        l_node.append(Node(proto=_proto, uuid=_param['auth'], ip=_param['server'], port=int(_param['port']), param=_param, alias=_param['name'], source=url))
                    case 'vmess' | 'vless':
                        try:
                            _param = {
                                    'host': _x['server'],
                                    'id': _x.get('uuid', ''),
                                    'port': _x['port'],
                                    'aid': _x.get('alterId', 0),
                                    'tls': _x.get('tls', None),
        # #                            'path': _x['ws-opts']['path'] if 'ws-opts' in _x and 'path' in _x['ws-opts'] else '/',
                                    'path': _x.get('ws-opts', {}).get('path', '/'),
                                    'host': _x.get('ws-opts', {}).get('headers', {}).get('host', {})
                            }
                            if _x['type'] == 'vless':
                                _param['security'] = _x['tls']
                                _param['type'] = _x['network']
                                del _x['type']
                            _param = {**_param, **_x}
                            l_node.append(Node(proto=_proto, uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                        except Exception as e:
                            warn(f'{name} decode failed for {url} {e=} {_x=}')
                    case _:
                        debug(f'{name} 未处理的协议 {_x["type"]}')
            debug(f'{name} got {len(l_node)} record(s) from {url}')
            return l_node
                

        # 特殊处理
        if url.startswith('https://mirror.ghproxy.com/https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/sub/'):
# #            debug(f'特殊处理w1770946466')
            l_new = []
            for _line in r.split('\n'):
                if _line.startswith('vmess://'):
                    if _tmp := b64d(_line[8:], url):
                        try:
                            json.loads(_tmp)
                            _newline = _line
                        except Exception as e:  # 只对vmess中base64解码后不是json格式的内容进行修正
#                            debug(f'json.loads got {e} {_tmp=}')
                            try:
                                _up = urlparse(_line)
                                if _tmp := b64d(_up.netloc, url):
                                    _tls, _uuid, _server, _port = re.split(':|@', _tmp, 3)
                                    _extra = parse_qs(_up.query) if _up.query else {}
                                    _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                                    _j = {
                                            'add': _server,
                                            'port': _port,
                                            'id': _uuid,
                                            'aid': _extra.get('alterId', 0),
                                            'path': _extra.get('path', '/'),
                                            'host': _extra.get('obfsParam', ''),
                                            'tls': _tls,
    #                                        'obfs': _extra['obfs'],
                                            }
                                    _newline = 'vmess://' + b64encode(json.dumps(_j).encode()).decode()
                            except Exception as e:
                                warn(f'{name} parse failed {e}, {_line=}, {url=}')
                                continue
                    else:
                        continue
                elif _line.startswith('ss://'):
                    # base64(<method>:<password>)@<ip>:<port>#<alias>
                    _up = urlparse(_line)
                    try:
                        _tmp = b64decode(_up.netloc).decode()
                        # 顺利解码，说明整体是base64编码的，需要修改
                        _methodpassword, _ipport = _tmp.split('@', 1)
                        _newline = b64encode(_methodpassword.encode()).decode() + '@' + _ipport
                    except:  # 报异常认为是正常格式无需修改
                        _newline = _line
                else:
                    _newline = _line
                l_new.append(_newline)
            r = b64encode('\n'.join(l_new).encode()).decode()

        # 特殊处理
        if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/clash/clash_v2ray.yml' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/clash/clash_trojan.yml' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/freenodes/freenodes/main/clash.yaml' or \
           url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml' or \
           url == 'https://anaer.github.io/Sub/clash.yaml':
            full_content = yaml.load(r, yaml.FullLoader)
            proxies = full_content.get('proxies')
            l_node = []
            for _x in proxies:
                if _x['type'] == 'ssr':
                    continue
                try:
                    _param = {
                            'host': _x['server'],
                            'id': _x.get('uuid', ''),
                            'port': _x['port'],
                            'aid': _x.get('alterId', 0),
                            'tls': _x.get('tls', None),
# #                            'path': _x['ws-opts']['path'] if 'ws-opts' in _x and 'path' in _x['ws-opts'] else '/',
                            'path': _x.get('ws-opts', {}).get('path', '/'),
                            'host': _x.get('ws-opts', {}).get('headers', {}).get('host', {})
                    }
                    if _x['type'] == 'ss':
                        _param['method'] = _x['cipher']
                    if _x['type'] == 'vless':
                        _param['security'] = _x['tls']
                    if _x['type'] == 'trojan':
                        _param['allowInsecure'] = _x.get('skip-cert-verify', True)
                    _param = {**_param, **_x}
                    l_node.append(Node(proto=_x['type'], uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                except Exception as e:
                    warn(f'{name} decode failed for {url} {e=} {_x=}')
                    continue
            debug(f'{name} got {len(l_node)} record(s) from {url}')
            return l_node


        if not (s := b64d(r, url)):
            error(f'{name} decode failed for r[:100]={r[:100]}, {url=}')
            return []
        ls = s.split('\n')

        try:
            l_tmp = (x for x in ls if x)

            # 特殊处理
            if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free':
# #                debug(f'特殊处理 {url=}')
                _l_n = []
                for _x in l_tmp:
                     try:
                        _up = urlparse(_x)
                        if _up.scheme == 'ss':
                            _l = b64decode(_up.netloc).decode()
                            _p1, _p2 = _l.split('@', 1)
                            _new = urlunparse((_up.scheme, b64encode(_p1.encode()).decode() + '@' + _p2, _up.path, _up.params,  _up.query, _up.fragment))
                        else:
                            _new = _x
                        _l_n.append(_new)
                     except Exception as e:
                        error(f'{name} skip node from {url} {e=} {_x=}')
                        continue
                l_tmp = _l_n

            # 特殊处理
            if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/ss':
                l_new = []
#                debug(f'try to process special format node, {url=}')
                for _x in l_tmp:
                    try:
                        _idx = _x.find('#')
                        _t = b64decode(_x[5:_idx]).decode()
                        _p1, _p2 = _t.split('@', 1)
                        x = _x[:5] + b64encode(_p1.encode()).decode() + '@' + _p2 + _x[_idx :]
                    except Exception as e:
                         warn(f'{name} got {e} processing ss node in {url}')
                         continue
                    l_new.append(x)
                l_tmp = l_new
                #debug(f'now {l_tmp=}')

            # 特殊处理
            if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/eycorsican/rule-sets/master/kitsunebi_sub':
                l_new = []
#                debug(f'try to process special format node, {url=}')
                for _x in l_tmp:
                    if _x.startswith('vmess://'):
                        _idx = _x.find('?')
                        try:
                            _t = b64decode(_x[8:_idx]).decode()
                            _tls, _uuid, _server, _port = re.split(':|@', _t, 3)
                            _up = urlparse(_x)  # ?network=tcp&aid=0&tls=0&allowInsecure=1&mux=0&muxConcurrency=8&remark=TCP%20Test%20Outbound'
                            _qs = parse_qs(_up.query)
                            _d = {'id': _uuid,
                                  'add': _server,
                                  'port': _port,
                                  'path': _qs.get('path', ['/', ])[0],
                                  'aid': _qs.get('aid', [0, ])[0],
                                  'ps': _qs.get('remark', ['', ])[0],
                                  'tls': _tls,
                                  }
                            _x = _x[:8] + b64encode(json.dumps(_d).encode()).decode()
                        except Exception as e:
                            warn(f'{name} parse vmess data from {url=} got {e}')
                            continue
                    l_new.append(_x)
                l_tmp = l_new


            # 特殊处理
            if url == 'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg':
                l_new = []
                debug(f'{name} try to process special format node, {url=}')
                for _x in l_tmp:
                    if _x.startswith('vless://'):
                        _idx = _x.find('?')
                        try:
                            _t = b64decode(_x[8:_idx]).decode()
                            _p1, _p2 = _t.split(':', 1)
                        except Exception as e:
                            continue
                        else:
                            _x = _x[:8] + _p2 + _x[_idx :]
                    elif _x.startswith('vmess://'):
                        _idx = _x.find('?')
                        try:
                            _t = b64d(_x[8:_idx], url, False)
                            assert _t
                            _tls, _uuid, _server, _port = re.split(':|@', _t, 3)
                            _up = urlparse(_x)
                            _qs = parse_qs(_up.query)
                            _d = {'id': _uuid,
                                  'add': _server,
                                  'host': _qs.get('obfsParam', [_server, ])[0],
                                  'port': _port,
                                  'path': _qs.get('path', ['/', ])[0],
                                  'aid': _qs.get('alterId', [0, ])[0],
                                  'ps': _qs.get('remarks', ['', ])[0],
                                  'tls': _tls,
                                  }
                            _x = _x[:8] + b64encode(json.dumps(_d).encode()).decode()
                        except Exception as e:
                            warn(f'{name} parse vmess got {e}, {url=} {_x[8:_idx]}')
                            continue
                    l_new.append(_x)
                l_tmp = l_new

        except binascii.Error:
            if r.startswith('https://api.tsutsu.one/sub'):  # TODO: 可能无用，可以删除
                debug(f'try to parse as param of \'url\'')  # https://api.tsutsu.one/sub?target=mixed&url=xxxxxx
                up = urlparse(r)
                debug(f'{r=} {url=} {data=}')
                qs = parse_qs(up.query)
                l_url = qs['url'][0]
                l_tmp = l_url.split('|') or []
            else:  # 尝试加=解码
                l_tmp = (x for x in b64d(r, url, False).split('\n') if x) if r else []
        except BaseException as e:
            error(f'{name} got error {e=}')
            raise e
        if not isinstance(l_tmp, list):
            l_tmp = list(l_tmp)

        if url:
            debug(f'{name} got {len(l_tmp)} record(s) from {url}')
        else:
            debug(f'{name} got {len(l_tmp)} record(s) from data')
        return self.__class__._parseProto(l_tmp, url)


    async def _getNodeUrl(self) -> list[str]:
        # get node list from file or internet
        today = datetime.today()
        yesterday = today + timedelta(days=-1)
        beforeyesterday = yesterday + timedelta(days=-1)
# #        l_freenode_url = await self._tmpDetectFreeNodeFileName()
        l_mibei_url = await self._tmpDetectMiBeiFileName()
        #l_url = []  # debug only
        l_source = [  # *l_freenode_url,
            f'https://freenode.me/wp-content/uploads/{today.year}/{today.month:02d}/{today.month:02d}{today.day:02d}.txt',
            f'https://freenode.me/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.month:02d}{yesterday.day:02d}.txt',
            *l_mibei_url,
            f'https://clashnode.com/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',
            f'https://clashnode.com/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
#            f'https://clashnode.com/wp-content/uploads/{beforeyesterday.year}/{beforeyesterday.month:02d}/{beforeyesterday.strftime("%Y%m%d")}.txt',

            f'https://nodefree.org/dy/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',
            f'https://nodefree.org/dy/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://clashgithub.com/wp-content/uploads/rss/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://clashgithub.com/wp-content/uploads/rss/{today.strftime("%Y%m%d")}.txt',
#            f'https://nodefree.org/dy/{beforeyesterday.year}/{beforeyesterday.month:02d}/{beforeyesterday.strftime("%Y%m%d")}.txt',

            f'https://node.oneclash.cc/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://node.oneclash.cc/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',

            f'https://freeclash.org/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%m%d")}.txt',
            f'https://freeclash.org/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%m%d")}.txt',

            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/umelabs/node.umelabs.dev/master/Subscribe/v2ray.md',

            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/freefq/free/master/v2',
            #'https://mirror.ghproxy.com/https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt', 
# #            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt', 
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ts-sf/fly/main/v2',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ts-sf/fly/main/v2',
            ##'https://raw.fgit.ml/ts-sf/fly/main/v2', 
            'https://cdn.jsdelivr.net/gh/ermaozi01/free_clash_vpn/subscribe/v2ray.txt',
# #            'https://tt.vg/freev2',
            'https://v2ray.neocities.org/v2ray.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/v2',
            #'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/ss',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/tr',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt',
            #'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Lewis-1217/FreeNodes/main/bpjzx1',
            #'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Lewis-1217/FreeNodes/main/bpjzx2',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub',

            #'https://gh-proxy.com//raw.fastgit.org/yaney01/Yaney01/main/yaney_01',
            #'https://mirror.ghproxy.com/https://raw.githubusercontent.com/sun9426/sun9426.github.io/main/subscribe/v2ray.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/clash/clash_v2ray.yml',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/clash/clash_trojan.yml',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ZywChannel/free/main/sub',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/free18/v2ray/main/v2ray.txt',
            #'https://sub.nicevpn.top/Clash.yaml',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray',

           f'https://node.onenode.cc/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
           f'https://node.onenode.cc/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',

            'https://anaer.github.io/Sub/clash.yaml',

            # https://github.com/Helpsoftware/fanqiang
            'https://jiang.netlify.com/',
            'https://youlianboshi.netlify.app/',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/eycorsican/rule-sets/master/kitsunebi_sub',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/umelabs/node.umelabs.dev/master/Subscribe/v2ray.md',

            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription_num',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
            f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/sub/{beforeyesterday.strftime("%y%m")}/{beforeyesterday.strftime("%y%m%d")}.txt',
            f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/sub/{yesterday.strftime("%y%m")}/{yesterday.strftime("%y%m%d")}.txt',
            f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/sub/{today.strftime("%y%m")}/{today.strftime("%y%m%d")}.txt',
            'https://mareep.netlify.app/sub/merged_proxies_new.yaml',  # https://github.com/vveg26/chromego_merge
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt',  # https://github.com/Flik6/getNode

            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/freenodes/freenodes/main/clash.yaml',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/yudou66.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/blues.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/halekj.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/mheidari98/.proxy/main/all',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/yebekhe/V2Hub/main/merged_base64',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Mahdi0024/ProxyCollector/master/sub/proxies.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vmess.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/ss.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt',

            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Japan/config.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/United%20States/config.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Germany/config.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Singapore/config.txt',
            'https://mirror.ghproxy.com/https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/main/sub/Austria/config.txt',
        ]
        #l_source = ['https://mirror.ghproxy.com/https://raw.githubusercontent.com/sun9426/sun9426.github.io/main/subscribe/v2ray.txt', ]
        #l_source = l_source[:5]+ l_source[-5:]  # debug only

        return l_source

    async def url2node(self, name: str, e_exit: asyncio.Event, q_in: asyncio.Queue, q_out: asyncio.Queue):
        nr = 0
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init {q_in.qsize()} url')
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
# #                info(f'{name} got event_exit, break')
                break
            url = t_q.result()
# #            debug(f'{name} get task {url=}')
            nr += 1
            q_in.task_done()
            l_node = await self._parseNodeData(name, url)
            for _node in l_node:
                await q_out.put(_node)

# #        info(f'{name} exit. processed {nr}')
        return nr

    async def uniq_nodes(self, name: str, e_exit: asyncio.Event, q_in: asyncio.Queue, q_out: asyncio.Queue):
        st_node = set()
        nr = 0
        last  = time()
# #        debug(f'{name} init {q_in.qsize()} node(s)')
        t_exit = asyncio.create_task(e_exit.wait())
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
# #                info(f'{name} got event_exit, break')
                break
            node = t_q.result()
            q_in.task_done()
            if node is None:
                if (duration:= time() - last) >= 24 * 3600:
                    st_node.clear()
                    debug(f'{name} set cleared, {duration=}.')
                    last = time()
                else:
                    debug(f'{name} set not cleared, {duration=}.')
                continue
            nr += 1

            h = hash(node)
            if h not in st_node:
                st_node.add(h)
                await q_out.put(node)

# #        info(f'{name} exit. {len(st_node)}/{nr}')
        return len(st_node), nr

    async def host2ip(self, name: str, e_exit: asyncio.Event, q_in: asyncio.Queue, q_out: asyncio.Queue):
        """使用dnspython异步获取域名对应的ip地址
        `read_ip` 为空 表示`ip`字段是域名，无法解析成ip
                  ==`ip` 表示`ip`字段本身就是ip地址
                  !=`ip` 表示`ip`字段是域名，可以解析成ip
        """
        rs = Resolver()
        rs.nameservers = ['8.8.8.8', '8.8.4.4']
        nr, nr_filter = 0, 0
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init {q_in.qsize()} node(s)')
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
# #                info(f'{name} got event_exit, break')
                break
            node = t_q.result()
            nr += 1
            q_in.task_done()

            try:
                ipaddress.IPv4Address(node.ip)
            except:
                try:
                    ipaddress.IPv6Address(node.ip)
                except:
                    # 是host
                    try:
                        rslt = await rs.resolve_name(node.ip, socket.AF_INET, lifetime=5)  # dns查询
                    except Exception as e:
                        pass
    # #                    debug(f'{name} got error {e}')
                    else:
                        node.real_ip = next(rslt.addresses())
                else:  # 是有效v6 ip
                    node.v4 = False
                    node.real_ip = node.ip
            else:  # 是有效v4 ip
                node.real_ip = node.ip
            if node.real_ip:
                await q_out.put(node)
            else:
                nr_filter += 1

# #        info(f'{name} exit. {nr} processed, {nr_filter} filtered.')
        return nr, nr_filter

    async def ip2area(self, name: str, e_exit: asyncio.Event, q_in: asyncio.Queue, q_out: asyncio.Queue):
        nr, nr_filter = 0, 0
        f = Ip2Area(qqwry_path)
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init {q_in.qsize()} node(s)')
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
# #                info(f'{name} got event_exit, break')
                break
            node = t_q.result()
            nr += 1
            q_in.task_done()

            if node.real_ip:
                if not node.v4:
                    await q_out.put(node)
                else:
                    r, a = f.isPreferredArea(node.real_ip)
                    if r:
                        node.area = a
                        await q_out.put(node)
                    else:
                        nr_filter += 1
            else:
                nr_filter += 1

        f.clear()
# #        info(f'{name} exit. {nr} processed, {nr_filter} filtered.')
        return nr, nr_filter

    async def filter_bad_ip(self, name: str, e_exit: asyncio.Event, q_in: asyncio.Queue, q_out: asyncio.PriorityQueue):
        """简单过滤地址
        用real_ip字段，用socket尝试连接，能连接上的才保留, 用select提速

        `batch` 用来指定一次在select上注册的文件对象数量，设得大会遇到打开太多文件的错误，系统默认1024，可考虑改大点比如 `ulimit -Hn 4096` `ulimit -Sn 4096`
        """
        nr, nr_filter = 0, 0
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init {q_in.qsize()} node(s)')
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
# #                info(f'{name} got event_exit, break')
                break
            node = t_q.result()
            nr += 1
            q_in.task_done()

            if not 65535 >= int(node.port) >= 0:
                nr_filter += 1
                continue

            x = time()
            try:
                _, wrt = await asyncio.wait_for(asyncio.open_connection(node.real_ip, int(node.port), limit=512), 5.0)
            except Exception:
                nr_filter += 1
            else:
                await q_out.put((time()-x, node))
                wrt.close()
                await wrt.wait_closed()

# #        info(f'{name} exit. {nr} processed, {nr_filter} filtered.')
        return nr, nr_filter

    async def measure_node(self, name: str, port: int, e_exit: asyncio.Event, q_in: asyncio.PriorityQueue, q_out: asyncio.PriorityQueue, e_increase: asyncio.Event):
        at = ProxyTest(port_range=port_range, nr_try=2, min_resp_count=2, interval=3, timeout=5)
        client = httpx.AsyncClient(headers=headers, verify=False, timeout=at.o_timeout, limits=at.o_limits, proxies=f'http://127.0.0.1:{port}')
        nr, nr_filter = 0, 0
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init use {port=}, {q_in.qsize()} node(s)')
        try:
            while 1:
                t_q = asyncio.create_task(q_in.get())
                done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
                if t_exit in done:
    # #                info(f'{name} got event_exit, break')
                    break
                _, node = t_q.result()
                nr += 1
                q_in.task_done()

                ping, nr_succ = await at._popen_conn(node, port, client)
                if ping >= 9999999 or nr_succ < at.nr_min_succ:
                    ping = None
                if ping:
                    if ping < 1000:  # 过滤慢速节点
                        info(f'{name} conn succ <green>{ping}{at.unit}</green> {node.area} {node} {node.alias}')
                        node.score = ping
                        node.score_unit = at.unit
                        await q_out.put((node.score, node))
                        e_increase.set()
                    else:
                        debug(f'{name} conn succ <yellow>{ping}{at.unit}</yellow> {node.area} {node} {node.alias}')
                        nr_filter += 1
# #                    debug(f'{name} now {q_out.qsize()} candidate.')
                else:
                    pass
#-#                    if test_mode:
                    trace(f'{name} bad {node.area} {node}')
                    nr_filter += 1
        finally:
            await at.clean()
            await client.aclose()
# #        info(f'{name} exit. {nr} processed, {nr_filter} filtered.')
        return nr, nr_filter


    async def launch(self, name: str, e_exit: asyncio.Event, q_in: asyncio.PriorityQueue, test_mode: bool, e_decrease: asyncio.Event):
        nr = 0
        t_exit = asyncio.create_task(e_exit.wait())
# #        debug(f'{name} init,  {q_in.qsize()} node(s)')
        proxy_auth = aiohttp.BasicAuth(proxy_user, proxy_pass)
        while 1:
            t_q = asyncio.create_task(q_in.get())
            done, _ = await asyncio.wait({t_exit, t_q}, return_when=asyncio.FIRST_COMPLETED)
            if t_exit in done:
                info(f'{name} got event_exit, break')
                break
            score, node = t_q.result()
            nr += 1
            e_decrease.set()
            q_in.task_done()
            info(f'{name} pick {score} {node.area} {node}, {q_in.qsize()} remain')

            if sys.platform != 'win32' and not test_mode:
                p, filepath = await self.launch_proxy(node)
 8845               succ(f'{name} service {node.area} {score}{node.score_unit} {node} started, pid={p.pid}')
                at = ProxyTest(nr_try=2, min_resp_count=1, interval=5, timeout=5)
                while 1:
                    #debug(f'{name} check node avaliable ...')
                    ping, nr_succ = await at._http_connect(node, proxy_auth=proxy_auth)
                    #debug(f'{name} check avaliable got {ping=} {nr_succ=}')
                    if ping >= 9999999 or nr_succ < at.nr_min_succ:
                        info(f'{name} node invaliable, picking new one')
                        break
                    else:
                        #info(f'{name} wait for next check ...')
                        print(f'[{datetime.now().strftime("%H:%M:%S")}_{ping}]', end='', file=sys.stderr, flush=True)

                        l_task = [asyncio.create_task(event_exit.wait()), asyncio.create_task(p.wait()), asyncio.create_task(asyncio.sleep(120))]
                        t_exit, t_process_exit, t_timeout = l_task
                        done, _ = await asyncio.wait(l_task, return_when=asyncio.FIRST_COMPLETED)
                        if t_timeout in done:
                            continue
                        elif t_exit in done:
                            info(f'{name} got exit flag, exit')
                            break
                        elif t_process_exit in done:
                            warn(f'{name} proxy killed? to pick new one...')
                            break
                try:
                    p.kill()
                except ProcessLookupError:
                    pass
                try:
                    await p.communicate()
                except ProcessLookupError:
                    pass
# #                debug(f'{name} remove conf {filepath}')
                try:
# #                    pass
                    os.remove(filepath)
                except:
                    pass
                await at.clean()
            elif test_mode:
                warn(f'{name} in test mode, {q_in.qsize()} candidate')
                try:
                    await asyncio.wait_for(event_exit.wait(), 300)
                except asyncio.exceptions.TimeoutError:
                    trace(f'{name} wake up')
                else:
# #                    info(f'{name} got exit flag, exit')
                    break
            else:
                warn(f'{name} win32 not support, no test')
                try:
                    await asyncio.wait_for(event_exit.wait(), 300)
                except asyncio.exceptions.TimeoutError:
                    pass
                    debug(f'{name} wake up')
                else:
                    info(f'{name} got exit flag, exit')
                    break

# #        info(f'{name} exit. {nr} processed, {q_in.qsize()} remain.')
        return nr, q_in.qsize()


    async def dispatch(self, name: str, e_exit: asyncio.Event, q_url, q_node, q_uniq_node, q_ip_node, q_area_node, q_conn_node, q_tested_node, e_increase, e_decrease, test_mode: bool):
        t_exit = asyncio.create_task(event_exit.wait())
        nr, nr_remain = 0, 0
        time_add = None
# #        debug(f'{name} init.')
        while 1:
            recent_put = False
            nr_remain = q_tested_node.qsize()
            if nr_remain <= 1 and (time_add is None or time() - time_add >=90):
                if all((q.qsize() == 0 for q in (q_url, q_node, q_uniq_node, q_ip_node, q_area_node, q_conn_node))):
                    info(f'{name} few candidate({nr_remain}), get more...')
                    nr += 1
                    await q_node.put(None)  # 告诉排重清除历史数据
                    if test_mode:
                        l_source = [
                                    'https://mirror.ghproxy.com/https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes',
                                    ]
                        l_source = []
                        l_s = [
# #                                'vless://308bab94-18e4-43f5-9c35-a89d95af2f25@104.18.202.209:443?mode=gun&security=tls&encryption=none&alpn=h2,http/1.1&fp=firefox&type=grpc&serviceName=Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android,Telegram:@Archive_Android&serviceName=%40s%70ik%65%76%70%6e&sni=dl.spikevpn.cfd#[🇨🇦]t.me/ConfigsHu',
# #                                'vless://5d0245cd-8412-4a32-b52c-ef810651e650@190.93.247.155:443?mode=gun&security=tls&encryption=none&alpn=h2,http/1.1&fp=chrome&type=grpc&serviceName=@Digiv2ray,@Digiv2ray,@Digiv2ray,@Digiv2ray,&sni=digi--v2raycncfs.RadioTeHran.oRG.#%40V2ray1_Ng+ALL',
# #                                'vless://a99dc06c-bf43-4264-9b2b-615a4f69f30f@MTN.Vpn-Mikey.cfd:443?mode=gun&security=tls&encryption=none&alpn=h2,http/1.1&fp=chrome&type=grpc&serviceName=@Vpn_Mikey،@Vpn_Mikey&sni=Germany.Vpn-Mikey.cfd#[🇨🇦]t.me/ConfigsHu',
                                'vless://717ef3fe-1213-4e09-ac4a-5ea693b49368@gpc.netflix.net:2083?type=grpc&mode=gun&serviceName=@vmesskhodam,@vmesskhodam,@vmesskhodam,@vmesskhodam,@vmesskhodam&security=tls&sni=a.lars1.nl#[🇨🇦]t.me/ConfigsHu',
# #                                'vless://0cfa9e5a-b641-4c5a-b090-df50c8025358@is.snappfoodd.top:2083?type=grpc&mode=gun&serviceName=@vmesskhodam,@vmesskhodam,@vmesskhodam,@vmesskhodam,@vmesskhodam&security=tls&sni=a.lars1.nl#[🇨🇷]t.me/ConfigsHu',
                               ]
                        if l_s:
                            l_node = self.__class__._parseProto(l_s, 'test')
                            for _node in l_node:
                                debug(f'in test_mode, put _node {_node}')
                                await q_node.put(_node)
                    else:
                        l_source = await self._getNodeUrl()
                        shuffle(l_source)
                        freevpnx = asyncio.create_task(self._tmp_freevpnx(q_node))
                        ssfree = asyncio.create_task(self._tmp_ssfree(q_node))
                        tolinkshare = asyncio.create_task(self._tmp_tolinkshare(q_node))
                        vpnnet = asyncio.create_task(self._tmp_vpnnet(q_node))

                    for _url in l_source:
                        await q_url.put(_url)
                    recent_put = True

                    time_add = time()
                else:
# #                    debug(f'{name} in processing')
                    print('=', end='', file=sys.stderr, flush=True)
            else:
                if nr_remain > 1:
# #                    debug(f'{name} remain {nr_remain} candidate, do nothing')
                    print(f'.{nr_remain}.', end='', file=sys.stderr, flush=True)
                else:
# #                    debug(f'{name} remain {nr_remain} candidate, frequently check, do nothing')
                    print(f'*{nr_remain}*', end='', file=sys.stderr, flush=True)

            t_increase, t_decrease, t_timeout = asyncio.create_task(e_increase.wait()), asyncio.create_task(e_decrease.wait()), asyncio.create_task(asyncio.sleep(600 if recent_put else 60))
            done, _ = await asyncio.wait({t_exit, t_increase, t_decrease, t_timeout}, return_when=asyncio.FIRST_COMPLETED)
            if t_timeout in done:
                continue
            elif t_exit in done:
# #                info(f'{name} got exit flag, exit')
                break
            elif t_increase in done:
                e_increase.clear()
                nr_remain = q_tested_node.qsize()
                if nr_remain >= 10:
                    if not test_mode:
                        debug(f'{nr_remain=}, remove tasks in q_url/node/uniq_node/ip_node/area_node/conn_node')
                        # 终止查找
                        for _q in (q_url, q_node, q_uniq_node, q_ip_node, q_area_node, q_conn_node):
                            while 1:
                                try:
                                    _q.get_nowait()
                                except asyncio.QueueEmpty:
                                    break
                                else:
                                    _q.task_done()
                    else:
                        debug(f'in test_mode, not stop measuring node(s)')
                else:
                    trace(f'now {nr_remain=}')
            else:
                e_decrease.clear()
                debug(f'{name} candidate decreased to {q_tested_node.qsize()}, check')
                continue

        info(f'{name} exit.')
        return nr, q_tested_node.qsize()

    async def do(self, test_mode: bool=False):
        if test_mode:
            warn(f'{"-"*10} IN TEST MODE {"-"*10}')
        else:
            info(f'{"-"*10} IN PROD MODE {"-"*10}')
        q_url, q_node, q_uniq_node, q_ip_node, q_area_node, q_conn_node, q_tested_node = \
                asyncio.Queue(), asyncio.Queue(), asyncio.Queue(), asyncio.Queue(), asyncio.Queue(), asyncio.PriorityQueue(), asyncio.PriorityQueue()
        event_candidate_increase, event_candidate_decrease = asyncio.Event(), asyncio.Event()

        l_url2node = [asyncio.create_task(self.url2node(f'url2node-{i:02d}', event_exit, q_url, q_node), name=f'url2node-{i:02d}') for i in range(1, 10 + 1)]
        uniq_nodes = asyncio.create_task(self.uniq_nodes(f'uniq-worker', event_exit, q_node, q_uniq_node), name='uniq_node')
        l_host2ip = [asyncio.create_task(self.host2ip(f'host2ip-{i:02d}', event_exit, q_uniq_node, q_ip_node), name=f'host2ip-{i:02d}') for i in range(1, 30 + 1)]
        l_ip2area = [asyncio.create_task(self.ip2area(f'ip2area-{i:02d}', event_exit, q_ip_node, q_area_node), name=f'ip2area-{i:02d}') for i in range(1, 2 + 1)]
        l_filter_bad_ip = [asyncio.create_task(self.filter_bad_ip(f'badip-{i:02d}', event_exit, q_area_node, q_conn_node), name=f'badip-{i:02d}') for i in range(1, 30 + 1)]
        l_measure_node = [asyncio.create_task(self.measure_node(f'measure-{i:02d}', port, event_exit, q_conn_node, q_tested_node, event_candidate_increase), name=f'measure-{i:02d}') for i, port in enumerate(port_range, 1)]
        launch = asyncio.create_task(self.launch(f'launcher', event_exit, q_tested_node, test_mode, event_candidate_decrease), name='launch')
        dispatch = asyncio.create_task(self.dispatch(f'dispatch', event_exit, q_url, q_node, q_uniq_node, q_ip_node, q_area_node, q_conn_node, q_tested_node, event_candidate_increase, event_candidate_decrease, test_mode), name='dispatch')
        done, _ = await asyncio.wait(l_url2node)
        l = [_done.result() for _done in done]
        s = sum(l)
        info(f'{len(l_url2node)} l_url2node exited. processed urls: {s} {l}')
        done = await uniq_nodes
        info(f'uniq_nodes exited. uniq, total: {done}')
        done, _ = await asyncio.wait(l_host2ip)
        l = [_done.result() for _done in done]
        s = list(map(sum, zip(*l)))
        info(f'{len(l_host2ip)} l_host2ip exited. total, filtered: {s} {l}')
        done, _ = await asyncio.wait(l_ip2area)
        l = [_done.result() for _done in done]
        s = list(map(sum, zip(*l)))
        info(f'{len(l_ip2area)} l_ip2area exited. total, filtered: {s} {l}')
        done, _ = await asyncio.wait(l_filter_bad_ip)
        l = [_done.result() for _done in done]
        s = list(map(sum, zip(*l)))
        info(f'{len(l_filter_bad_ip)} l_filter_bad_ip exited. total, filtered: {s} {l}')
        done, _ = await asyncio.wait(l_measure_node)
        l = [_done.result() for _done in done]
        s = list(map(sum, zip(*l)))
        info(f'{len(l_measure_node)} l_measure_node exited. total, filtered: {s} {l}')
        done = await launch
        info(f'launch exited. total, remain: {done}')
        done = await dispatch 
        info(f'dispatch exited. nr_dispatch, candidate_remain: {done}')


@logger.catch
async def main(test_mode: bool):
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT)

    x = NodeProcessor()
    await x.do(test_mode)
    await x.clean()

    info(f'done')



if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    parser = argparse.ArgumentParser(prog='make_proxy.py')
    parser.add_argument('-t', '--test', action='store_true', help='in test mode')
    parser.add_argument('-l', '--loglevel', choices=['trace', 'debug', 'info'], default='debug', help='set log level')
    args = parser.parse_args()

    # 初始化日志
    logger.remove()
    logger.add(sys.stderr, colorize=True, format='<green>{time:YYYYMMDD_HHmmss}</green><cyan>{level:.1s}</cyan>:{module}.{function}:{line}|<level>{message}</level>', filter='', level=args.loglevel.upper())
    mylogger = logger.opt(colors=True)
    mylogger.level('TRACE', color='<fg blue>')
    mylogger.level('DEBUG', color='<fg light-blue>')
    mylogger.level('INFO', color='<bold><fg white>')
    mylogger.level('SUCCESS', color='<bold><fg GREEN>')
    mylogger.level('WARNING', color='<bold><fg yellow>')
    mylogger.level('ERROR', color='<bold><bg RED><fg white>')
    mylogger.level('CRITICAL', color='<bold><bg WHITE><fg red>')
    trace, debug, info, succ, warn, error, critical = mylogger.trace, mylogger.debug, mylogger.info, mylogger.success, mylogger.warning, mylogger.error, mylogger.critical
#-#    trace(f'this is trace')
#-#    debug(f'this is debug')
#-#    info(f'this is info')
#-#    succ(f'this is succ')
#-#    warn(f'this is warning')
#-#    error(f'this is error')
#-#    critical(f'this is critical')
#-#    sys.exit(0)

    asyncio.run(main(args.test), debug=args.test)


