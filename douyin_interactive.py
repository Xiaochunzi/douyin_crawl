#!/usr/bin/env python3
"""
抖音下载器 - 交互式命令行工具
支持视频、图集、用户主页批量下载
"""

import os
import sys
from core.douyin_crawler import DouyinCrawler


def print_banner():
    """打印欢迎界面"""
    print("\n" + "=" * 50)
    print("     🎵 抖音下载器 - 交互式命令行工具 🎵")
    print("=" * 50)
    print()


def print_menu():
    """打印主菜单"""
    print("\n请选择操作：")
    print("-" * 30)
    print("  1. 下载单个视频或图集")
    print("  2. 批量下载用户主页作品")
    print("  3. 仅解析链接信息（不下载）")
    print("  4. 设置输出目录")
    print("  5. 设置Cookie文件")
    print("  0. 退出程序")
    print("-" * 30)


def get_input(prompt: str, default: str = None) -> str:
    """获取用户输入，支持默认值"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def confirm(prompt: str) -> bool:
    """确认操作"""
    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()
        if choice in ('y', 'yes', '是'):
            return True
        elif choice in ('n', 'no', '否'):
            return False
        print("请输入 y 或 n")


def download_single_interactive(crawler: DouyinCrawler, output_dir: str):
    """交互式下载单个视频或图集"""
    url = get_input("请输入视频/图集链接")
    if not url:
        print("❌ 链接不能为空")
        return
    
    print(f"\n📥 开始解析链接...")
    try:
        result = crawler.parse(url)
        content_type = result['content_type']
        
        if content_type == 'video':
            print(f"📹 检测到视频: {result['desc'][:50]}...")
            print(f"   作者: {result['author_nickname']}")
            if confirm("是否开始下载"):
                path = crawler.download_video(url, output_dir)
                if path:
                    print(f"✅ 视频下载成功: {path}")
                else:
                    print("❌ 视频下载失败")
        elif content_type == 'image':
            print(f"🖼️  检测到图集: {result['desc'][:50]}...")
            print(f"   作者: {result['author_nickname']}")
            print(f"   共 {result['image_count']} 张图片")
            if confirm("是否开始下载"):
                paths = crawler.download_image(url, output_dir)
                if paths:
                    print(f"✅ 图集下载成功，共 {len(paths)} 张图片")
                else:
                    print("❌ 图集下载失败")
        else:
            print("❌ 未知内容类型")
    except Exception as e:
        print(f"❌ 下载失败: {e}")


def download_user_interactive(crawler: DouyinCrawler, output_dir: str):
    """交互式批量下载用户主页作品"""
    url = get_input("请输入用户主页链接")
    if not url:
        print("❌ 链接不能为空")
        return
    
    pages_str = get_input("下载页数", "1")
    try:
        max_pages = int(pages_str)
        if max_pages < 1:
            max_pages = 1
    except ValueError:
        max_pages = 1
    
    print(f"\n👤 准备下载用户主页作品，页数: {max_pages}")
    if confirm("是否开始下载"):
        try:
            paths = crawler.download_user_videos(url, max_pages=max_pages, output_dir=output_dir)
            print(f"✅ 批量下载完成，共下载 {len(paths)} 个文件")
        except Exception as e:
            print(f"❌ 批量下载失败: {e}")


def parse_only_interactive(crawler: DouyinCrawler):
    """交互式仅解析链接信息"""
    url = get_input("请输入链接")
    if not url:
        print("❌ 链接不能为空")
        return
    
    print(f"\n📋 开始解析...")
    try:
        result = crawler.parse(url)
        print("\n" + "=" * 40)
        print("📋 解析结果:")
        print("=" * 40)
        print(f"  类型: {'视频' if result['content_type'] == 'video' else '图集'}")
        print(f"  ID: {result['aweme_id']}")
        print(f"  描述: {result['desc']}")
        print(f"  作者: {result['author_nickname']}")
        print(f"  发布时间: {result['create_time']}")
        
        if result['content_type'] == 'video':
            print(f"  视频地址: {result['play_url']}")
        elif result['content_type'] == 'image':
            print(f"  图片数量: {result['image_count']}")
            for i, img_url in enumerate(result['image_urls'], 1):
                print(f"  图片 {i}: {img_url}")
        print("=" * 40)
    except Exception as e:
        print(f"❌ 解析失败: {e}")


def main():
    """主函数"""
    print_banner()
    
    # 默认配置
    output_dir = "downloads"
    cookie_file = "cookie.txt"
    
    # 检查cookie文件
    while True:
        if not os.path.exists(cookie_file):
            print(f"⚠️  Cookie文件不存在: {cookie_file}")
            cookie_file = get_input("请输入Cookie文件路径", "cookie.txt")
            if not os.path.exists(cookie_file):
                print("❌ 文件不存在，请检查路径")
                if not confirm("是否继续"):
                    print("👋 再见！")
                    return
            else:
                break
        else:
            break
    
    # 初始化爬虫
    print(f"\n🚀 正在初始化...")
    print(f"   Cookie文件: {cookie_file}")
    print(f"   输出目录: {output_dir}")
    
    try:
        crawler = DouyinCrawler.from_cookie_file(cookie_file)
        if not crawler.cookie:
            print("❌ Cookie为空，请检查文件内容")
            return
        print("✅ 初始化完成！\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 主循环
    while True:
        print_menu()
        choice = get_input("请输入选项")
        
        if choice == "0":
            print("\n👋 感谢使用，再见！")
            break
        
        elif choice == "1":
            download_single_interactive(crawler, output_dir)
        
        elif choice == "2":
            download_user_interactive(crawler, output_dir)
        
        elif choice == "3":
            parse_only_interactive(crawler)
        
        elif choice == "4":
            new_dir = get_input("请输入输出目录", output_dir)
            if new_dir:
                output_dir = new_dir
                os.makedirs(output_dir, exist_ok=True)
                print(f"✅ 输出目录已设置为: {output_dir}")
        
        elif choice == "5":
            new_cookie = get_input("请输入Cookie文件路径", cookie_file)
            if os.path.exists(new_cookie):
                cookie_file = new_cookie
                try:
                    crawler = DouyinCrawler.from_cookie_file(cookie_file)
                    print(f"✅ Cookie文件已更新: {cookie_file}")
                except Exception as e:
                    print(f"❌ 更新失败: {e}")
            else:
                print(f"❌ 文件不存在: {new_cookie}")
        
        else:
            print("❌ 无效选项，请重新输入")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中断，再见！")
        sys.exit(0)
