import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CrawlerRequest:
    """简洁的爬虫请求类，专注于核心功能"""
    
    def __init__(self, 
                 headers: Optional[Dict[str, str]] = None,
                 min_sleep: float = 1.0,
                 max_sleep: float = 3.0,
                 max_retries: int = 3,
                 timeout: int = 60,
                 max_workers: int = 3):
        """
        初始化爬虫请求类
        
        Args:
            headers: 请求头
            min_sleep: 最小睡眠时间（秒）
            max_sleep: 最大睡眠时间（秒）
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
            max_workers: 最大并发工作线程数
        """
        self.session = self._create_session()
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_workers = max_workers
        
        # 设置请求头
        if headers:
            self.session.headers.update(headers)
        
        # 重新配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 请求统计
        self.request_count = 0
        self.success_count = 0
    
    def _create_session(self) -> requests.Session:
        """创建并配置请求会话"""
        session = requests.Session()
        
        # 配置重试策略（使用默认值，后续在__init__中重新配置）
        retry_strategy = Retry(
            total=3,  # 默认值
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def set_cookies(self, cookies: Dict[str, str]) -> None:
        """设置会话Cookie"""
        self.session.cookies.update(cookies)
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """设置请求头"""
        self.session.headers.update(headers)
    
    def random_sleep(self) -> None:
        """随机睡眠"""
        sleep_time = random.uniform(self.min_sleep, self.max_sleep)
        logger.debug(f"随机睡眠 {sleep_time:.2f} 秒...")
        time.sleep(sleep_time)
    
    def rotate_user_agent(self) -> None:
        """轮换User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
        ]
        
        new_ua = random.choice(user_agents)
        self.session.headers['User-Agent'] = new_ua
        logger.debug(f"轮换User-Agent: {new_ua}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送请求的通用方法"""
        self.random_sleep()
        # if random.random() < 0.3:
        #     self.rotate_user_agent()
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = getattr(self.session, method.lower())(url, **kwargs)
            response.raise_for_status()
            
            self.request_count += 1
            self.success_count += 1
            
            return response
            
        except requests.RequestException as e:
            self.request_count += 1
            logger.error(f"{method}请求失败: {url}, 错误: {e}")
            raise
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """发送GET请求"""
        return self._make_request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """发送POST请求"""
        return self._make_request('POST', url, **kwargs)
    
    def download_file(self, url: str, file_path: str, chunk_size: int = 8192) -> bool:
        """下载文件到本地"""
        try:
            response = self.get(url, stream=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"文件下载成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"文件下载失败: {url}, 错误: {e}")
            return False
    
    def download_files_batch(self, url_file_pairs: List[tuple]) -> Dict[str, bool]:
        """批量下载文件"""
        results = {}
        
        def download_single(args):
            url, file_path = args
            success = self.download_file(url, file_path)
            return file_path, success
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(download_single, pair): pair[1] 
                            for pair in url_file_pairs}
            
            for future in as_completed(future_to_file):
                file_path, success = future.result()
                results[file_path] = success
        
        return results
    
    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """发送GET请求并返回JSON数据"""
        response = self.get(url, **kwargs)
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        return {
            'total_requests': self.request_count,
            'successful_requests': self.success_count,
            'failed_requests': self.request_count - self.success_count,
            'success_rate': success_rate
        }
    
    def close(self) -> None:
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 