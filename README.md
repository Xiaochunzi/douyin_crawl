# douyin_crawl

### 简介
```text
一个简洁的抖音作品批量下载命令行工具
2025/8/3 发现接口请求时偶发请求限流导致响应无数据，可能是触发了反爬机制
```

### 架构特点
```text
- 封装了简洁的 CrawlerRequest 类处理爬虫相关功能
- 支持自动随机睡眠、User-Agent 轮换、重试机制等
- 模块化设计，代码结构清晰，易于理解和使用
- 工具类通用性强，不绑定特定网站的请求头
```

### 开发环境
```text
windows10
pycharm
```

### 编译运行环境
```text
Python 3.8.6 (tags/v3.8.6:db45529, Sep 23 2020, 15:52:53) [MSC v.1927 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
```

### 环境准备

#### 为什么推荐使用虚拟环境？

虚拟环境可以：
- **隔离依赖**：避免与系统 Python 环境冲突
- **版本控制**：确保项目依赖版本的一致性
- **易于管理**：方便项目的部署和迁移
- **避免污染**：不会影响其他 Python 项目

#### 推荐使用虚拟环境

**Windows 用户：**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python crawl_home.py

# 退出虚拟环境
deactivate
```

**Linux/macOS 用户：**
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python crawl_home.py

# 退出虚拟环境
deactivate
```

#### 直接安装（不推荐）

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者单独安装
pip install py_mini_racer>=0.6.0
pip install requests>=2.25.0
pip install urllib3>=1.26.0
pip install loguru>=0.6.0
```

### 快速启动

**Windows 用户：**
```bash
# 一键启动（如果已创建虚拟环境）
.venv\Scripts\activate && python crawl_home.py
```

**Linux/macOS 用户：**
```bash
# 一键启动（如果已创建虚拟环境）
source .venv/bin/activate && python crawl_home.py
```

### 项目结构
```
douyin_crawl/
├── crawl_home.py          # 主程序
├── config.ini            # 配置文件
├── requirements.txt       # 依赖列表
├── LICENSE               # 许可证文件
├── .gitignore           # Git忽略文件
├── utils/
│   ├── crawler_request.py # 爬虫请求类
│   ├── xbogus_util.py    # X-Bogus 签名工具
│   ├── X-Bogus.js        # JavaScript 签名代码
│   └── my_util.py        # 工具函数
└── 运行截图/              # 运行示例截图
```

### 配置说明

在 `config.ini` 文件中配置你的 Cookie：

```ini
[douyin]
cookie = your_cookie_string_here
```

### 设计优势

- **模块化设计**：功能分离，代码结构清晰
- **通用性强**：`CrawlerRequest` 类可用于各种爬虫场景
- **易于维护**：简洁的代码结构，便于理解和修改
- **稳定可靠**：内置重试机制和错误处理

### 注意事项

1. 请确保在 `config.ini` 中配置正确的 Cookie
2. 遵守目标网站的爬虫协议和使用条款
3. 合理设置请求间隔，避免对服务器造成过大压力
4. 下载的文件会保存在以用户ID命名的目录中

### 常见问题

**Q: 虚拟环境激活失败？**
```bash
# Windows 用户尝试：
.venv\Scripts\activate.bat

# Linux/macOS 用户尝试：
source .venv/bin/activate
```

**Q: 依赖安装失败？**
```bash
# 升级 pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**Q: 权限问题？**
```bash
# Linux/macOS 用户可能需要：
chmod +x .venv/bin/activate
```

**Q: Python 版本问题？**
- 确保使用 Python 3.7 或更高版本
- 检查 Python 版本：`python --version`

### 许可证

本项目采用 GPL 许可证，详见 [LICENSE](LICENSE) 文件。
