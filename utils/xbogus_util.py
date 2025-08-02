from py_mini_racer import py_mini_racer
import urllib.parse


def generate_url_with_xbs(url, user_agent):
    query = urllib.parse.urlparse(url).query
    
    # 读取 JS 文件内容
    with open('utils/X-Bogus.js', 'r', encoding='utf-8') as f:
        js_code = f.read()
    
    # 创建 JS 执行上下文
    ctx = py_mini_racer.MiniRacer()
    ctx.eval(js_code)
    
    # 调用 sign 函数
    xbogus = ctx.call("sign", query, user_agent)
    return xbogus
