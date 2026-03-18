# -*- coding: utf-8 -*-
"""
抖音养号自动化脚本 (Douyin Account Nurturing Automation Script)

功能说明:
    本脚本使用uiautomator2 实现抖音账号的自动化养号操作，包括:
    - 自动浏览推荐视频
    - 随机点赞 (可配置概率)
    - 随机关注 (可配置概率)  
    - 随机搜索关键词并浏览搜索结果
    - 完整的统计信息输出
    
使用场景:
    - 抖音账号日常养号
    - 模拟真实用户行为
    - 提升账号活跃度
    
注意事项:
    - 需要设备已开启 USB 调试
    - 建议每次运行不超过 60 分钟
    - 点赞、关注概率不宜设置过高
    
作者：AI Agent Skills
版本：3.0 (简化版 - 仅养号功能)
日期：2026-03-17

使用说明:
    - 本脚本为简化版本，假设环境已配置完成
    - 虚拟环境已内置 uiautomator2，无需额外安装
    - 直接使用 Python 执行即可
    
重要提示:
    - 使用 WiFi 连接设备时，需先运行 adb connect 连接设备（需指定端口 5555）
    - 设备参数格式应为 IP:端口，例如：192.168.1.100:5555
    
示例命令:
    # 先连接设备（注意：必须指定端口号 5555）
    adb connect 192.168.1.100:5555
    
    # 再执行养号脚本
    python douyin_nurturing.py -d 192.168.1.100:5555
    python douyin_nurturing.py -d 192.168.1.100:5555 --seconds 1800 --like_prob 20
"""

# ==================== 导入依赖库 ====================
import random          # 随机数生成，用于概率控制
import subprocess      # subprocess 模块，用于执行 ADB 命令
import time            # 时间控制，用于延迟等待
import logging         # 日志模块，用于输出运行日志
import argparse        # 参数解析，用于命令行参数处理
from datetime import datetime  # 时间计算，用于运行时长统计
from pathlib import Path       # 路径处理，用于获取脚本目录

# 导入 uiautomator2 库
# 注意：虚拟环境中已内置 uiautomator2，无需额外安装
import uiautomator2 as u2

# ==================== 日志配置 ====================
# 配置日志输出格式和级别
logging.basicConfig(
    level=logging.INFO,  # 日志级别：INFO，输出所有重要信息
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # 时间格式
)
logger = logging  # 创建日志记录器

# ==================== 全局常量定义 ====================
# 抖音应用包名
DOUYIN_PACKAGE = "com.ss.android.ugc.aweme"

# 默认搜索关键词列表 (使用换行符分隔)
DEFAULT_KEYWORDS = "美食\n游戏\n娱乐"

# ==================== 抖音养号主类 ====================
class DouyinNurturing:
    """
    抖音养号主类
    
    功能:
        - 连接 Android 设备
        - 初始化设备设置
        - 执行养号任务 (浏览、点赞、关注、搜索)
        - 输出统计信息
    
    属性:
        screen_width (int): 设备屏幕宽度
        screen_height (int): 设备屏幕高度
        like_prob (float): 点赞概率 (0-1 之间)
        search_prob (float): 搜索概率 (0-1 之间)
        key_word (str): 搜索关键词列表
        collect_prob (float): 关注概率 (0-1 之间)
        seconds (int): 运行时长 (秒)
        deviceName (str): 设备名称
        adbPort (str): ADB 端口
        device: uiautomator2 设备对象
    """
    
    def __init__(self, **kwargs):
        """
        初始化养号参数
        
        参数:
            **kwargs: 可选参数包括:
                - like_prob: 点赞概率 (%), 默认 0.2%
                - searchProb: 搜索概率 (%), 默认 0.2%
                - keyWord: 搜索关键词，默认 "美食\n游戏\n娱乐"
                - collect_prob: 关注概率 (%), 默认 0.1%
                - seconds: 运行时长 (秒), 默认 600 秒 (10 分钟)
                - deviceName: 设备名称 (必填)
                - adbPort: ADB 端口，默认 "5037"
                - platformVersion: 平台版本
        """
        # 屏幕尺寸
        self.screen_width = None
        self.screen_height = None
        
        # 概率参数 (转换为 0-1 之间的小数)
        self.like_prob = kwargs.get("like_prob", 0.2) / 100
        self.search_prob = kwargs.get("searchProb", 0.2) / 100
        self.key_word = kwargs.get("keyWord", DEFAULT_KEYWORDS).replace("\\n", "\n")
        self.collect_prob = kwargs.get("collect_prob", 0.1) / 100
        
        # 运行参数
        self.seconds = kwargs.get("seconds", 60 * 10)  # 默认运行 10 分钟
        self.deviceName = kwargs.get("deviceName")
        self.adbPort = kwargs.get("adbPort", "5037")
        self.platformVersion = kwargs.get("platformVersion")
        
        # 设备对象
        self.device = None
        
        # 重试机制
        self.max_retries = 3
        self.failure_count = 0
        
        # 统计数据
        self.view_count = 0      # 浏览视频数
        self.like_count = 0      # 点赞数
        self.comment_count = 0   # 评论数
        self.follow_count = 0    # 关注数
        self.search_count = 0    # 搜索次数


    def find_element_by_multi(
            self,
            locators: list,
            set_wait: tuple = (False, 5),
            no_such_element_except: tuple = (False, "")
    ):
        """
        智能查找元素 - 支持多组定位器和自动重试
        
        功能说明:
            按顺序尝试多种定位方式查找元素，支持等待和异常处理
            使用 uiautomator2 的定位方法
            
        参数:
            locators (list): 多组定位器，每项为 (by, value) 元组
                           by 可以是："id", "description", "text", "className", "packageName"
                           例如：[("id", "xxx:2vh"), ("description", "搜索")]
            set_wait (tuple): 等待设置 (是否开启等待，等待时长秒数)，默认 (False, 5)
            no_such_element_except (tuple): 异常设置 (是否抛出异常，异常信息)，默认 (False, "")
            
        返回:
            element: 找到的元素对象，如果未找到则返回 None
            
        使用示例:
            # 查找搜索按钮（优先使用 ID，备用使用描述）
            search_btn = self.find_element_by_multi([
                ("id", f"{DOUYIN_PACKAGE}:id/2vh"),
                ("description", "搜索")
            ])
            if search_btn:
                search_btn.click()
            
            # 带等待的查找（最多等待 5 秒）
            element = self.find_element_by_multi([
                ("id", "xxx:id/target")
            ], set_wait=(True, 5))
        """
        # 参数验证
        if not locators or len(locators) == 0:
            logger.error("定位器列表不能为空")
            return None
            
        # 解析参数
        wait_visibility, wait_timeout = set_wait
        raise_exception, error_msg = no_such_element_except
        
        # 遍历所有定位器
        for i, (by, value) in enumerate(locators):
            try:
                logger.info(f"尝试定位元素 [{i+1}/{len(locators)}]: by={by}, value={value}")
                
                # 使用 uiautomator2 的定位方法
                element = None
                if by == "id":
                    element = self.device(resourceId=value)
                elif by == "description":
                    element = self.device(description=value)
                elif by == "text":
                    element = self.device(text=value)
                elif by == "className":
                    element = self.device(className=value)
                elif by == "packageName":
                    element = self.device(packageName=value)
                else:
                    logger.warning(f"不支持的定位方式：{by}")
                    continue
                
                # 检查元素是否存在
                if element and element.exists(timeout=3):
                    logger.info(f"元素定位成功 [尝试 {i+1} 次]")
                    return element
                
                # 如果未找到且开启了等待
                if not element and wait_visibility:
                    logger.info(f"元素未立即找到，等待最多 {wait_timeout} 秒...")
                    start_time = time.time()
                    while time.time() - start_time < wait_timeout:
                        if element.exists(timeout=1):
                            logger.info(f"等待成功，元素已可见")
                            return element
                        time.sleep(0.5)
                    logger.warning(f"等待元素超时")
                
                # 如果找到元素，直接返回
                if element:
                    logger.info(f"元素定位成功 [尝试 {i+1} 次]")
                    return element
                    
            except Exception as e:
                logger.warning(f"定位元素失败 [{i+1}/{len(locators)}]: {e}")
                # 继续尝试下一个定位器
                continue
        
        # 所有定位器都失败
        logger.warning(f"所有 {len(locators)} 种定位方式都未找到元素")
        
        # 根据参数决定是否抛出异常
        if raise_exception:
            error_message = error_msg if error_msg else f"未找到元素，已尝试 {len(locators)} 种定位方式"
            logger.error(error_message)
            raise Exception(error_message)  # 使用标准 Exception 替代 ProcessException
        
        return None

    def click_element_by_multi(
            self,
            locators: list,
            set_wait: tuple = (False, 5),
            timeout: int = 3
    ) -> bool:
        """
        智能点击元素 - 封装查找和点击操作
        
        功能说明:
            查找并点击元素，简化调用代码
            使用 uiautomator2 的定位方法
            
        参数:
            locators (list): 多组定位器，每项为 (by, value) 元组
                           by 可以是："id", "description", "text", "className", "packageName"
            set_wait (tuple): 等待设置 (是否开启等待，等待时长秒数)
            timeout (int): 元素存在性检查超时时间（秒）
            
        返回:
            bool: 点击成功返回 True，失败返回 False
            
        使用示例:
            # 点击搜索按钮
            clicked = self.click_element_by_multi([
                ("id", f"{DOUYIN_PACKAGE}:id/2vh"),
                ("description", "搜索")
            ])
            if clicked:
                logger.info("点击成功")
        """
        try:
            # 查找元素
            element = self.find_element_by_multi(locators, set_wait)
            
            # 检查元素是否存在
            if element and element.exists(timeout=timeout):
                element.click()
                logger.info("元素点击成功")
                return True
            else:
                logger.warning("元素不存在或不可点击")
                return False
                
        except Exception as e:
            logger.error(f"点击元素失败：{e}")
            return False

    def execute_adb_command(self, adb_command, timeout=10):
        """
        执行 ADB 命令 (静态方法)
        
        功能:
            通过 subprocess 执行 ADB 命令，并返回执行结果
            
        参数:
            adb_command (str): 完整的 ADB 命令字符串
            timeout (int): 命令执行超时时间 (秒), 默认 10 秒
            
        返回:
            tuple: (是否成功，输出内容)
                - 成功时返回 (True, stdout)
                - 失败时返回 (False, stderr)
                
        异常处理:
            - subprocess.TimeoutExpired: 命令执行超时
            - Exception: 其他执行异常
        """
        try:
            logger.info(f"执行 ADB 命令：{adb_command}")
            result = subprocess.run(
                adb_command,
                shell=True,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # 解码输出 (忽略编码错误)
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
            
            if result.returncode == 0:
                logger.info(f"命令执行成功")
                return True, stdout
            else:
                logger.error(f"命令执行失败：{stderr}")
                return False, stderr
        except subprocess.TimeoutExpired:
            logger.error("命令执行超时")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"执行异常：{e}")
            return False, str(e)

    def initialize_device_settings(self):
        """
        初始化设备设置 (简化版)
        
        功能说明:
            由于环境已预配置，此方法仅做最基本的设备设置
            所有优化设置已在虚拟环境中预设
            
        注意:
            - 本版本为简化版，不包含复杂的 ADB 配置
            - 所有必要的环境设置已在虚拟环境中完成
        """
        logger.info("设备设置已预配置，跳过复杂初始化")
        logger.info("开始连接设备...")

    def connect_device(self):
        """
        连接 Android 设备
        
        功能:
            使用 uiautomator2 连接指定的 Android 设备
            获取设备屏幕尺寸用于后续操作
            
        返回:
            bool: 连接成功返回 True，失败返回 False
            
        异常处理:
            捕获所有连接异常并记录日志
        """
        logger.info(f"尝试连接设备：{self.deviceName}")
        
        try:
            # 先尝试清理可能残留的服务（增强版）
            logger.info("检查并清理可能的残留服务...")
            self._force_cleanup_before_connect()
            
            # 使用 uiautomator2 连接设备
            self.device = u2.connect(self.deviceName)
            logger.info("设备连接成功")
            
            # 获取屏幕尺寸 (用于后续点击、滑动操作)
            self.screen_width, self.screen_height = self.get_window_size()
            logger.info(f"屏幕分辨率：{self.screen_width}x{self.screen_height}")
            
            return True
        except Exception as e:
            logger.error(f"设备连接失败：{e}")
            # 连接失败时尝试清理
            logger.info("连接失败，尝试清理服务...")
            self.cleanup_uiautomator_service()
            return False

    def _force_cleanup_before_connect(self):
        """
        连接前强制清理（增强版）
        
        功能:
            在连接设备前彻底清理所有可能的残留服务
            避免 UiAutomation 冲突
        """
        if not self.deviceName:
            return
            
        try:
            # 1. 强制停止所有 uiautomator 相关包
            packages = [
                "com.github.uiautomator",
                "com.github.uiautomator.test",
                "com.wetest.uia2",
                "androidx.test.uiautomator"
            ]
            
            logger.info("强制停止 uiautomator 相关进程...")
            for package in packages:
                try:
                    cmd = f"adb -s {self.deviceName} shell am force-stop {package}"
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        timeout=5,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if result.returncode == 0:
                        logger.debug(f"✓ 已停止 {package}")
                except Exception:
                    pass  # 忽略失败
            
            # 2. 清除 UiAutomation 设置
            try:
                cmd = f"adb -s {self.deviceName} shell settings put secure enabled_accessibility_services none"
                subprocess.run(cmd, shell=True, timeout=3,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug("✓ 已清除 UiAutomation 设置")
            except Exception:
                pass
            
            # 3. 等待服务完全停止
            logger.info("等待服务释放...")
            time.sleep(3)  # 增加等待时间，确保服务完全释放
            
            logger.info("✓ 连接前清理完成")
        except Exception as e:
            logger.warning(f"连接前清理失败：{e}")

    def run(self):
        """
        运行养号任务 (主入口 - 简化版)
        
        功能说明:
            1. 连接设备 (环境已预配置)
            2. 启动抖音应用
            3. 执行养号脚本
            4. 异常重试机制 (最多 3 次)
            
        简化说明:
            - 跳过复杂的环境检查
            - 直接使用预配置的环境
            - 专注于养号核心功能
            
        异常处理:
            - 设备连接失败：重试
            - 脚本执行异常：重试
            - 超过最大重试次数：抛出异常并退出
        """
        logger.info("=" * 50)
        logger.info("开始执行抖音养号任务 (简化版)")
        logger.info("环境已预配置，跳过环境检查")
        logger.info("=" * 50)
        
        # 设置 Ctrl+C 信号处理
        import signal
        
        def signal_handler(sig, frame):
            logger.warning("\n⚠  检测到 Ctrl+C 中断信号")
            logger.info("正在清理服务...")
            self.cleanup_uiautomator_service()
            logger.info("服务已清理，退出程序")
            import sys
            sys.exit(1)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        
        # 重试机制 (最多 3 次)
        while self.max_retries > 0:
            try:
                # 1. 连接设备 (环境已预配置)
                if not self.connect_device():
                    raise Exception("设备连接失败")
                
                # 短暂等待设备稳定
                time.sleep(2)
                
                # 2. 启动抖音应用
                logger.info("启动抖音应用...")
                self.device.app_start(DOUYIN_PACKAGE)
                time.sleep(8)  # 等待抖音启动完成
                logger.info("抖音应用已启动")
                
                # 3. 执行养号脚本
                logger.info("开始执行养号任务...")
                self.script()
                break  # 执行成功，退出重试循环
                
            except KeyboardInterrupt:
                # Ctrl+C 中断，已经由信号处理器处理
                raise
            except Exception as e:
                logger.error(f"发生异常：{e}")
                self.failure_count += 1
                self.max_retries -= 1
                
                if self.max_retries == 0:
                    logger.error("已达到最大重试次数，任务失败")
                    # 清理应用和服务
                    logger.info("清理应用和服务...")
                    self.cleanup_uiautomator_service()
                    # 断开设备连接
                    if self.device:
                        try:
                            self.device.disconnect()
                        except Exception:
                            pass
                    raise Exception("任务失败")
                else:
                    logger.info(f"重试中... 剩余重试次数：{self.max_retries}")
        
        logger.info("=" * 50)
        logger.info("养号任务结束")
        logger.info("=" * 50)

    def cleanup_uiautomator_service(self):
        """
        清理 uiautomator2 服务（Ctrl+C、异常或正常退出时调用）
        
        功能:
            1. 停止抖音应用
            2. 停止 uiautomator2 服务（使用官方 API）
            3. 释放 UiAutomation 资源
        """
        logger.info("正在清理应用和服务...")
        
        # 1. 停止抖音应用
        if self.device:
            try:
                logger.info("停止抖音应用...")
                self.device.app_stop(DOUYIN_PACKAGE)
                logger.info("✓ 抖音应用已停止")
            except Exception as e:
                logger.warning(f"停止抖音应用失败：{e}")
        
        # 2. 停止所有应用（可选，如果需要彻底清理）
        if self.device:
            try:
                logger.info("停止所有应用...")
                self.device.app_stop_all()
                logger.info("✓ 所有应用已停止")
            except Exception as e:
                logger.warning(f"停止所有应用失败：{e}")
        
        # 3. 停止 uiautomator2 服务（使用官方 API）
        if self.device:
            try:
                logger.info("停止 uiautomator2 服务...")
                # 使用官方推荐的方法：d.stop_uiautomator()
                self.device.stop_uiautomator()
                logger.info("✓ uiautomator 服务已停止 (stop_uiautomator)")
            except Exception as e:
                logger.warning(f"stop_uiautomator 失败：{e}")
        
        # 4. 强制停止 uiautomator 进程（ADB 备用方案，确保彻底清理）
        if self.deviceName:
            try:
                logger.info("强制停止 uiautomator 进程...")
                packages = [
                    "com.github.uiautomator",
                    "com.github.uiautomator.test",
                    "com.wetest.uia2",
                    "androidx.test.uiautomator"
                ]
                
                for package in packages:
                    try:
                        cmd = f"adb -s {self.deviceName} shell am force-stop {package}"
                        result = subprocess.run(
                            cmd, 
                            shell=True, 
                            timeout=5,
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE
                        )
                        if result.returncode == 0:
                            logger.info(f"✓ 已停止 {package} (ADB)")
                        else:
                            logger.debug(f"停止 {package} 返回码：{result.returncode}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"停止 {package} 超时")
                    except Exception as adb_error:
                        logger.debug(f"停止 {package} 失败：{adb_error}")
                
                logger.info("✓ 所有 uiautomator 进程已停止")
            except Exception as e:
                logger.debug(f"强制停止进程失败：{e}")
        
        # 5. 等待服务完全释放
        logger.info("等待服务释放...")
        time.sleep(2)
        
        logger.info("清理完成")

    def script(self):
        """
        养号主脚本 (核心逻辑)
        
        功能:
            1. 循环浏览推荐视频
            2. 随机执行搜索操作
            3. 随机点赞
            4. 随机关注
            5. 统计浏览数据
            
        流程:
            - 按时间循环执行 (直到达到设定时长)
            - 每次循环浏览一个视频
            - 根据概率触发搜索、点赞、关注
        """
        start_time = datetime.now()  # 记录开始时间
        logger.info("开始浏览抖音推荐页")
        logger.info(f"计划运行时长：{self.seconds}秒")

        # 主循环 (直到达到设定时长)
        while (datetime.now() - start_time).seconds < self.seconds:
            self.view_count += 1
            logger.info(f"正在浏览第 {self.view_count} 个视频")

            # 随机搜索 (根据概率触发)
            if random.random() < self.search_prob:
                logger.info("开始执行搜索操作")
                self.search_and_browse()

            # 滑动到下一个视频
            self.swipe_to_next()
            time.sleep(random.uniform(5, 10))  # 等待视频播放 (5-10 秒随机)
            
            # 随机点赞 (根据概率触发)
            if random.random() < self.like_prob:
                logger.info("随机执行点赞操作")
                if self.like_post():
                    self.like_count += 1
            
            # 随机关注 (根据概率触发)
            if random.random() < self.collect_prob:
                logger.info("随机执行关注操作")
                if self.follow_user():
                    self.follow_count += 1

        # 输出统计信息
        logger.info("养号任务完成，输出统计信息")
        self.print_statistics()
        self.normal_end()

    def search_and_browse(self):
        """
        搜索并浏览功能
        
        功能:
            1. 点击搜索按钮
            2. 输入随机关键词
            3. 查看搜索结果
            4. 浏览搜索结果中的视频
            5. 返回主页
            
        流程:
            - 多种方式定位搜索按钮 (ID / 描述)
            - 随机选择一个关键词
            - 搜索后切换到视频标签
            - 浏览 3-6 个搜索结果视频
            - 随机点赞搜索结果
            - 按 4 次返回键回到主页
        """
        try:
            # 1. 点击搜索按钮 - 使用智能点击封装方法
            search_clicked = self.click_element_by_multi([
                ("id", f"{DOUYIN_PACKAGE}:id/2vh"),
                ("description", "搜索")
            ], set_wait=(True, 3))
            
            if search_clicked:
                logger.info("点击搜索按钮成功")
            else:
                logger.warning("未找到搜索按钮，跳过本次搜索")
                return
            
            # 等待搜索页面加载
            time.sleep(2)
            
            # 2. 输入随机关键词
            keyword_list = self.key_word.split("\n")
            keyword_list.append("")  # 添加空字符串避免总是搜索
            search_word = random.choice(keyword_list)
            
            if search_word != "":
                logger.info(f"正在搜索：{search_word}")
                
                # 3. 查找搜索输入框
                try:
                    search_input = self.device(className="android.widget.EditText")
                    if search_input.exists(timeout=3):
                        search_input.set_text(search_word)
                        time.sleep(random.randint(2, 4))  # 等待输入完成
                        
                        # 4. 按下回车键执行搜索
                        self.device.press("enter")
                        time.sleep(random.randint(5, 10))  # 等待搜索结果加载
                        
                        # 5. 切换到视频标签
                        try:
                            video_tab = self.device(text="视频")
                            if video_tab.exists(timeout=3):
                                video_tab.click()
                                time.sleep(random.randint(5, 10))
                        except Exception:
                            logger.warning("未找到视频标签，使用默认结果")
                        
                        # 6. 浏览搜索结果 (随机 3-6 个视频)
                        swipe_times = random.randint(3, 6)
                        for i in range(swipe_times):
                            time.sleep(3)
                            self.swipe_to_next()
                            logger.info(f"浏览搜索结果视频 {i+1}/{swipe_times}")
                            
                            # 随机点赞搜索结果
                            if random.random() < self.like_prob:
                                if self.like_post():
                                    self.like_count += 1
                        
                        self.search_count += 1  # 搜索次数 +1
                        
                except Exception as e:
                    logger.error(f"搜索输入失败：{e}")
            
            # 7. 返回主页 (按 4 次返回键)
            logger.info("返回主页...")
            for _ in range(4):
                self.device.press("back")
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"搜索操作失败：{e}")

    def swipe_to_next(self):
        """
        滑动到下一个视频
        
        功能:
            模拟用户从屏幕底部向上滑动，切换到下一个视频
            
        滑动参数:
            - 起点：屏幕水平居中，垂直 80% 高度 (底部)
            - 终点：屏幕水平居中，垂直 20% 高度 (顶部)
            - 滑动时间：0.5 秒 (模拟自然滑动)
        """
        try:
            logger.info("滑动到下一个视频...")
            # 执行滑动操作
            self.device.swipe(
                self.screen_width / 2,           # 起点 X: 屏幕水平居中
                self.screen_height * 0.8,        # 起点 Y: 屏幕底部 80%
                self.screen_width / 2,           # 终点 X: 屏幕水平居中
                self.screen_height * 0.2,        # 终点 Y: 屏幕顶部 20%
                0.5                              # 滑动时间：0.5 秒
            )
            logger.info("滑动成功")
        except Exception as e:
            logger.error(f"滑动失败：{e}")

    def get_window_size(self):
        """
        获取设备窗口大小
        
        功能:
            通过 uiautomator2 获取设备屏幕分辨率
            
        返回:
            tuple: (宽度，高度)
                - 成功时返回实际分辨率
                - 失败时返回默认值 (1080, 1920)
        """
        try:
            size = self.device.window_size()
            return size[0], size[1]
        except Exception as e:
            logger.error(f"获取窗口大小失败：{e}")
            return 1080, 1920  # 返回默认分辨率

    def like_post(self):
        """
        点赞视频
        
        功能:
            通过双击屏幕中央区域模拟点赞操作
            (抖音的双击点赞功能)
            
        返回:
            bool: 点赞成功返回 True，失败返回 False
        """
        try:
            # 计算屏幕中央坐标
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            
            # 双击屏幕中央 (抖音的双击点赞手势)
            self.device.double_click(center_x, center_y)
            time.sleep(1)  # 等待点赞动画
            
            logger.info("点赞成功 (双击屏幕)")
            return True
        except Exception as e:
            logger.error(f"点赞失败：{e}")
            return False

    def follow_user(self):
        """
        关注用户
            
        功能:
            尝试点击关注按钮（通常在视频右侧用户头像附近）
            使用智能元素定位封装方法
                
        定位方式:
            1. 使用资源 ID 定位（优先级高）
            2. 使用文本"关注"定位（备用方案）
                
        返回:
            bool: 关注成功返回 True，失败返回 False
        """
        try:
            # 使用智能点击封装方法
            clicked = self.click_element_by_multi([
                ("id", f"{DOUYIN_PACKAGE}:id/d-c"),
                ("text", "关注")
            ], set_wait=(True, 3), timeout=3)
                
            if clicked:
                time.sleep(1)  # 等待关注动画
                logger.info("关注成功")
                return True
            else:
                logger.info("未找到关注按钮")
                return False
                    
        except Exception as e:
            logger.error(f"关注失败：{e}")
            return False

    def print_statistics(self):
        """
        打印统计信息
        
        功能:
            输出本次养号任务的详细统计数据
            包括：浏览数、点赞数、关注数、搜索次数等
        """
        logger.info("=" * 50)
        logger.info("养号任务统计:")
        logger.info("=" * 50)
        logger.info(f"浏览视频总数：{self.view_count}")
        logger.info(f"点赞数量：{self.like_count}")
        logger.info(f"关注数量：{self.follow_count}")
        logger.info(f"搜索次数：{self.search_count}")
        logger.info(f"评论数量：{self.comment_count}")
        logger.info("=" * 50)

    def normal_end(self):
        """
        正常结束任务
        
        功能:
            1. 返回主页
            2. 停止抖音应用
            3. 停止 uiautomator 服务
            4. 断开设备连接
            5. 清理资源
        """
        logger.info("开始结束流程...")
        try:
            time.sleep(random.randint(0, 5))  # 随机等待 0-5 秒
            
            # 1. 返回主页
            logger.info("返回主页...")
            if self.device:
                self.device.press("home")
                time.sleep(2)
            
            # 2. 清理应用和服务
            logger.info("清理应用和服务...")
            self.cleanup_uiautomator_service()
            
                
        except Exception as e:
            logger.error(f"结束操作失败：{e}")


# ==================== 主函数 ====================
def main():
    """
    主函数：解析命令行参数并执行养号任务
    
    功能说明:
        本函数负责解析用户输入的命令行参数，创建养号对象并执行任务
        
    必填参数:
        -d/--deviceName: 设备名称 (如：192.168.1.100:5555) [必须提供]
        
    常用可选参数:
        --seconds: 运行秒数 (默认 600 秒 = 10 分钟)
        --like_prob: 点赞概率 (%) (默认 10%)
        --collect_prob: 关注概率 (%) (默认 10%)
        --searchProb: 搜索概率 (%) (默认 80%)
        --keyWord: 搜索关键词 (多个用\\n 分隔)
        
    其他参数:
        -accountId: 目标账号 ID (默认"000")
        -job_id: 任务 ID (可选)
        -a/--adbPort: ADB 端口 (默认"5037")
        -ver/--platformVersion: 平台版本 (可选)
        -v/--variables: 目标变量 (可选)
    
    使用示例:
        # 先连接设备（WiFi，注意必须指定端口 5555）
        adb connect 192.168.1.100:5555
        
        # 基础用法 - 使用默认参数运行 10 分钟
        python douyin_nurturing.py -d 192.168.1.100:5555
        
        # 运行 30 分钟，点赞概率 20%
        python douyin_nurturing.py -d 192.168.1.100:5555 --seconds 1800 --like_prob 20
        
        # 自定义搜索关键词
        python douyin_nurturing.py -d 192.168.1.100:5555 --keyWord "美食\\n 旅游\\n 健身"
        
        # 完整参数示例
        python douyin_nurturing.py -d 192.168.1.100:5555 -a 5037 --seconds 1800 \\
            --like_prob 20 --collect_prob 10 --searchProb 80 \\
            --keyWord "美食\\n 游戏\\n 娱乐"
    
    注意事项:
        - 环境已预配置，无需安装额外依赖
        - 确保设备已开启 USB 调试并已连接（WiFi）
        - 建议首次运行时使用默认参数测试
        - 运行时间不宜超过 60 分钟
        - 使用 WiFi 连接时，设备格式应为 IP:端口
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='抖音养号自动化脚本 (简化版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
===========================================
使用示例:
  # 先连接设备（WiFi，注意必须指定端口 5555）
  adb connect 192.168.1.100:5555
  
  # 基础用法 - 使用默认参数运行 10 分钟
  python douyin_nurturing.py -d 192.168.1.100:5555
  
  # 运行 30 分钟，点赞概率 20%
  python douyin_nurturing.py -d 192.168.1.100:5555 --seconds 1800 --like_prob 20
  
  # 自定义搜索关键词
  python douyin_nurturing.py -d 192.168.1.100:5555 --keyWord "美食\\n 旅游\\n 健身"
  
  # 查看完整帮助信息
  python douyin_nurturing.py --help
===========================================
        """
    )
    
    # 添加参数
    parser.add_argument(
        '-accountId', 
        '--accountId', 
        dest='accountId', 
        type=str, 
        default="000", 
        help='目标账号 ID (默认：000)'
    )
    parser.add_argument(
        '-j', 
        '--job_id', 
        dest='job_id', 
        type=str, 
        default=None, 
        help='任务 ID (可选)'
    )
    parser.add_argument(
        '-d', 
        '--deviceName', 
        dest='deviceName', 
        type=str, 
        required=True, 
        help='设备名称 (必填，如：192.168.1.100:5555)'
    )
    parser.add_argument(
        '-a', 
        '--adbPort', 
        dest='adbPort', 
        type=str, 
        default='5037', 
        help='ADB 端口 (默认：5037)'
    )
    parser.add_argument(
        '-ver', 
        '--platformVersion', 
        dest='platformVersion', 
        type=str, 
        default=None, 
        help='平台版本 (可选)'
    )
    parser.add_argument(
        '-v', 
        '--variables', 
        dest='variables', 
        type=str, 
        default='{}', 
        help='目标变量 (默认：{})'
    )
    parser.add_argument(
        '-seconds', 
        '--seconds', 
        dest='seconds', 
        type=int, 
        default=600, 
        help='运行秒数 (默认：600 秒 = 10 分钟)'
    )
    parser.add_argument(
        '-like_prob', 
        '--like_prob', 
        type=float, 
        default=10, 
        help='点赞概率 (%%)，默认 10%%'
    )
    parser.add_argument(
        '-collect_prob', 
        '--collect_prob', 
        type=float, 
        default=10, 
        help='关注概率 (%%)，默认 10%%'
    )
    parser.add_argument(
        '-searchProb', 
        '--searchProb', 
        type=float, 
        default=80, 
        help='搜索概率 (%%)，默认 80%%'
    )
    parser.add_argument(
        '-keyWord', 
        '--keyWord', 
        type=str, 
        default="美食\n游戏\n娱乐", 
        help='搜索关键词 (多个用\\n分隔，默认：美食\\n 游戏\\n娱乐)'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 创建养号对象并运行
    logger.info("创建养号任务对象...")
    nurturing = DouyinNurturing(**vars(args))
    
    # 执行任务
    nurturing.run()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 运行主函数
    main()
