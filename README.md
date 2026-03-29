# 抖音下载器

抖音视频/图集下载工具，支持单个作品下载和用户主页批量下载。

## 功能

- ✅ 下载单个视频或图集（自动识别）
- ✅ 批量下载用户主页作品
- ✅ 仅解析链接信息
- ✅ 下载进度条显示

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 1. 准备 Cookie

创建 `cookie.txt` 文件，填入你的抖音 Cookie。

### 2. 交互式模式（推荐）

```bash
python douyin_interactive.py
```

### 3. 命令行模式

```bash
# 下载单个作品 (推荐)
python douyin_cli.py -u "8.43 05/21 X@Z.md qRK:/ - 不好是蛇形刁手！！# 叉子摇 # 绝区零# 妄想天使  https://v.douyin.com/e8iDdXMv268/ 复制此链接，打开Dou音搜索，直接观看视频！"

# 批量下载用户主页 (默认下载一页约20个视频)
python douyin_cli.py --user "长按复制此条消息，打开抖音搜索，查看TA的更多作品。 https://v.douyin.com/gEQ3KVpf_R4/" --pages 1

# 仅解析
python douyin_cli.py -u "https://v.douyin.com/xxxxx" --parse-only
```

## 项目结构

```
.
├── core/
│   └── douyin_crawler.py    # 核心爬虫逻辑
├── util/
│   ├── abogus.py            # a_bogus 签名
│   └── xbogus.py            # X-Bogus 签名
├── douyin_cli.py            # 命令行工具
├── douyin_interactive.py    # 交互式工具
├── requirements.txt         # 依赖
└── cookie.txt               # Cookie 文件（需自行创建）
```

## 依赖

- requests - HTTP 请求
- gmssl - SM3 哈希计算
- tqdm - 进度条显示

## 免责声明

仅供学习交流使用，请勿用于商业用途。下载内容版权归原著作权人所有。
