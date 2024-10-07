import gym
from fsspec.implementations.libarchive import new_api

from RL_brain import *
from action_list import *
import torch
from tqdm import tqdm
import matplotlib.pyplot as plt
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# GPU运算
device = torch.device("cuda") if torch.cuda.is_available() \
    else torch.device("cpu")


# ------------------------------- #
# 全局变量
# ------------------------------- #

capacity = 500  # 经验池容量
lr = 2e-3  # 学习率
gamma = 0.9  # 折扣因子
epsilon = 0.6  # 贪心系数
target_update = 200  # 目标网络的参数的更新频率
batch_size = 32
# n_hidden = 128  # 隐含层神经元个数
min_size = 200  # 经验池超过200后再训练
return_list = []  # 记录每个回合的回报
true_list = [] # 记录每个回合发现的有效载荷

basic_token_n = 22
escaping_action_n = 6
max_payload_size = 10

# 加载环境
# env = gym.make("CartPole-v1", render_mode="human")
# n_states = env.observation_space.shape[0]  # 4
n_states = 64
# 输入为1*n的vector，第一位为是否出现语法错误，1-100为当前action，后100为当前载荷（2维）降维后的vector

# n_actions = env.action_space.n  # 2
n_actions = 1000
# 只为当前的action进行q值计算

injection_result = "true"


# 实例化经验池
replay_buffer = ReplayBuffer(capacity)
# 实例化DQN
agent = DQN(n_states=n_states,
            n_actions=n_actions,
            learning_rate=lr,
            gamma=gamma,
            epsilon=epsilon,
            target_update=target_update,
            device=device,
            )
# 加载模型权重
# agent.q_net.load_state_dict(torch.load('dqn_model_weights_6.pth'))
# agent.q_net.eval()  # 切换到评估模式

# 训练模型
# for i in range(10):  # 100回合
    # 每个回合开始前重置环境
    # state = env.reset()[0]  # len=4
token_list = TokenList()
state = token_list.encode_state()
# 记录每个回合的回报
episode_return = 0
episode_true = 0
done = False
epsilon_new = 0.1
random_mod = 0

# 打印训练进度，一共10回合
# with tqdm(total=10, desc='Iteration %d' % i) as pbar:
count_e = 0
count_n = 0
count_false = 0
count_invalid = 0
count_syntax = 0
count_multiple = 0
count_ncommand = 0
count_nosuch = 0
count_true = 0
mod = 0
while True:
    # 获取当前状态下需要采取的动作

    if random_mod == 0:
        action = agent.take_action(state, epsilon)
    else:
        action = agent.take_action(state, epsilon_new)
    # 执行action
    if count_n >= 99:
        print(token_list.get_string())
    token_list.decode_action(action)
    if token_list.injection_result == "nosuchaction":
        count_nosuch += 1
    token_list.inject("http://192.168.75.128/ci2.php", mod)


    if token_list.injection_result == "false":
        count_false += 1
    if token_list.injection_result == "invalidaction":
        count_invalid += 1
    if token_list.injection_result == "syntax":
        count_syntax += 1
    if token_list.injection_result == "multiplecommand":
        count_multiple += 1
    if token_list.injection_result == "nonecommand":
        count_ncommand += 1
    if token_list.injection_result == "true":
        count_true += 1
    # 获取新的state（payload+result）
    next_state = token_list.encode_state()
    if token_list.injection_result == "true":
        print(token_list.get_string())
        done = True
        episode_true += 1
    #计算reward

    reward = agent.reward(token_list.injection_result)
    # print(token_list.injection_result)

    ## 更新环境
    ## next_state, reward, done, _, _ = env.step(action)


    # 添加经验池
    replay_buffer.add(state, action, reward, next_state, done)
    # 更新当前状态
    state = next_state
    # 更新回合回报
    episode_return += reward

    # 当经验池超过一定数量后，训练网络
    if replay_buffer.size() > min_size:
        # 从经验池中随机抽样作为训练集
        s, a, r, ns, d = replay_buffer.sample(batch_size)
        # 构造训练集
        transition_dict = {
            'states': s,
            'actions': a,
            'next_states': ns,
            'rewards': r,
            'dones': d,
        }
        # 网络更新
        agent.update(transition_dict)
    # 找到目标就结束
    if done: break
    count_n += 1
    if count_n >= 100:
        # 保存模型权重
        print(f"nosuchaction:{count_nosuch}")
        print(f"false: {count_false}")
        print(f"invalid: {count_invalid}")
        print(f"syntax: {count_syntax}")
        print(f"multiple: {count_multiple}")
        print(f"ncommand: {count_ncommand}")
        print(f"true: {count_true}")
        print()
        # print(f"israndom: {random_mod}")
        # if count_false <= 10:
        #     random_mod = 1
        torch.save(agent.q_net.state_dict(), 'dqn_model_weights_8.pth')
        return_list.append(episode_return)
        true_list.append(episode_true)
        episode_return = 0
        episode_true = 0
        count_nosuch = 0
        count_n = 0
        count_false = 0
        count_invalid = 0
        count_syntax = 0
        count_multiple = 0
        count_ncommand = 0
        count_true = 0
        count_e += 1
    # if count_e >= 20:
    #     mod = 1
    if count_e >= 200:
        break


# 记录每个回合的回报


# # 更新进度条信息
# pbar.set_postfix({
#     'return': '%.3f' % return_list[-1]
# })
# pbar.update(1)

# 绘图
episodes_list = list(range(len(return_list)))
plt.plot(episodes_list, return_list)
plt.xlabel('Episodes')
plt.ylabel('Returns')
plt.title('DQN Returns')
plt.show()

sus_list = list(range(len(true_list)))
plt.plot(sus_list, true_list)
plt.xlabel('Episodes')
plt.ylabel('true_n')
plt.title('DQN true Returns')
plt.show()
