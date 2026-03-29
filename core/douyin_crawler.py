"""
抖音爬虫核心逻辑 - 精简版
去除容错处理，保留清晰的爬虫主干逻辑
"""

import re
import os
import requests
from urllib.parse import quote
from util.abogus import ABogus
from util.xbogus import XBogus


def _load_cookie(cookie_file: str = "cookie.txt") -> str:
    """从文件加载 Cookie"""
    if not os.path.exists(cookie_file):
        return ""
    
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie = f.read().strip()
    
    if not cookie:
        print(f"警告：{cookie_file} 文件为空")
    return cookie


def _sanitize_filename(filename: str, max_length: int = 100) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换 Windows 和 Unix 的非法字符
    illegal_chars = r'[<>"/\\|?*:\n\r\t]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点
    filename = filename.strip(' .')
    
    # 限制长度
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    # 如果为空，返回默认名称
    if not filename:
        filename = "untitled"
    
    return filename


def _get_unique_path(base_path: str) -> str:
    """获取唯一的文件路径，处理重名"""
    if not os.path.exists(base_path):
        return base_path
    
    # 分离路径和扩展名
    dir_name = os.path.dirname(base_path)
    file_name = os.path.basename(base_path)
    name, ext = os.path.splitext(file_name)
    
    # 尝试添加序号
    counter = 1
    while True:
        new_name = f"{name}_{counter:03d}{ext}"
        new_path = os.path.join(dir_name, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1
        # 防止无限循环
        if counter > 999:
            import time
            timestamp = int(time.time())
            new_name = f"{name}_{timestamp}{ext}"
            return os.path.join(dir_name, new_name)


class DouyinCrawler:
    """抖音爬虫核心类"""
    
    def __init__(self, cookie: str = "", cookie_file: str = "cookie.txt"):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        
        # 优先级：传入的 cookie > cookie 文件 > 空
        if cookie:
            self.cookie = cookie
        else:
            self.cookie = _load_cookie(cookie_file)
        
        self.download_dir = "downloads"
        self.max_pages = 1
    
    @classmethod
    def from_cookie_file(cls, cookie_file: str = "cookie.txt"):
        """从 Cookie 文件创建爬虫实例"""
        return cls(cookie_file=cookie_file)

    def get_resource_id(self, share_url: str) -> str:
        """从分享链接提取视频 ID（保留完整正则匹配项）"""
        # 提取 URL（支持多种格式）
        url_patterns = [
            r'https?://[^\s]+',
            r'v\.douyin\.com/[^\s]+',
            r'douyin\.com/video/\d+',
            r'douyin\.com/aweme/detail/\d+',
        ]
        
        extracted_url = None
        for pattern in url_patterns:
            match = re.search(pattern, share_url)
            if match:
                extracted_url = match.group(0)
                if not extracted_url.startswith('http'):
                    extracted_url = 'https://' + extracted_url
                break
        
        if not extracted_url:
            extracted_url = share_url.strip()
        
        # 直接从 URL 提取 ID（支持多种格式）
        patterns = [
            r'/video/(\d+)',
            r'/aweme/detail/(\d+)',
            r'/note/(\d+)',
            r'video_id=(\d+)',
            r'aweme_id=(\d+)',
            r'note_id=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, extracted_url)
            if match:
                return match.group(1)
        
        # 通过重定向获取真实 URL
        resp = requests.get(extracted_url, allow_redirects=True, timeout=15)
        for pattern in patterns:
            match = re.search(pattern, resp.url)
            if match:
                return match.group(1)
        
        # 从 HTML 提取（尝试多种字段名）
        id_patterns = [
            r'"aweme_id":"(\d+)"',
            r'"itemId":"(\d+)"',
            r'"video_id":"(\d+)"',
            r'"note_id":"(\d+)"',
            r'/video/(\d+)',
            r'/aweme/detail/(\d+)',
            r'/note/(\d+)',
            r'aweme_id=(\d+)',
            r'video_id=(\d+)',
            r'note_id=(\d+)',
        ]
        for pattern in id_patterns:
            match = re.search(pattern, resp.text)
            if match:
                video_id = match.group(1)
                if video_id.isdigit() and len(video_id) >= 15:
                    return video_id
        
        raise ValueError(f"无法从链接提取视频 ID: {extracted_url}")

    def _request_json(self, api_url: str, params: dict, headers: dict) -> dict | None:
        """请求 API 并返回 JSON（支持 a_bogus 和 X-Bogus 双签名）"""
        # 先试 a_bogus
        try:
            a_bogus = ABogus().get_value(params)
            params["a_bogus"] = quote(a_bogus, safe="")
            resp = requests.get(api_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                return resp.json()
        except Exception:
            pass
        
        # 再试 X-Bogus
        try:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            xb_value = XBogus(self.user_agent).getXBogus(param_str)
            xb_url = f"{api_url}?{param_str}&X-Bogus={xb_value[1]}"
            resp = requests.get(xb_url, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                return resp.json()
        except Exception:
            pass
        
        return None

    def get_aweme_detail(self, video_id: str) -> dict:
        """获取作品详情（支持 a_bogus 和 X-Bogus 双签名）"""
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": video_id,
            "pc_client_type": "1",
            "version_code": "290100",
            "version_name": "29.1.0",
            "cookie_enabled": "true",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "130.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "130.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "platform": "PC",
            "msToken": "",
        }
        
        headers = {
            "User-Agent": self.user_agent,
            "Referer": f"https://www.douyin.com/video/{video_id}",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        
        api_url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
        
        # 使用 a_bogus 签名请求
        result = self._request_json(api_url, params, headers)
        if result and "aweme_detail" in result:
            return result
        
        # 如果失败，尝试 note 链接的 referer
        headers["Referer"] = f"https://www.douyin.com/note/{video_id}"
        result = self._request_json(api_url, params, headers)
        if result and "aweme_detail" in result:
            return result
        
        raise ValueError("API 请求失败：a_bogus 和 X-Bogus 签名均无效，可能需要更新 Cookie 或签名算法")

    def _extract_video_info(self, data: dict) -> dict:
        """提取单个视频信息"""
        aweme = data["aweme_detail"]
        video = aweme["video"]
        
        # 提取最高画质视频地址
        bit_rate_list = video.get("bit_rate") or []
        if bit_rate_list:
            bit_rate_list.sort(key=lambda x: x.get("bit_rate", 0), reverse=True)
            for br in bit_rate_list:
                play_addr = br.get("play_addr", {})
                url_list = play_addr.get("url_list", [])
                if url_list:
                    play_url = url_list[0].replace("playwm", "play")
                    break
            else:
                play_addr = video["play_addr"]
                url_list = play_addr.get("url_list", [])
                play_url = url_list[0].replace("playwm", "play")
        else:
            play_addr = video["play_addr"]
            url_list = play_addr.get("url_list", [])
            play_url = url_list[0].replace("playwm", "play")
        
        # 提取封面
        cover = video.get("cover") or {}
        cover_list = cover.get("url_list") or []
        cover_url = cover_list[0] if cover_list else None
        
        # 提取作者信息
        author = aweme["author"]
        
        return {
            "aweme_id": aweme["aweme_id"],
            "desc": aweme["desc"],
            "create_time": aweme["create_time"],
            "author_id": author.get("uid", author.get("sec_uid", "unknown")),
            "author_nickname": author["nickname"],
            "author_sec_uid": author["sec_uid"],
            "cover_url": cover_url,
            "play_url": play_url,
            "content_type": "video",
        }

    def _extract_image_info(self, data: dict) -> dict:
        """提取图集信息"""
        aweme = data["aweme_detail"]
        images = aweme.get("images") or []
        
        # 提取图片 URLs
        image_urls = []
        for img in images:
            if not isinstance(img, dict):
                continue
            
            url_list = img.get("url_list") or []
            if url_list:
                image_urls.append(url_list[0])
                continue
            
            download_list = img.get("download_url_list") or []
            if download_list:
                image_urls.append(download_list[0])
        
        # 提取作者信息
        author = aweme["author"]
        
        # 提取封面（使用第一张图片）
        preview_url = image_urls[0] if image_urls else None
        
        return {
            "aweme_id": aweme["aweme_id"],
            "desc": aweme["desc"],
            "create_time": aweme["create_time"],
            "author_id": author.get("uid", author.get("sec_uid", "unknown")),
            "author_nickname": author["nickname"],
            "author_sec_uid": author["sec_uid"],
            "cover_url": preview_url,
            "image_urls": image_urls,
            "image_count": len(image_urls),
            "content_type": "image",
        }

    def parse_video(self, share_url: str) -> dict:
        """解析单个视频"""
        video_id = self.get_resource_id(share_url)
        data = self.get_aweme_detail(video_id)
        return self._extract_video_info(data)

    def parse_image(self, share_url: str) -> dict:
        """解析图集"""
        video_id = self.get_resource_id(share_url)
        data = self.get_aweme_detail(video_id)
        return self._extract_image_info(data)

    def parse(self, share_url: str) -> dict:
        """智能解析（自动识别视频或图集）"""
        video_id = self.get_resource_id(share_url)
        data = self.get_aweme_detail(video_id)
        
        # 判断内容类型
        aweme = data.get("aweme_detail") or {}
        aweme_type = aweme.get("aweme_type", 0)
        
        if aweme_type in (0, 4):
            return self._extract_video_info(data)
        elif aweme_type in (2, 68) or aweme.get("images"):
            return self._extract_image_info(data)
        else:
            # 默认按视频处理
            return self._extract_video_info(data)

    def get_sec_uid(self, user_url: str) -> str:
        """从用户链接提取 sec_uid（支持短链接跳转）"""
        # 提取 URL
        url_patterns = [
            r'https?://[^\s]+',
            r'douyin\.com/user/[^\s]+',
        ]
        
        extracted_url = None
        for pattern in url_patterns:
            match = re.search(pattern, user_url)
            if match:
                extracted_url = match.group(0)
                if not extracted_url.startswith('http'):
                    extracted_url = 'https://' + extracted_url
                break
        
        if not extracted_url:
            extracted_url = user_url.strip()
        
        # 尝试多种匹配模式
        patterns = [
            r"/user/([^/?\s]+)",
            r"sec_uid=([^&\s]+)",
            r"user/([^/?\s]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, extracted_url)
            if match:
                return match.group(1)
        
        # 如果是短链接，尝试跳转获取真实 URL
        if 'v.douyin.com' in extracted_url:
            try:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
                if self.cookie:
                    headers["Cookie"] = self.cookie
                
                resp = requests.get(extracted_url, headers=headers, allow_redirects=True, timeout=10)
                final_url = resp.url
                
                # 从最终 URL 提取 sec_uid
                for pattern in patterns:
                    match = re.search(pattern, final_url)
                    if match:
                        return match.group(1)
                    
                # 从响应内容中提取
                for pattern in patterns:
                    match = re.search(pattern, resp.text)
                    if match:
                        return match.group(1)
            except Exception as e:
                print(f"短链接跳转失败: {e}")
        
        raise ValueError(f"无法从用户链接提取 sec_uid: {extracted_url}")

    def get_user_videos(self, sec_uid: str, max_pages: int = 1) -> list[str]:
        """获取用户作品链接列表"""
        headers = {
            "User-Agent": self.user_agent,
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        
        api_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
        max_cursor = 0
        video_urls = []
        
        for _ in range(max_pages):
            params = {
                "device_platform": "webapp",
                "aid": "6383",
                "channel": "channel_pc_web",
                "sec_user_id": sec_uid,
                "max_cursor": str(max_cursor),
                "count": "20",
                "locate_query": "false",
                "show_live_replay_strategy": "1",
                "need_time_list": "1",
                "time_list_query": "0",
                "whale_cut_token": "",
                "cut_version": "1",
                "publish_video_strategy_type": "2",
                "pc_client_type": "1",
                "version_code": "290100",
                "version_name": "29.1.0",
                "cookie_enabled": "true",
                "screen_width": "1920",
                "screen_height": "1080",
                "browser_language": "zh-CN",
                "browser_platform": "Win32",
                "browser_name": "Chrome",
                "browser_version": "130.0.0.0",
                "browser_online": "true",
                "engine_name": "Blink",
                "engine_version": "130.0.0.0",
                "os_name": "Windows",
                "os_version": "10",
                "cpu_core_num": "12",
                "device_memory": "8",
                "platform": "PC",
                "downlink": "10",
                "effective_type": "4g",
                "round_trip_time": "50",
                "msToken": "",
            }
            
            data = self._request_json(api_url, params, headers)
            if not data:
                continue
            
            aweme_list = data["aweme_list"]
            for aweme in aweme_list:
                video_urls.append(f"https://www.douyin.com/video/{aweme['aweme_id']}")
            
            if not data["has_more"]:
                break
            max_cursor = data["max_cursor"]
        
        return video_urls

    def parse_user_home(self, user_url: str, max_pages: int = 1) -> list[str]:
        """解析用户主页，返回作品链接列表"""
        sec_uid = self.get_sec_uid(user_url)
        return self.get_user_videos(sec_uid, max_pages)

    def parse_user_home_detail(self, user_url: str, max_pages: int = 1) -> list[dict]:
        """解析用户主页，返回详细作品信息"""
        sec_uid = self.get_sec_uid(user_url)
        video_urls = self.get_user_videos(sec_uid, max_pages)
        
        # 解析每个作品的详细信息
        details = []
        for url in video_urls:
            try:
                result = self.parse(url)
                details.append(result)
            except Exception:
                continue
        
        return details

    def _get_download_headers(self, referer: str = "https://www.douyin.com/") -> dict:
        """获取下载请求头（完整的浏览器特征）"""
        headers = {
            "User-Agent": self.user_agent,
            "Referer": referer,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Priority": "u=1, i",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def download_file(self, url: str, save_path: str, show_progress: bool = True) -> bool:
        """下载单个文件（视频或图片）"""
        try:
            headers = self._get_download_headers()
            
            # 使用 stream 模式下载大文件
            resp = requests.get(url, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()
            
            # 获取文件总大小
            total_size = int(resp.headers.get('content-length', 0))
            
            # 确保目录存在
            dir_path = os.path.dirname(save_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # 写入文件
            downloaded_size = 0
            with open(save_path, 'wb') as f:
                if show_progress and total_size > 0:
                    # 使用 tqdm 显示进度条
                    from tqdm import tqdm
                    with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=os.path.basename(save_path)) as pbar:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
            
            if downloaded_size == 0:
                print(f"警告：下载的文件为空：{save_path}")
                return False
            
            return True
        except requests.exceptions.RequestException as e:
            print(f"下载失败（网络错误）：{url}, 错误：{e}")
            return False
        except Exception as e:
            print(f"下载失败：{url}, 错误：{e}")
            return False

    def download_video(self, share_url: str, output_dir: str = None, group_by_user: bool = False) -> str | None:
        """下载单个视频
        
        Args:
            share_url: 视频分享链接
            output_dir: 输出目录
            group_by_user: 是否按用户分组（批量下载时使用）
        """
        result = self.parse_video(share_url)
        
        if result['content_type'] != 'video':
            raise ValueError("该链接不是视频")
        
        video_url = result['play_url']
        
        # 使用视频描述作为文件名
        desc = result.get('desc', '')
        if desc:
            filename = _sanitize_filename(desc) + ".mp4"
        else:
            filename = f"video_{result['aweme_id']}.mp4"
        
        # 使用配置文件中的默认目录
        if output_dir is None:
            output_dir = self.download_dir
        
        # 按用户分组（仅批量下载时启用）
        if group_by_user:
            author_nickname = result.get('author_nickname', 'unknown')
            author_sec_uid = result.get('author_sec_uid', '')
            user_id_short = author_sec_uid[-8:] if len(author_sec_uid) >= 8 else author_sec_uid
            user_folder = f"{_sanitize_filename(author_nickname, max_length=40)}_{user_id_short}"
            video_dir = os.path.join(output_dir, user_folder, "视频")
        else:
            video_dir = output_dir
        
        save_path = os.path.join(video_dir, filename)
        
        # 处理重名
        save_path = _get_unique_path(save_path)
        
        # 直接使用解析出来的 URL 下载
        if self.download_file(video_url, save_path):
            print(f"视频已下载：{save_path}")
            return save_path
        return None

    def download_image(self, share_url: str, output_dir: str = None, group_by_user: bool = False) -> list[str]:
        """下载图集所有图片
        
        Args:
            share_url: 图集分享链接
            output_dir: 输出目录
            group_by_user: 是否按用户分组（批量下载时使用）
        """
        result = self.parse_image(share_url)
        
        if result['content_type'] != 'image':
            raise ValueError("该链接不是图集")
        
        image_urls = result['image_urls']
        
        # 使用图集描述作为文件夹名
        desc = result.get('desc', '')
        if desc:
            folder_name = _sanitize_filename(desc, max_length=50)
        else:
            folder_name = f"album_{result['aweme_id']}"
        
        # 使用配置文件中的默认目录
        if output_dir is None:
            output_dir = self.download_dir
        
        # 按用户分组（仅批量下载时启用）
        if group_by_user:
            author_nickname = result.get('author_nickname', 'unknown')
            author_sec_uid = result.get('author_sec_uid', '')
            user_id_short = author_sec_uid[-8:] if len(author_sec_uid) >= 8 else author_sec_uid
            user_folder = f"{_sanitize_filename(author_nickname, max_length=40)}_{user_id_short}"
            image_base_dir = os.path.join(output_dir, user_folder, "图集")
        else:
            image_base_dir = output_dir
        
        # 创建图集目录（处理重名）
        album_dir = os.path.join(image_base_dir, folder_name)
        album_dir = _get_unique_path(album_dir)
        os.makedirs(album_dir, exist_ok=True)
        
        # 直接使用解析出来的 URL 下载
        downloaded = []
        for i, img_url in enumerate(image_urls, 1):
            filename = f"{i:03d}.jpg"
            save_path = os.path.join(album_dir, filename)
            
            if self.download_file(img_url, save_path):
                downloaded.append(save_path)
                print(f"图片 {i}/{len(image_urls)} 已下载：{save_path}")
        
        return downloaded

    def download(self, share_url: str, output_dir: str = None) -> list[str]:
        """智能下载（自动识别视频或图集）"""
        result = self.parse(share_url)
        
        if output_dir is None:
            output_dir = self.download_dir
        
        if result['content_type'] == 'video':
            path = self.download_video(share_url, output_dir)
            return [path] if path else []
        elif result['content_type'] == 'image':
            return self.download_image(share_url, output_dir)
        else:
            raise ValueError("未知内容类型")

    def download_user_videos(self, user_url: str, max_pages: int = None, output_dir: str = None) -> list[str]:
        """批量下载用户所有作品"""
        if max_pages is None:
            max_pages = self.max_pages
        if output_dir is None:
            output_dir = self.download_dir
        
        details = self.parse_user_home_detail(user_url, max_pages)
        
        downloaded = []
        for i, item in enumerate(details, 1):
            print(f"\n[{i}/{len(details)}] 下载 {item['content_type']} - {item['desc'][:20]}...")
            
            try:
                if item['content_type'] == 'video':
                    video_url = f"https://www.douyin.com/video/{item['aweme_id']}"
                    # 批量下载时启用用户分组
                    path = self.download_video(video_url, output_dir, group_by_user=True)
                    if path:
                        downloaded.append(path)
                elif item['content_type'] == 'image':
                    image_url = f"https://www.douyin.com/note/{item['aweme_id']}"
                    # 批量下载时启用用户分组
                    paths = self.download_image(image_url, output_dir, group_by_user=True)
                    downloaded.extend(paths)
            except Exception as e:
                print(f"下载失败：{e}")
                continue
        
        print(f"\n下载完成！共下载 {len(downloaded)} 个文件")
        return downloaded
