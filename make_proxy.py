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
from aiohttp_socks import ProxyType, ProxyConnector
import asyncio
# 貌似还是有警告
#setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)
#import uvloop
import sys
import os
import os.path
import random
from random import sample
import shlex
import subprocess
from subprocess import TimeoutExpired
from time import time
import ssl
import certifi
from collections import defaultdict
#import pprint
import json
from pathlib import PurePath
from copy import deepcopy
from urllib.parse import urlparse, unquote_plus, parse_qs, urlunparse, quote
#from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
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
from dns.asyncresolver import Resolver
import dns.resolver
#from lxml import etree
from functools import partial
from logging import INFO, DEBUG
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_random, retry_if_result, before_sleep_log, retry_if_exception_type, TryAgain
from loguru import logger
logger.remove()
#logger.add(sys.stderr, backtrace=True, diagnose=True, colorize=True, format='<green>{time:YYYYMMDD_HHmmss}</green><cyan>{level:.1s}</cyan>|<level>{message}</level>', filter='', level='DEBUG')
logger.add(sys.stderr, colorize=True, format='<green>{time:YYYYMMDD_HHmmss}</green><cyan>{level:.1s}</cyan>:{module}.{function}:{line}|<level>{message}</level>', filter='', level='DEBUG')
mylogger = logger.opt(colors=True)
mylogger.level('INFO', color='<white>')
mylogger.level('DEBUG', color='<blue>')
#mylogger.level('WARNING', color='<cyan><BLUE>')
mylogger.level('WARNING', color='<yellow>')
#mylogger.level('ERROR', color='<red><WHITE>')
mylogger.level('ERROR', color='<RED><white>')
info, debug, error, warn, exception = mylogger.info, mylogger.debug, mylogger.error, mylogger.warning, mylogger.exception
from make_proxy_conf import port_range
from make_proxy_conf import proxies, headers, conf_tpl
from make_proxy_conf import proxy_host, proxy_port, proxy_user, proxy_pass
from make_proxy_conf import test_wait_seconds
from make_proxy_conf import v2ray_path, hysteria_path, hysteria2_path, conf_basepath
from make_proxy_conf import inboundsSetting, outboundsSetting_vmess, outboundsSetting_ss, outboundsSetting_trojan, outboundsSetting_vless
from make_proxy_conf import settingHysteria , settingHysteria2
event_exit = asyncio.Event()
CTRL_C_TIME = 0


@dataclass
class Node(object):
    '''代表节点的数据类
    '''
    proto: str
    uuid: str = ''
    ip: str = ''
    port: int = 0
    param: str|list|dict = None  # 包含协议需要的
    alias: str = ''

    # 用于连通性测试
    real_ip: str = ''  # ip字段为域名时，连通性测试前需要获取对应ip地址. 如果ip=real_ip说明ip是地址，如果real_ip为空说明ip是域名但无法解析出地址，如果real_ip不为空且real_ip!=ip说明ip是域名且能解析出地址
    protocol: str = ''
    score: int|None = None
    score_unit: str = 'ms'

    # 标明来源
    source: str|list[str] = None  # 开始时都是str，排重后相同的节点其source合并成list[str]

    @property
    def is_connected(self):
        return self.score is not None

    def __repr__(self):
        if self.proto == 'hysteria2' or self.proto == 'hy':
            return f'<N h2:{self.ip}:{self.port}>'
        else:
            return f'<N {self.proto[:2]}:{self.ip}:{self.port}>'

    def __hash__(self):
        return hash((str(self), self.uuid, json.dumps(self.param)))


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
                debug(f'64decode failed {url=} s[:100]={s[:100]}')
            else:
                debug(f'64decode failed {url=} {s=}')
    else:
        if isinstance(rslt, bytes):
            try:
                rslt = rslt.decode()
            except UnicodeDecodeError as e:
                if len(rslt) > 500:
                    debug(f'decode bytes failed {url=} {e=} rslt[:100]={rslt[:100]}')
                else:
                    debug(f'decode bytes failed {url=} {e=} {rslt=}')
                rslt = None
    return rslt


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
        self.timeout = aiohttp.ClientTimeout(total=30.0, connect=10.0, sock_connect=15.0, sock_read=20.0)
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

    async def launch_proxy(self, node: Node, test_mode: bool = False, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        '''`test_mode` 为True时尝试通过命令行传入配置

        返回启动的进程和对应的配置文件路径，如果是命令行传入配置，则配置文件路径为空
        '''
        proto = node.proto
        match proto:
            case 'vmess' | 'vless' | 'ss' | 'trojan':
                return await self._launch_v2ray(node, test_mode, port)
            case 'hysteria':
                return await self._launch_hysteria(node, test_mode, port)
            case 'hysteria2':
                return await self._launch_hysteria2(node, test_mode, port)
            case _:
                error(f'unknown proto {proto} !!!')
                return None, ''


    async def _launch_v2ray(self, node: Node, test_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''
        if not test_mode:
            # kill running one
            os.system("kill `ps xf| grep -v grep | grep v2ray | awk '{print $1}'` > /dev/null 2>&1")

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if test_mode == True:
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

            args = shlex.split(f'{v2ray_path} run')
            p = await asyncio.create_subprocess_exec(*args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            p.stdin.write(json.dumps(settings).encode('utf8'))  # 配置内容通过STDIN传入
            if p.stdin.can_write_eof():
                p.stdin.write_eof()
        else:
            filepath = PurePath(conf_basepath, f"{node.proto}_{node.ip}.json").as_posix()
            with open(filepath, 'w') as fo:
                fo.write(jsonpickle.dumps(settings, indent=2))
            debug(f'conf file saved. {filepath}')
            # launch new process
            args = shlex.split(f'{v2ray_path} run -config {filepath}')
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/tmp/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

        await asyncio.sleep(test_wait_seconds)
        return p, filepath


    async def _launch_hysteria(self, node: Node, test_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if test_mode == True:  # 测试模式下无密码, 不输出日志到文件
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
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/tmp/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

        await asyncio.sleep(test_wait_seconds)
        return p, filepath

    async def _launch_hysteria2(self, node: Node, test_mode: bool, port: int = 0) -> tuple[asyncio.subprocess.Process, str]:
        p, filepath = None, ''

        nc = NodeConfig()
        settings = nc.genConfig[node.proto](node)
        if test_mode == True:  # 测试模式下无密码, 不输出日志到文件
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
            p = await asyncio.create_subprocess_exec(*args, stdout=open('/tmp/proxy.log', 'w'), stderr=subprocess.STDOUT, preexec_fn=preexec_ignore_sigint)

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
        self.interval = interval  # 代理每次测试之间的休眠时间
# #        self.urls = urls or ['https://www.google.com/', 'https://www.youtube.com/' ]  # 用于连通测试的目标站点，能访问到认为是连通
        self.urls = urls or ['https://www.youtube.com/', ]  # 用于连通测试的目标站点，能访问到认为是连通
        self.unit = unit  # 计量单位

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.clean()
        return False

#-#    async def connection_test_old(self, l_node: list[Node]) -> list[Node]:
#-#        port_lock = {port: asyncio.Lock() for port in self.port_range}
#-#
#-#        task_list = []
#-#        for i, node in enumerate(l_node, 1):
#-#            port = random.choice(list(port_lock.keys()))
#-#            task = asyncio.create_task(self._try_connect(node, port, port_lock[port]))
#-#            task_list.append(task)
#-#        if task_list:
#-#            await asyncio.wait(task_list)
#-#
#-#        l_node = [x for x in l_node if x.is_connected]
#-#        l_node.sort(key=lambda x: x.score)
#-#        return l_node

    async def _conn_test_worker(self, worker_name: str, port: int, queue: asyncio.Queue) -> list[Node]:
        client = httpx.AsyncClient(headers=headers, verify=False, timeout=self.timeout, proxies=f'http://127.0.0.1:{port}')
        while True:
            try:
                node = queue.get_nowait()
                try:
# #                    ping, nr_succ = await self._popen_conn(node, port, client)
                    ping, nr_succ = await self._popen_conn(node, port, client)
                    if ping >= 9999999 or nr_succ < self.nr_min_succ:
                        ping = None
                    if ping:
                        info(f'{worker_name} conn succ {ping}{self.unit} {node} {node.alias}')
                    node.score = ping
                    node.score_unit = self.unit
                finally:
                    queue.task_done()
            except asyncio.QueueEmpty:
                break

        await client.aclose()
# #        debug(f'{worker_name} exit.')

    async def connection_test(self, l_node: list[Node]) -> list[Node]:
        q = asyncio.Queue()
        list(map(lambda x: q.put_nowait(x), l_node))
        self.port_range = self.port_range[:q.qsize()]    # 端口数决定了worker数，如果总任务数少于可用端口数则不创建那么多worker
# #        debug(f'create {len(self.port_range)} workers')
        task_list = [asyncio.create_task(self._conn_test_worker(f'worker-{_i:02d}', _port, q)) for _i, _port in enumerate(self.port_range, 1)]
        debug(f'total {len(task_list)} workers')
        if task_list:
            await asyncio.wait(task_list)
        l_node = [x for x in l_node if x.is_connected]
        l_node.sort(key=lambda x: x.score)
        return l_node

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
        url = random.choice(self.urls)
        try:
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
                except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                        break
                except (ssl.SSLError, ssl.SSLZeroReturnError, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError, httpx.ProxyError) as e:
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

        return score, nr_succ

    async def _popen_conn_old(self, node: Node, port: int, client: aiohttp.ClientSession=None) -> tuple[int, int]:
        '''aiohttp实现
        '''
        score = self._init_score()
        nr_succ = 0

        p, config_path = await self.launch_proxy(node, True, port)
        url = random.choice(self.urls)
        try:
            for i in range(self.nr_try):
                try:
                    begin = time()
                    resp = await self.client.head(url=url, timeout=self.timeout, proxy=f'http://127.0.0.1:{port}')
                    finish = time()
# #                    body = await resp.read()
# #                    length = len(body or '')
                    length = 0
                    nr_succ += 1
                    latency = int((finish - begin) * 1000)
                    #debug(f'{node} times: {i + 1} score:{latency}ms response: {length} bytes')
                    score = self._score(latency, length, score)
                    if nr_succ >= self.nr_min_succ:  # 达到阈值提前退出
                        break
                except aiohttp.ClientConnectionError as e:
# #                    debug(f'{node} not available: ClientConnectionError {e=}')
#                    mylogger.opt(exception=True).error(f'got error {url}', diagnose=False, backtrace=False)
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
            except:
                pass

        return score, nr_succ


    async def _http_connect(self, node: Node, proxy_auth: aiohttp.BasicAuth|None = None) -> tuple[int, int]:
        score = self._init_score()
        nr_succ = 0
        url = random.choice(self.urls)

        # https://github.com/encode/httpx/discussions/2350  httpx.URL() does not parse url correctly with curly brackets in password
        p = httpx.Proxy(httpx.URL(f'http://{proxy_host}:{proxy_port}/', username=proxy_user, password=proxy_pass))
# #        client = httpx.AsyncClient(timeout=self.timeout, proxies=f'http://{quote(proxy_user)}:{quote(proxy_pass)}@{proxy_host}:{proxy_port}')

        client = httpx.AsyncClient(headers=headers, verify=False, timeout=self.timeout, proxies=p)
# #        client = httpx.AsyncClient(timeout=self.timeout, proxies=p)
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
                warn(f'{node} {i+1}/{self.nr_try} test failed: {type(e)} {e}')
                if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                    break
            await asyncio.sleep(self.interval)
        await client.aclose()
        return score, nr_succ

    async def _socks_connect(self, ip: str, port: int, user: str, password: str):
        score = self._init_score()
        nr_succ = 0
        url = random.choice(self.urls)
        connector = ProxyConnector(proxy_type=ProxyType.SOCKS5, host=ip, port=port, username=user, password=password, rdns=True)
        for i in range(self.nr_try):
            try:
                begin = time()
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.head(url=url, timeout=self.timeout) as resp:
                        body = await resp.read()
                finish = time()
                length = len(body or '')
                nr_succ += 1
                latency = int((finish - begin) * 1000)
                info(f'{node} times: {i + 1} score:{latency}{self.unit} response: {length} bytes')
                score = self._score(latency, length, score)
            except Exception as e:
                error(f'{node} test failed: {e}')
                if self.nr_try - i - 1 + nr_succ < self.nr_min_succ:
                    break
            await asyncio.sleep(self.interval)
        return score, nr_succ
#-#
#-#    async def _try_connect(self, node: Node, port: int, port_lock: asyncio.Lock):
#-#        node.score = None
#-#        if node.protocol == 'http':
#-#            ping, nr_succ = await self._http_connect(node)
#-#        elif node.protocol == 'socks':
#-#            ping, nr_succ = await self._socks_connect(node)
#-#        else:
#-#            async with port_lock:
#-#                ping, nr_succ = await self._popen_connect(node, port)
#-#        if ping >= 9999999:
#-#            ping = None
#-#        if nr_succ < self.nr_min_succ:
#-#            ping = None
#-#        if ping:
#-#            info(f'conn succ {ping}{self.unit} {node} {node.alias}')
#-#        else:
#-#            pass
#-#            #debug(f'connect failed for {node}')
#-#        node.score = ping
#-#        node.score_unit = self.unit


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
#                    if attempt.retry_state.attempt_number >= 2:
#                        debug(f'getting {attempt.retry_state.attempt_number} {url}')
#                        debug(f'using proxy ...')
#                        r = await self.client.get(url, timeout=10, proxy=proxies['http://'], ssl=False)
#                    else:
#                        r = await self.client.get(url, timeout=10, ssl=False)
                    r = await self.client.get(url, timeout=10, ssl=True)
                    async with r:
                        if r.status == 200:
                            content = await r.text()
                        elif r.status == 404:
                            warn(f'{r.status=} fetching {url=}')
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
                case 'trojan': # <password>@<ip>:<port>?<extra>#<alias>
                    try:
                        _tmp, _ip, _port = re.split(':|@', m.netloc, 2)
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
# #                    try:
# #                        _s = b64decode(m.netloc.encode(), validate=True).decode()
                    _s = b64d(m.netloc.encode(), url, False)
                    if not _s:
# #                    except:  # 非整体base64编码
                        *_tmp, _ip_port = m.netloc.split('@')
                        _tmp = ''.join(_tmp)
                        try:
                            _ip, _port = _ip_port.split(':', 1)
                        except ValueError as e:
                            warn(f'skip one ss node cause got ValueError: {e} {_ip_port=} {_node=} {url=}')
                            continue
                        if _tmp.count('-') != 4:
                            _uuid = b64d(_tmp, url)
                            _uuid = _uuid.decode() if type(_uuid) is bytes else _uuid
                            if not _uuid:
                                debug(f'_uuid no need decode, {_node=} {url=}')
                                _uuid = _tmp.decode() if type(_tmp) is bytes else _tmp
    #                            _uuid = _tmp
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
                            warn(f'error parse {e}, {_node=}, {url=}')
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

                case 'vless':  # <uuid>@<ip>:<port>?<extra>#<alias>
                    try:
                        _uuid, _ip, _port = re.split(':|@', m.netloc, 2)
                        _extra = parse_qs(m.query) if m.query else {}
                        _extra = dict((_k,_v[0]) for _k,_v in _extra.items())
                        _alias = unquote_plus(m.fragment)
                        #debug(f'vless:{_node}')
                        if 'path' not in _extra:
                            _extra['path'] = '/'
                        if 'type' not in _extra:
                            debug(f'parse vless, no \'type\' in _extra, {url=}')
                            continue
                        l_node.append(Node(proto=_proto, uuid=_uuid, ip=_ip, port=int(_port), param=_extra, alias=_alias, source=url))
                    except Exception as e:
                        warn(f'got error when add vless node {e} {m=} {url=}')
                case 'hysteria2' | 'hy2':  # <auth>@<server>:<port>/?insecure=<insecure>&sni=<sni>#<name>
                    try:
                        _auth, _server, _port = re.split(':|@', m.netloc, 2)
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
                    warn(f'unknown {_proto=} source: {url=} {_node=}')

        return l_node


    async def _tmpDetectFreeNodeFileName(self) -> list[str]:
        """临时加上，用来尝试获取非固定的文件名
        """
        l_url = []
        today = datetime.today()
        yesterday = today + timedelta(days=-1)
        beforeyesterday = yesterday + timedelta(days=-1)
        for _day in [today, yesterday, beforeyesterday]:
            url = f'https://freenode.me/wp-content/uploads/{_day.year}/{_day.month:02d}/{_day.month:02d}{_day.day:02d}{{}}.txt'
            l_cor = [self.client.head(url.format(x if x else ''), timeout=3, ssl=False) for x in range(100)]
            #l_cor.append(self.client.head(f'https://freenode.me/wp-content/uploads/{_day.year}/{_day.month:02d}/{_day.month:02d}{_day.day:02d}.txt', timeout=3, ssl=False))
            l_rslt = await asyncio.gather(*l_cor, return_exceptions=True)
            for r in l_rslt:
                if isinstance(r, aiohttp.ClientResponse):
                    if r.status == 200:
                        debug(f'detected {r.url}')
                        l_url.append(str(r.url))

        #debug(f'detected freenode.me url: {l_url}')
        return l_url

    async def _tmpDetectMiBeiFileName(self) -> list[str]:
        l_url = []
        today = datetime.today()
        url = 'https://www.mibei77.com/search/label/jiedian'
        content = await self._getNodeData(url)
        if not content:
            return l_url
        m = re.search("<article class='blog-post hentry index-post post-0'>.+?<a href='([^']+)' .+?>.+?</article>", content, re.M|re.U|re.S)
        if m:
            today_url = m.group(1)
            debug(f'{today_url=}')
            content = await self._getNodeData(today_url)
            if content:
                m = re.search('http://mm\.mibei77\.com/\d{6}/.+?\.txt', content)
                if m:
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


    async def _tmp_freevpnx(self) -> list[Node]:
        url = 'https://url.cr/api/user.ashx?do=freevpn&ip=127.0.0.1&uuid=67ee96e3-70c5-4741-9105-60d7fd8c42b3'
        l_node = []
        content = await self._getNodeData(url)
        if content:
            content = re.sub('(\r\n){2,}', '\n', content)
            l_tmp = content.split('\n')
            debug(f'got {len(l_tmp)} record(s) from {url}')
            l_node = self.__class__._parseProto(l_tmp, url)

        return l_node


    async def _tmp_ssfree(self) -> list[Node]:
        url = 'https://view.ssfree.ru/'
        l_node = []
        content = await self._getNodeData(url)
        if not content:
            return l_node
        m = re.search('data-clipboard-text="(.+?)"', content)
        if m:
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
        else:
            warn(f'no node data found from {url}')

        return l_node

    async def _tmp_tolinkshare(self) -> list[Node]:
        l_node = []
        url = 'https://raw.fastgit.org/tolinkshare/freenode/main/README.md'
        content = await self._getNodeData(url)
        if content:
            l = re.findall('```(.+?)```', content, re.U|re.M|re.S)
            if l:
                l_tmp = list(filter(None, chain.from_iterable((x.split('\n') for x in l))))  # filter用于过滤空行
                debug(f'got {len(l_tmp)} record(s) from {url}')
# #                pp = pprint.PrettyPrinter(indent=2, width=80, compact=True, sort_dicts=False)
# #                debug(pp.pformat(l_tmp))
                l_node = self.__class__._parseProto(l_tmp, url)
        return l_node

    async def _tmp_vpnnet(self) -> list[Node]:
        l_node = []
        url = 'https://raw.fastgit.org/VpnNetwork01/vpn-net/main/README.md'
        content = await self._getNodeData(url)
        if content:
            l = re.findall('```(.+?)```', content, re.U|re.M|re.S)
            if l:
                l_tmp = list(filter(None, chain.from_iterable((x.split('\n') for x in l))))  # filter用于过滤空行
                debug(f'got {len(l_tmp)} record(s) from {url}')
# #                pp = pprint.PrettyPrinter(indent=2, width=80, compact=True, sort_dicts=False)
# #                debug(pp.pformat(l_tmp))
                l_node = self.__class__._parseProto(l_tmp, url)
        return l_node

    async def _parseNodeData(self, url: str, data: str=None) -> list[Node]:
        if url:
            #debug(f'getting {url}')
            r = await self._getNodeData(url)
            if not r:
                warn(f'no node data got from {url}')
                return []
        elif data:
            r = data
        else:
            warn('url and data both empty !')
            return []

        # 特殊处理
        if url == 'https://mareep.netlify.app/sub/merged_proxies_new.yaml':
            full_content = yaml.load(r, yaml.FullLoader)
            proxies = full_content.get('proxies')
            l_node = []
            for _x in proxies:
                match _x['type']:
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
                        l_node.append(Node(proto=_x['type'], uuid=_param['auth'], ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
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
                        l_node.append(Node(proto=_x['type'], uuid=_param['auth'], ip=_param['server'], port=int(_param['port']), param=_param, alias=_param['name'], source=url))
                    case _:
                        debug(f'未处理的协议 {_x["type"]}')
            debug(f'got {len(l_node)} record(s) from {url}')
            return l_node
                

        # 特殊处理
        if url.startswith('https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/'):
            debug(f'特殊处理w1770946466')
            l_new = []
            for _line in r.split('\n'):
                if _line.startswith('vmess://'):
                    _up = urlparse(_line)
#                    debug(f'{_line=} to {_up=}')
                    _tmp = b64d(_up.netloc)
#                    try:
#                        _tmp = b64decode(_up.netloc).decode()
#                    except Exception as e:
#                        warn(f'error b64decode {_up.netloc=}')
#                        continue
#                        pass
#                        mylogger.opt(exception=True).error(f'error b64decode {_up.netloc=}', diagnose=False, backtrace=False)
                    if _tmp:
                        try:
                            json.loads(_tmp)
                            _newline = _line
                        except Exception as e:  # 只对vmess中base64解码后不是json格式的内容进行修正
#                            debug(f'json.loads got {e} {_tmp=}')
                            try:
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
                                warn(f'parse failed {e} for {_tmp=}')
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
        if url == 'https://raw.fastgit.org/Rokate/Proxy-Sub/main/clash/clash_v2ray.yml':
            full_content = yaml.load(r, yaml.FullLoader)
            proxies = full_content.get('proxies')
            l_node = []
            for _x in proxies:
                try:
                    _param = {
                            'host': _x['server'],
                            'id': _x['uuid'],
                            'port': _x['port'],
                            'aid': _x['alterId'],
                            'tls': _x.get('tls', None),
# #                            'path': _x['ws-opts']['path'] if 'ws-opts' in _x and 'path' in _x['ws-opts'] else '/',
                            'path': _x.get('ws-opts', {}).get('path', '/'),
                            'host': _x.get('ws-opts', {}).get('headers', {}).get('host', {})
                    }
                    _param = {**_param, **_x}
                    l_node.append(Node(proto=_x['type'], uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                except Exception as e:
                    warn(f'decode failed for {url} {e=} {_x=}')
                    continue
            debug(f'got {len(l_node)} record(s) from {url}')
            return l_node

        if url == 'https://anaer.github.io/Sub/clash.yaml':
            full_content = yaml.load(r, yaml.FullLoader)
            proxies = full_content.get('proxies')
            l_node = []
            for _x in proxies:
                try:
                    match _x['type']:
                        case 'vmess':
                            _param = {
                                    'host': _x['server'],
                                    'id': _x['uuid'],
                                    'port': _x['port'],
                                    'aid': _x['alterId'],
                                    'tls': _x.get('tls', None),
    # #                            'path': _x['ws-opts']['path'] if 'ws-opts' in _x and 'path' in _x['ws-opts'] else '/',
                                    'path': _x.get('ws-opts', {}).get('path', '/'),
                                    'host': _x.get('ws-opts', {}).get('headers', {}).get('host', {})
                            }
                            _param = {**_param, **_x}
                            l_node.append(Node(proto=_x['type'], uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                        case 'vless':  # {'name': '加拿大 336', 'port': 443, 'server': '172.67.96.59', 'skip-cert-verify': False, 'tfo': False, 'tls': True, 'type': 'vless', 'uuid': 'b0138d55-a493-4dc3-9932-c6f0391707c1'}
                            _param = {
                                    'host': _x['server'],
                                    'id': _x['uuid'],
                                    'port': _x['port'],
                                    'path': _x.get('ws-opts', {}).get('path', '/'),
                                    'security': _x['tls'],
                                    'sni': _x.get('sni', None),
                                    'flow': _x.get('flow', None),
                            }
                            _param = {**_param, **_x}
                            l_node.append(Node(proto=_x['type'], uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                        case 'trojan':
                            _param = {
                                    'host': _x['server'],
                                    'port': _x['port'],
                                    'password': _x['password'],
                                    'allowInsecure': _x.get('skip-cert-verify', True),
                                    'sni': _x['sni'],  # unused
                                    'network': _x['network'],  # unused
                                    'upd': _x.get('udp', False),  # unused
                                    }
                            l_node.append(Node(proto=_x['type'], uuid=_x.get('uuid', ''), ip=_x['server'], port=int(_x['port']), param=_param, alias=_x['name'], source=url))
                        case _:
                            error(f'unused node type {_x["type"]}')
                except Exception as e:
                    warn(f'decode failed for {url} {e=} {_x=}')
                    continue
            debug(f'got {len(l_node)} record(s) from {url}')
            return l_node

        s = b64d(r, url)
        if not s:
            error(f'decode failed {url} for {r[:100]}')
            return []
        ls = s.split('\n')

        try:
            l_tmp = (x for x in ls if x)

            # 特殊处理
            if url == 'https://raw.fastgit.org/learnhard-cn/free_proxy_ss/main/free':
                debug(f'特殊处理 {url=}')
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
                        error(f'skip node from {url} {e=} {_x=}')
                        continue
                l_tmp = _l_n

            # 特殊处理
            if url == 'https://raw.fastgit.org/Leon406/SubCrawler/master/sub/share/ss':
                l_new = []
#                debug(f'try to process special format node, {url=}')
                for _x in l_tmp:
                    try:
                        _idx = _x.find('#')
                        _t = b64decode(_x[5:_idx]).decode()
                        _p1, _p2 = _t.split('@', 1)
                        x = _x[:5] + b64encode(_p1.encode()).decode() + '@' + _p2 + _x[_idx :]
                    except Exception as e:
                         warn(f'got {e} processing ss node in {url}')
                         continue
                    l_new.append(x)
                l_tmp = l_new
                #debug(f'now {l_tmp=}')

            # 特殊处理
            if url == 'https://raw.fastgit.org/eycorsican/rule-sets/master/kitsunebi_sub':
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
                            warn(f'parse vmess data from {url=} got {e}')
                            continue
                    l_new.append(_x)
                l_tmp = l_new


            # 特殊处理
            if url == 'https://raw.fastgit.org/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg':
                l_new = []
                debug(f'try to process special format node, {url=}')
                for _x in l_tmp:
                    if _x.startswith('vless://'):
                        _idx = _x.find('?')
                        try:
                            _t = b64decode(_x[8:_idx]).decode()
                            _p1, _p2 = _t.split(':', 1)
# #                            debug(f'{_t=} {_p1=} {_p2=}')
                        except Exception as e:
                            continue
                        else:
                            _x = _x[:8] + _p2 + _x[_idx :]
# #                            debug(f'{_x=}')
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
                            warn(f'parse vmess got {e}, {url=} {_x[8:_idx]}')
                            continue
                    l_new.append(_x)
                l_tmp = l_new

# #                debug(f'now Jsnzkpg got {len(l_tmp)} records')
# #                debug(f'{l_tmp=}')
        except binascii.Error:
            if r.startswith('https://api.tsutsu.one/sub'):
                debug(f'try to parse as param of \'url\'')  # https://api.tsutsu.one/sub?target=mixed&url=xxxxxx
                up = urlparse(r)
                debug(f'{r=} {url=} {data=}')
                qs = parse_qs(up.query)
                l_url = qs['url'][0]
                l_tmp = l_url.split('|') or []
            else:  # 尝试加=解码
                l_tmp = (x for x in b64d(r, url).split('\n') if x) if r else []
        except BaseException as e:
            error(f'got error {e=}')
            raise e
        if not isinstance(l_tmp, list):
            l_tmp = list(l_tmp)

        if url:
            debug(f'got {len(l_tmp)} record(s) from {url}')
        else:
            debug(f'got {len(l_tmp)} record(s) from data')
        return self.__class__._parseProto(l_tmp, url)


    async def _host2ip(l: list[Node], timeout: int=5, batch: int=2000):
        """使用dnspython异步获取域名对应的ip地址
        `read_ip` 为空 表示`ip`字段是域名，无法解析成ip
                  ==`ip` 表示`ip`字段本身就是ip地址
                  !=`ip` 表示`ip`字段是域名，可以解析成ip
        """
        idx, nr = 0, len(l)
        rs = Resolver()
        rs.nameservers = ['8.8.8.8', '8.8.4.4']

        while idx <= nr:
            l_host = []
            for x in l[idx: idx+batch]:
                #debug(f'batch [{idx}: {idx+batch})')
                try:
                    ipaddress.IPv4Address(x.ip)
                except:
                    # 是host
                    l_host.append(x)
                else:  # 是有效ip
                    x.real_ip = x.ip
                    continue
            #debug(f'batch [{idx}: {idx+batch}] need query {len(l_host)} host(s)')

            l_cor = [rs.resolve_name(x.ip, socket.AF_INET, lifetime=timeout) for x in l_host]
            l_rslt = await asyncio.gather(*l_cor, return_exceptions=True)
            for i, x in enumerate(l_rslt):
                if isinstance(x, dns.resolver.HostAnswers):
                    l_host[i].real_ip = next(x.addresses())  # 只取第一个地址
# #                elif isinstance(x, dns.resolver.NXDOMAIN):  # 域名解析失败
# #                    cnt_bad += 1
# #                else:  #  失败/超时/无响应
# #                    #warn(f'{i=} failed type {type(x)}')
# #                    cnt_bad += 1

            idx += batch

# #        debug(f'host->ip succ {cnt_ok} failed {cnt_bad}')
        cnt_noneed = sum(1 for x in l if x.real_ip and x.real_ip == x.ip)
        cnt_ok = sum(1 for x in l if x.real_ip and x.real_ip != x.ip)
        #debug(f'some host->ip {[(x.proto, x.uuid, x.ip, x.real_ip, x.port) for x in l if x.real_ip and x.real_ip != x.ip][:10]}')
        cnt_bad = sum(1 for x in l if not x.real_ip)
        info(f'total {len(l)} is_ip {cnt_noneed} host->ip succ {cnt_ok} failed {cnt_bad}')


    def _filterBySimpleLow(l: list[Node], timeout: int=5, batch: int=800) -> list:
        """简单过滤地址
        用real_ip字段，用socket尝试连接，能连接上的才保留, 用select提速

        `batch` 用来指定一次在select上注册的文件对象数量，设得大会遇到打开太多文件的错误，系统默认1024，可考虑改大点比如 `ulimit -Hn 4096` `ulimit -Sn 4096`
        """
        idx, nr, l_ret = 0, len(l), []
        d = {}
        with selectors.DefaultSelector() as sel:
            while idx < nr:
                succ, bad = 0, 0
# #                debug(f'connect_ex and register [{idx}:]...')
                for x in l[idx: ]:
                    idx += 1
                    # 域名无法解析出ip的直接算失败，过滤掉
                    if not x.real_ip:
                        bad += 1
                        continue

                    sk = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
                    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sk.connect_ex((x.real_ip, int(x.port)))
                    k = sel.register(sk, selectors.EVENT_READ|selectors.EVENT_WRITE)
                    d[k] = (sk, x)
                    if len(d) >= batch:
                        break

                debug(f'do select with {len(d)} registered.')
                while 1:
                    l_events = sel.select(timeout)
                    if not l_events:
                        break
                    for _k, _events in l_events:
                        if _events & selectors.EVENT_READ or _events & selectors.EVENT_WRITE:
                            _sk, _node = d.pop(_k)
                            l_ret.append(_node)
                            try:
                                _sk.close()
                            except:
                                pass
                            sel.unregister(_sk)
                            succ += 1
                        else:
                            debug(f'unknown evnet {_events} for {d[_k][1]}')
                # 把不成功的socket关闭
                bad += len(d)
                while 1:
                    try:
                        _, (_sk, _) = d.popitem()
                        sel.unregister(_sk)
                        try:
                            _sk.close()
                        except:
                            pass
                    except KeyError:
                        break

# #                debug(f'batch {succ=} {bad=}')

        return l_ret
    
    async def _filterBySimple(l: list[Node], timeout: int=3, batch: int=100) -> list:
        """通过判断连通性过滤节点
        """
        idx, nr, l_ret = 0, len(l), []
        while idx <= nr:
            #debug(f'batch [{idx}: {idx+batch})')
            l_cor = [asyncio.wait_for(asyncio.open_connection(x.ip, int(x.port), limit=8), timeout) for x in l[idx: idx+batch]]
            l_rslt = await asyncio.gather(*l_cor, return_exceptions=True)

            for i, x in enumerate(l_rslt):
                if isinstance(x, tuple):
                    _, w = x
                    #debug(f'{l[idx+i]} passed')
                    w.close()
                    try:
                        await w.wait_closed()
                    except Exception as e:
                        warn(f'got except when wait_closed, {type(e)}, {e}')

            l_ret.extend(compress(l[idx: idx+batch], [isinstance(x, tuple) for x in l_rslt]))
            idx += batch

        return l_ret

    async def _getNodeUrl(self) -> list[str]:
        # get node list from file or internet
        today = datetime.today()
        yesterday = today + timedelta(days=-1)
        beforeyesterday = yesterday + timedelta(days=-1)
        l_freenode_url = await self._tmpDetectFreeNodeFileName()
        l_mibei_url = await self._tmpDetectMiBeiFileName()
        #l_url = []  # debug only
        l_source = [*l_freenode_url,
            *l_mibei_url,
            f'https://clashnode.com/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',
            f'https://clashnode.com/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
#            f'https://clashnode.com/wp-content/uploads/{beforeyesterday.year}/{beforeyesterday.month:02d}/{beforeyesterday.strftime("%Y%m%d")}.txt',

            f'https://nodefree.org/dy/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',
            f'https://nodefree.org/dy/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://clashgithub.com/wp-content/uploads/rss/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://clashgithub.com/wp-content/uploads/rss/{today.strftime("%Y%m%d")}.txt',
#            f'https://nodefree.org/dy/{beforeyesterday.year}/{beforeyesterday.month:02d}/{beforeyesterday.strftime("%Y%m%d")}.txt',

            f'https://oneclash.cc/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
            f'https://oneclash.cc/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',

            f'https://freeclash.org/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%m%d")}.txt',
            f'https://freeclash.org/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%m%d")}.txt',

            'https://raw.fastgit.org/umelabs/node.umelabs.dev/master/Subscribe/v2ray.md',

            'https://raw.fastgit.org/freefq/free/master/v2',
            #'https://raw.fastgit.org/tbbatbb/Proxy/master/dist/v2ray.config.txt', 
# #            'https://raw.fastgit.org/tbbatbb/Proxy/master/dist/v2ray.config.txt', 
            'https://raw.fastgit.org/ts-sf/fly/main/v2',
            'https://raw.fastgit.org/ts-sf/fly/main/v2',
            ##'https://raw.fgit.ml/ts-sf/fly/main/v2', 
            'https://cdn.jsdelivr.net/gh/ermaozi01/free_clash_vpn/subscribe/v2ray.txt',
# #            'https://tt.vg/freev2',
            'https://v2ray.neocities.org/v2ray.txt',
            'https://raw.fastgit.org/Leon406/SubCrawler/master/sub/share/v2',
            #'https://raw.fastgit.org/Leon406/SubCrawler/master/sub/share/ss',
            'https://raw.fastgit.org/Leon406/SubCrawler/master/sub/share/tr',
            'https://raw.fastgit.org/peasoft/NoMoreWalls/master/list.txt',
            #'https://raw.fastgit.org/Lewis-1217/FreeNodes/main/bpjzx1',
            #'https://raw.fastgit.org/Lewis-1217/FreeNodes/main/bpjzx2',
            'https://raw.fastgit.org/a2470982985/getNode/main/v2ray.txt',
            'https://raw.fastgit.org/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt',
            'https://raw.fastgit.org/ripaojiedian/freenode/main/sub',

            #'https://gh-proxy.com//raw.fastgit.org/yaney01/Yaney01/main/yaney_01',
            #'https://raw.fastgit.org/sun9426/sun9426.github.io/main/subscribe/v2ray.txt',
            'https://raw.fastgit.org/learnhard-cn/free_proxy_ss/main/free',
            'https://raw.fastgit.org/Rokate/Proxy-Sub/main/clash/clash_v2ray.yml',
            'https://raw.fastgit.org/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg',
            'https://raw.fastgit.org/ZywChannel/free/main/sub',
            'https://raw.fastgit.org/free18/v2ray/main/v2ray.txt',
            #'https://sub.nicevpn.top/Clash.yaml',
            'https://raw.fastgit.org/mfuu/v2ray/master/v2ray',

           f'https://onenode.cc/wp-content/uploads/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime("%Y%m%d")}.txt',
           f'https://onenode.cc/wp-content/uploads/{today.year}/{today.month:02d}/{today.strftime("%Y%m%d")}.txt',

            'https://anaer.github.io/Sub/clash.yaml',

            # https://github.com/Helpsoftware/fanqiang
            'https://jiang.netlify.com/',
            'https://youlianboshi.netlify.app/',
            'https://raw.fastgit.org/eycorsican/rule-sets/master/kitsunebi_sub',
            'https://raw.fastgit.org/umelabs/node.umelabs.dev/master/Subscribe/v2ray.md',

            'https://raw.fastgit.org/w1770946466/Auto_proxy/main/Long_term_subscription_num',
            'https://raw.fastgit.org/mahdibland/ShadowsocksAggregator/master/Eternity',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{beforeyesterday.strftime("%y%m")}/{beforeyesterday.strftime("%y%m%d")}.txt',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{yesterday.strftime("%y%m")}/{yesterday.strftime("%y%m%d")}.txt',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{today.strftime("%y%m")}/{today.strftime("%y%m%d")}.txt',
             'https://mareep.netlify.app/sub/merged_proxies_new.yaml',  # https://github.com/vveg26/chromego_merge
            'https://raw.fastgit.org/a2470982985/getNode/main/v2ray.txt',  # https://github.com/Flik6/getNode
        ]
        #l_source = ['https://raw.fastgit.org/sun9426/sun9426.github.io/main/subscribe/v2ray.txt', ]
        #l_source = l_source[:5]+ l_source[-5:]  # debug only

        return l_source


    async def _getNodeList(self, from_source: bool=False) -> list[Node]:
        l_source = await self._getNodeUrl()
# #        l_source = ['https://raw.fastgit.org/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg',] # debug only
        l_rslt = await asyncio.gather(*[self._parseNodeData(x) for x in l_source])
        l_rslt.append(await self._tmp_freevpnx())
        l_rslt.append(await self._tmp_ssfree())
        l_rslt.append(await self._tmp_tolinkshare())
        l_rslt.append(await self._tmp_vpnnet())
        l_rslt.append(self.__class__._parseProto(['hysteria2://sharecentrepro@ushy2.sharecentre.online:4433?peer=ushy2.sharecentre.online&obfs=none#hy2%EF%BD%9CTEST',], 'test'))
        l_node = list(chain.from_iterable(l_rslt))

# #        event_exit.set()  # debug only

#        l_node = list(filter(lambda x: x.proto=='hysteria', l_node))  # debug only
        if event_exit.is_set():
            warn('got exit event')
            return []

        debug(f'total got {len(l_node):,} unfiltered node(s)')
        # remove dup while keeping order
        # merge source while check dup node
        st_exist = set()
        l_uniq = []
        d_nd = defaultdict(list)  # key: hash(Node)  value: list[source: str]
        for _i, _h in enumerate(map(hash, l_node)):
            if _h not in st_exist:
                l_uniq.append(l_node[_i])
                st_exist.add(_h)
            d_nd[_h].append(l_node[_i].source)
        for _n in l_uniq:
            _n.source = list(set(d_nd[hash(_n)]))  # 排重，一个源里可能重复出现相同节点
        del d_nd

        l_node = l_uniq
        info(f'after remove duplicate, remain {len(l_node):,} node(s)')
        st_all_source = set(chain.from_iterable(map(attrgetter('source'), l_node)))  # stat 不同来源的同一个节点累计计算
        #l_node = await self.__class__._filterBySimple(l_node, timeout=5, batch=800)
        debug(f'STAT source_cnt: {Counter((len(x.source) for x in l_node)).most_common()}')  # 按节点的来源数统计

        #with open('/tmp/dbg_nodes', 'w') as fo:
        #    fo.write(jsonpickle.dumps(l_node, indent=2))
        await self.__class__._host2ip(l_node, timeout=5, batch=2000)
        l_node = self.__class__._filterBySimpleLow(l_node, timeout=5, batch=3000)
        info(f'after simple filter, remain {len(l_node):,} node(s)')
        if event_exit.is_set():
            warn('got exit event')
            return []
        # 过滤掉中国节点
        l_node = list(filter(lambda x: x.alias.find('中国') == -1 and x.alias.find('CN') == -1, l_node))
        info(f'after cn filter, remain {len(l_node):,} node(s)')
        st_now_source = set(chain.from_iterable(map(attrgetter('source'), l_node)))  # stat
        warn(f'bad source: {st_all_source - st_now_source}')  # 连一个可连(不见得可用)节点都没有的来源

        debug(f'{Counter((x.proto for x in l_node)).most_common()}')
        return l_node

    async def do(self, from_source: bool=False):
        pp = pprint.PrettyPrinter(indent=2, width=80, compact=True, sort_dicts=False)
        start = time() # 服务起始时间，用于判断在一定间隔内重新选择节点时直接使用备选节点
        cur_node = None  # 当前选择节点
        alt_node = []  # 备选节点
        alt_quota = 10 # 备选节点数
        while 1:
            if alt_node:  # and time() - start < 3600 * 12:
                cur_node = alt_node.pop(0)
                debug(f'use alt_node {cur_node}, left {len(alt_node)}')
            else:
                cur_node = None
                del alt_node[:]
                l_node = await self._getNodeList(from_source)  # get node list
                d_source_cnt = dict(Counter(chain.from_iterable(_x.source for _x in l_node)).most_common())  # stat
                # check avaliable
                info(f'total {len(l_node):,} node(s) to test')
                begin = time()
                async with ProxyTest(port_range=port_range, nr_try=1, min_resp_count=1, interval=3, timeout=5) as at:
                    l_tested = await at.connection_test(l_node)
                debug(f'test duration: {time()-begin: .1f}s')

                if l_node:
                    info(f'<green>total {len(l_tested)/len(l_node)*100:.2f}% {len(l_tested):,}/{len(l_node):,} node(s) passed test</green>')
                    debug(f'STAT proto {Counter((x.proto for x in l_tested)).most_common()}')  # 按协议统计
                    debug(f'STAT ip/domain {Counter(("domain" if x.ip!=x.real_ip else "ip" for x in l_tested)).most_common()}')  # 按domain/ip统计
                    debug(f'STAT source_cnt {Counter((len(x.source) for x in l_tested)).most_common()}')  # 按节点来源数量统计
                d_avaliable = OrderedDict(Counter(chain.from_iterable(x.source for x in l_tested)).most_common())
                for _k, _v in d_avaliable.items():
                    debug(f'<green>{f"{_v}/{d_source_cnt[_k]}":<10}{_k}</green>')
                    del d_source_cnt[_k]
                for _k, _v in d_source_cnt.items():
                    debug(f'<yellow>{f"0/{_v}":<10}{_k}</yellow>')

                # 选择节点
                if l_tested:
                    filter_node_us = [x for x in l_tested if (x.alias.find('美国')!=-1 or x.alias.find('US')!=-1)]  # 美节点
                    filter_node_uk = [x for x in l_tested if (x.alias.find('英国')!=-1 or x.alias.find('UK')!=-1)]  # 英节点
                    filter_node_others = [x for x in l_tested if x not in filter_node_us and x not in filter_node_uk]  # 其他节点优先
                    filter_node = [*filter_node_us, *filter_node_uk, *filter_node_others]
                    cur_node =  filter_node[0] if filter_node else l_tested[0]
                    if filter_node and len(filter_node) > 1:
                        alt_node[:] = filter_node[1:1+alt_quota]
                    if len(alt_node) < alt_quota:
                        for _x in l_tested:
                            if _x != cur_node and _x not in alt_node:
                                alt_node.append(_x)
                                if len(alt_node) >= alt_quota:
                                    break
                    if alt_node:
                        debug(f'set alt_node to {len(alt_node)}: {alt_node}')

            if cur_node:
                info(f'chosen node {cur_node.score}{cur_node.score_unit}, {cur_node}: {cur_node.alias} from {cur_node.source}')
            # launch proxy service
            if sys.platform != 'win32' and cur_node:
                p, filepath = await self.launch_proxy(cur_node)
                info(f'service started, pid={p.pid}')
                at = ProxyTest(nr_try=2, min_resp_count=1, interval=8, timeout=7)
                proxy_auth = aiohttp.BasicAuth(proxy_user, proxy_pass)
# #                last_date = None
                while 1:
                    #debug(f'check node avaliable ...')
                    ping, nr_succ = await at._http_connect(cur_node, proxy_auth=proxy_auth)
                    #debug(f'check avaliable got {ping=} {nr_succ=}')
                    if ping >= 9999999 or nr_succ < at.nr_min_succ:
                        info(f'node invaliable, choose new one')
                        break
                    else:
                        #info(f'wait for next check ...')
                        print(f'{datetime.now().strftime("%H:%M:%S ")}', end='', file=sys.stderr, flush=True)

                        l_task = [asyncio.create_task(event_exit.wait()), asyncio.create_task(p.wait()), asyncio.create_task(asyncio.sleep(180))]
                        e_exit, p_exit, timeout = l_task
                        done, _ = await asyncio.wait(l_task, return_when=asyncio.FIRST_COMPLETED)
                        if timeout in done:
                            continue
                        elif e_exit in done:
                            info(f'got exit flag, exit')
                            break
                        elif p_exit in done:
                            warn(f'proxy killed? to pick new one...')
                            break

                try:
                    p.kill()
                except ProcessLookupError:
                    pass
                try:
                    await p.communicate()
                except ProcessLookupError:
                    pass
# #                debug(f'remove conf {filepath}')
                try:
# #                    pass
                    os.remove(filepath)
                except:
                    pass
                await at.clean()
            elif sys.platform != 'win32': # no node chosen
                warn(f'no avaliable node, sleep ...')
                try:
                    await asyncio.wait_for(event_exit.wait(), 300)
                except asyncio.exceptions.TimeoutError:
                    debug(f'no avaliable node, wake up and retry ...')
                else:
                    info(f'got exit flag, exit')
                    break
            else:
                debug(f'break on win32')
                break
            if event_exit.is_set():
                break


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
        setting[0]['listen'] = proxy_host
        setting[0]['port'] = proxy_port
        setting[0]['settings']['accounts'][0]['user'] = proxy_user
        setting[0]['settings']['accounts'][0]['pass'] = proxy_pass
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
        outboundsSetting[0]['streamSettings']['security'] = arg['tls'] or 'none'
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

        outboundsSetting[0]['streamSettings']['network'] = arg['type']
        outboundsSetting[0]['streamSettings']['tlsSettings']['serverName'] = arg.get('sni') or node.ip

        if arg['type'] == 'tcp':
            del outboundsSetting[0]['streamSettings']['wsSettings']
            if 'reality-opts' in arg and arg['reality-opts']:
                # 参考 https://github.com/XTLS/Xray-examples/blob/main/VLESS-TCP-XTLS-Vision-REALITY/config_client.jsonc
                del outboundsSetting[0]['streamSettings']['tlsSettings']
                outboundsSetting[0]['streamSettings']['security'] = 'reality'
                outboundsSetting[0]['streamSettings']['realitySettings']['serverName'] = arg['sni']
                outboundsSetting[0]['streamSettings']['realitySettings']['fingerprint'] = arg['fingerprint']
                outboundsSetting[0]['streamSettings']['realitySettings']['publicKey'] = arg['public-key']
                outboundsSetting[0]['streamSettings']['realitySettings']['shortId'] = arg['short-id']
        else:  # 'ws'
            outboundsSetting[0]['streamSettings']['wsSettings']['path'] = arg['path']
            outboundsSetting[0]['streamSettings']['wsSettings']['headers']['Host'] = arg.get('host', '')

        if arg['security'] is None or arg['security'] == 'none':
            del outboundsSetting[0]['streamSettings']['security']
        else:
            if not outboundsSetting[0]['streamSettings']['security']:  # 
                outboundsSetting[0]['streamSettings']['security'] = arg['security']

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
        settings['http']['listen'] = f'{proxy_host}:{proxy_port}'
        settings['http']['user'] = proxy_user
        settings['http']['password'] = proxy_pass
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
        settings['http']['listen'] = f'{proxy_host}:{proxy_port}'
        settings['http']['username'] = proxy_user
        settings['http']['password'] = proxy_pass
        settings['http']['realm'] = 'need pass'
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


@logger.catch
async def main():
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT)

    x = NodeProcessor()
    await x.do()
    await x.clean()

    info(f'done')

@logger.catch
async def test():
    x = NodeProcessor()
    #nc = NodeConfig()
    #settings = nc.genConfig[node.proto](node)
    #info(f'{jsonpickle.dumps(settings, indent=2)}')

    #filepath = PurePath(conf_basepath, f"{node.proto}_{node.ip}.json").as_posix()
    #with open(filepath, 'w') as fo:
        #    fo.write(jsonpickle.dumps(settings, indent=2))
    #debug(f'conf file saved. {filepath}')

    #proxy_auth = aiohttp.BasicAuth(proxy_user, proxy_pass)
    #at = ProxyTest(nr_try=3, min_resp_count=2, interval=8, timeout=5)
    #ping, nr_succ = await at._http_connect(node, proxy_auth=proxy_auth)
    #debug(f'check avaliable got {ping=} {nr_succ=}')

#    l_source = list(filter(lambda x: x.find('airport') != -1, l_source))

    today = datetime.today()
    yesterday = today + timedelta(days=-1)
    beforeyesterday = yesterday + timedelta(days=-1)
    l_source = [
#             'https://raw.fastgit.org/w1770946466/Auto_proxy/main/Long_term_subscription_num',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{beforeyesterday.strftime("%y%m")}/{beforeyesterday.strftime("%y%m%d")}.txt',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{yesterday.strftime("%y%m")}/{yesterday.strftime("%y%m%d")}.txt',
            f'https://raw.fastgit.org/w1770946466/Auto_proxy/main/sub/{today.strftime("%y%m")}/{today.strftime("%y%m%d")}.txt',
            'https://raw.fastgit.org/a2470982985/getNode/main/v2ray.txt',
            ]
#
    l_rslt = await asyncio.gather(*[x._parseNodeData(_x) for _x in l_source])
#    await x.clean()
#    return
    l_node = list(chain.from_iterable(l_rslt))

#-#    l_s = [
#-##            'hy2://HowdyHysteria2023w0W@hysteria.udpgw.com:8443/?insecure=1&sni=sni-here.com&obfs=salamander&obfs-password=HysteriaHowdy#Howdy%20Hysteria',
#-#            'hysteria2://sharecentrepro@ushy2.sharecentre.online:4433?peer=ushy2.sharecentre.online&obfs=none#hy2%EF%BD%9CTEST',
#-#            ]
#-#    l_node = x.__class__._parseProto(l_s, 'test')

#    l_node = list(filter(lambda x: x.proto=='hysteria', l_node))
#    l_node = list(filter(lambda x: x.proto=='vless', l_node))
#    l_node = await x._tmp_vpnnet()
    debug(f'total got {len(l_node):,} unfiltered node(s)')
#    debug(f'{l_node=}')
    if not l_node:
        await x.clean()
        return


#    nc = NodeConfig()
#    node = l_node[0]
#    settings = nc.genConfig[node.proto](node)
#    info(f'{jsonpickle.dumps(settings, indent=2)}')
#    filepath = PurePath(conf_basepath, f"{node.proto}_{node.ip}.json").as_posix()
#    with open(filepath, 'w') as fo:
#        fo.write(jsonpickle.dumps(settings, indent=2))
#    debug(f'conf file saved. {filepath}')
#    await x.clean()
#    return

    # remove dup while keeping order
    # merge source while check dup node
    st_exist = set()
    l_uniq = []
    d_nd = defaultdict(list)  # key: hash(Node)  value: list[source: str]
    for _i, _h in enumerate(map(hash, l_node)):
        if _h not in st_exist:
            l_uniq.append(l_node[_i])
            st_exist.add(_h)
        d_nd[_h].append(l_node[_i].source)
    for _n in l_uniq:
        _n.source = d_nd[hash(_n)]
    del d_nd
    l_node = l_uniq

    await x.__class__._host2ip(l_node, timeout=5, batch=2000)
    l_node = x.__class__._filterBySimpleLow(l_node, timeout=5, batch=3000)
    info(f'after simple filter, remain {len(l_node):,} node(s)')
    info(f'total {len(l_node):,} node(s) to test')
    debug(f'{Counter((x.proto for x in l_node)).most_common()}')

# #    nc = NodeConfig()
# #    for _node in l_node:
# #        settings = nc.genConfig[_node.proto](_node)
# #        info(f'\n{jsonpickle.dumps(settings, indent=2)}')
# #        filepath = PurePath(conf_basepath, f"{_node.proto}_{_node.ip}.json").as_posix()
# #        with open(filepath, 'w') as fo:
# #            fo.write(jsonpickle.dumps(settings, indent=2))
# #        debug(f'conf file saved. {filepath}')

    pp = pprint.PrettyPrinter(indent=2, width=80, compact=True, sort_dicts=False)

    async with ProxyTest(port_range=port_range, nr_try=2, min_resp_count=2, interval=3, timeout=5) as at:
        l_tested = await at.connection_test(l_node)
        if l_node:
            info(f'<green>total {len(l_tested)/len(l_node)*100:.2f}% {len(l_tested):,}/{len(l_node):,} node(s) passed test</green>')
            debug(f'STAT proto {Counter((x.proto for x in l_tested)).most_common()}')  # 按协议统计
            debug(f'STAT ip/domain {Counter(("domain" if x.ip!=x.real_ip else "ip" for x in l_tested)).most_common()}')  # 按domain/ip统计
            debug(f'STAT source_cnt {Counter((len(x.source) for x in l_tested)).most_common()}')  # 按节点来源数量统计

            d_source_cnt = dict(Counter(chain.from_iterable(_x.source for _x in l_node)).most_common())  # stat
            debug(pp.pformat(d_source_cnt))
            d_avaliable = OrderedDict(Counter(chain.from_iterable(x.source for x in l_tested)).most_common())
            for _k, _v in d_avaliable.items():
                debug(f'<green>{f"{_v}/{d_source_cnt[_k]}":<10}{_k}</green>')
                del d_source_cnt[_k]
            for _k, _v in d_source_cnt.items():
                debug(f'<yellow>{f"0/{_v}":<10}{_k}</yellow>')

    await x.clean()


if __name__ == '__main__':
    #asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    parser = argparse.ArgumentParser(prog='make_proxy.py')
    parser.add_argument('-t', '--test', action='store_true', help='in test mode')
    args = parser.parse_args()
    if args.test:
        warn(f'{"-"*10} IN TEST MODE {"-"*10}')
        asyncio.run(test())
    else:
        info(f'{"-"*10} IN PROD MODE {"-"*10}')
        asyncio.run(main())


