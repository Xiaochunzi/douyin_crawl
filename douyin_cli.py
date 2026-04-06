#!/usr/bin/env python3
"""
抖音下载器 CLI 工具
支持视频、图集、用户主页和合集批量下载
"""

import argparse
import sys
import os
from core.douyin_crawler import DouyinCrawler


def download_single(crawler: DouyinCrawler, url: str, output_dir: str):
    """下载单个视频或图集"""
    try:
        result = crawler.parse(url)
        content_type = result['content_type']

        if content_type == 'video':
            print(f"📹 检测到视频: {result['desc'][:50]}...")
            path = crawler.download_video(url, output_dir)
            if path:
                print(f"✅ 视频下载成功: {path}")
            else:
                print("❌ 视频下载失败")
        elif content_type == 'image':
            print(f"🖼️  检测到图集: {result['desc'][:50]}...")
            paths = crawler.download_image(url, output_dir)
            if paths:
                print(f"✅ 图集下载成功，共 {len(paths)} 张图片")
            else:
                print("❌ 图集下载失败")
        else:
            print("❌ 未知内容类型")
    except Exception as e:
        print(f"❌ 下载失败: {e}")


def download_user(crawler: DouyinCrawler, user_url: str, max_pages: int, output_dir: str):
    """下载用户主页所有作品"""
    try:
        print(f"👤 开始下载用户主页作品，页数: {max_pages}")
        paths = crawler.download_user_videos(user_url, max_pages=max_pages, output_dir=output_dir)
        print(f"✅ 批量下载完成，共下载 {len(paths)} 个文件")
    except Exception as e:
        print(f"❌ 批量下载失败: {e}")


def download_collection(crawler: DouyinCrawler, collection_url: str, max_pages: int, output_dir: str, log_file: str = None):
    """下载合集所有作品"""
    try:
        print(f"📚 开始下载合集作品，页数: {max_pages}")
        paths = crawler.download_collection_videos(
            collection_url,
            max_pages=max_pages,
            output_dir=output_dir,
            log_file=log_file,
        )
        print(f"✅ 合集下载完成，共下载 {len(paths)} 个文件")
    except Exception as e:
        print(f"❌ 合集下载失败: {e}")


def parse_only(crawler: DouyinCrawler, url: str):
    """仅解析单条作品，不下载"""
    try:
        result = crawler.parse(url)
        print("\n📋 解析结果:")
        print(f"  类型: {result['content_type']}")
        print(f"  ID: {result['aweme_id']}")
        print(f"  描述: {result['desc']}")
        print(f"  作者: {result['author_nickname']}")

        if result['content_type'] == 'video':
            print(f"  视频地址: {result['play_url']}")
        elif result['content_type'] == 'image':
            print(f"  图片数量: {result['image_count']}")
            for i, img_url in enumerate(result['image_urls'], 1):
                print(f"  图片 {i}: {img_url}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")


def parse_collection_only(crawler: DouyinCrawler, collection_url: str, max_pages: int):
    """仅解析合集，不下载"""
    try:
        mix_id = crawler.get_collection_id(collection_url)
        detail = crawler.get_collection_detail(mix_id)
        mix_info = detail.get('mix_info') or {}
        mix_name = mix_info.get('mix_name', '')

        items = crawler.parse_collection_detail(collection_url, max_pages=max_pages)
        print("\n📋 合集解析结果:")
        print(f"  合集ID: {mix_id}")
        if mix_name:
            print(f"  合集名称: {mix_name}")
        print(f"  作品数量: {len(items)}")

        for i, item in enumerate(items[:10], 1):
            print(f"  {i}. [{item['content_type']}] {item['aweme_id']} - {item['desc'][:40]}")

        if len(items) > 10:
            print(f"  ... 其余 {len(items) - 10} 条未展示")
    except Exception as e:
        print(f"❌ 合集解析失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='抖音下载器 - 支持视频、图集、用户主页和合集批量下载',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 下载单个视频或图集
  python douyin_cli.py -u "https://v.douyin.com/xxxxx"

  # 仅解析单条作品不下载
  python douyin_cli.py -u "https://v.douyin.com/xxxxx" --parse-only

  # 下载用户主页前2页作品
  python douyin_cli.py --user "https://www.douyin.com/user/xxxxx" --pages 2

  # 下载合集前2页作品
  python douyin_cli.py --collection "https://www.douyin.com/collection/xxxxx" --pages 2

  # 仅解析合集
  python douyin_cli.py --collection "https://v.douyin.com/xxxxx" --pages 1 --parse-only

  # 合集下载并写入日志文件
  python douyin_cli.py --collection "https://v.douyin.com/xxxxx" --pages 50 --log-file ./collection_progress.log

  # 指定输出目录
  python douyin_cli.py -u "https://v.douyin.com/xxxxx" -o ./my_downloads

  # 使用自定义 cookie 文件
  python douyin_cli.py -u "https://v.douyin.com/xxxxx" --cookie ./my_cookie.txt
        '''
    )

    parser.add_argument('-u', '--url', help='视频或图集链接')
    parser.add_argument('--user', help='用户主页链接（批量下载）')
    parser.add_argument('--collection', help='合集链接（批量下载）')
    parser.add_argument('-o', '--output', default='downloads', help='输出目录 (默认: downloads)')
    parser.add_argument('-p', '--pages', type=int, default=1, help='用户主页/合集下载页数 (默认: 1)')
    parser.add_argument('--cookie', default='cookie.txt', help='Cookie 文件路径 (默认: cookie.txt)')
    parser.add_argument('--parse-only', action='store_true', help='仅解析，不下载')
    parser.add_argument('--log-file', help='进度日志文件路径（仅合集下载生效，默认写到合集目录）')

    args = parser.parse_args()

    if not args.url and not args.user and not args.collection:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.cookie):
        print(f"❌ Cookie 文件不存在: {args.cookie}")
        print("请创建 cookie.txt 文件并填入你的抖音 Cookie")
        sys.exit(1)

    print("🚀 初始化抖音下载器...")
    crawler = DouyinCrawler.from_cookie_file(args.cookie)

    if not crawler.cookie:
        print("❌ Cookie 为空，请检查 cookie.txt 文件")
        sys.exit(1)

    print("✅ 初始化完成\n")
    os.makedirs(args.output, exist_ok=True)

    if args.collection:
        if args.parse_only:
            parse_collection_only(crawler, args.collection, args.pages)
        else:
            download_collection(crawler, args.collection, args.pages, args.output, args.log_file)
    elif args.user:
        download_user(crawler, args.user, args.pages, args.output)
    elif args.parse_only:
        parse_only(crawler, args.url)
    else:
        download_single(crawler, args.url, args.output)


if __name__ == '__main__':
    main()
