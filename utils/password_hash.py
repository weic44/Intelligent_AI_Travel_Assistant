# from passlib.context import CryptContext

# 密码哈希的算法：bcrypt
# 当设置为 "auto" 时，它将根据已配置的密码哈希方案自动确定哪些方案被视为过时的，并且在验证密码时会更新为更安全的哈希算法。
# password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


# def get_hashed_password(password: str) -> str:
#     """
#     接受一个真实的密码，返回一个hash之后的密文
#     :param password:
#     :return:
#     """
#     return password_context.hash(password)
#
#
# def verify_password(password: str, hashed_pass: str) -> bool:
#     """
#     校验密码是否正确
#     :param password: 传入的密码
#     :param hashed_pass: hash之后密文
#     :return:
#     """
#     return password_context.verify(password, hashed_pass)
import hashlib
from passlib.context import CryptContext

# 配置密码上下文
# schemes: 指定使用的算法
# deprecated: 自动标记过时算法，验证时若发现旧算法会自动重新哈希
# bcrypt__rounds: 设置 bcrypt 的工作因子（迭代次数），默认12，可根据服务器性能调整（越高越安全但越慢）
password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=5
)


def _prehash_password(password: str) -> str:
    """
    对密码进行预处理，解决 bcrypt 72字节限制问题。
    使用 SHA-256 将任意长度的密码转换为固定长度的十六进制字符串。
    """
    # 1. 编码为 UTF-8
    # 2. 计算 SHA-256 哈希
    # 3. 转换为十六进制字符串 (长度为64字符，远小于72字节限制)
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def get_hashed_password(password: str) -> str:
    """
    接受一个真实的密码，返回一个 hash 之后的密文

    :param password: 用户输入的明文密码
    :return: bcrypt 哈希后的字符串
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # 先预处理，再哈希
    prehashed = _prehash_password(password)
    return password_context.hash(prehashed)


def verify_password(password: str, hashed_pass: str) -> bool:
    """
    校验密码是否正确

    :param password: 用户输入的明文密码
    :param hashed_pass: 数据库中存储的 hash 密文
    :return: True 如果密码匹配，否则 False
    """
    if not password or not hashed_pass:
        return False

    try:
        # 先预处理，再验证
        prehashed = _prehash_password(password)
        return password_context.verify(prehashed, hashed_pass)
    except Exception as e:
        # 生产环境中建议记录日志，而不是直接打印
        print(f"Password verification error: {e}")
        return False
