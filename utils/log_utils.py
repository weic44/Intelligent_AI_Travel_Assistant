import os
import sys
import logging

# 1. 确定日志目录路径
# 获取当前文件所在目录的上级目录作为项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(root_dir, 'logs')

# 2. 创建日志目录（如果不存在）
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 3. 定义日志文件路径
log_file_path = os.path.join(log_dir, 'app.log')

# 4. 配置日志格式
# 格式说明: 时间 - 级别 - 文件名:行号 - 消息
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name=None):
    """
    获取一个配置好的 Logger 实例
    :param name: logger 的名称，通常使用 __name__
    :return: logging.Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name if name else 'root')

    # 设置日志级别 (DEBUG 表示记录所有级别的日志)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 Handler (在多次调用 get_logger 时很重要)
    if logger.handlers:
        return logger

    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Handler 1: 控制台输出 (StreamHandler) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Handler 2: 文件输出 (FileHandler) ---
    # encoding='utf-8' 确保中文正常显示
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有 DEBUG 及以上级别
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 5. 测试使用
if __name__ == '__main__':
    # 获取 logger 实例
    log = get_logger(__name__)

    # 记录不同级别的日志
    log.debug("这是一条调试信息 (Debug)")
    log.info("程序正常启动 (Info)")
    log.warning("这是一个警告信息 (Warning)")
    log.error("发生了一个错误 (Error)")

    print(f"日志已写入至: {log_file_path}")
