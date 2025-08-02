import threading
import uuid
from loguru import logger


def sanitize_filename(filename, max_len=100, ellipsis_str='...'):
    """去除操作系统不支持的文件名字符，并处理过长的文件名"""
    if not filename:
        logger.warning("文件名为空，生成随机UUID作为文件名。")
        return str(uuid.uuid4())
    
    # 去除非法字符
    invalid_chars = '<>:"/\\|?*\n\t\r'
    sanitized = ''.join('' if c in invalid_chars else c for c in filename).strip(' .')
    
    # 处理过长文件名
    if len(sanitized) > max_len:
        if len(ellipsis_str) >= max_len:
            raise ValueError("省略符号长度不能大于或等于最大文件名长度。")
        head_len = (max_len - len(ellipsis_str)) // 2
        tail_len = max_len - len(ellipsis_str) - head_len
        sanitized = sanitized[:head_len] + ellipsis_str + sanitized[-tail_len:]
    
    return sanitized if sanitized else str(uuid.uuid4())


class IDGenerator:
    """线程安全的ID生成器"""
    _last_id = 0
    _lock = threading.Lock()

    @classmethod
    def generate_unique_id(cls) -> int:
        """线程安全地生成并返回一个新的全局自增ID"""
        with cls._lock:
            cls._last_id += 1
            logger.debug(f"生成新的唯一ID: {cls._last_id}")
            return cls._last_id


if __name__ == '__main__':
    print(IDGenerator.generate_unique_id())

