import torch
from torch import nn
# from action_list import TokenList
import torch.nn.functional as F
import numpy as np
import collections
import random

# from run_this import injection_result


# --------------------------------------- #
# 经验回放池
# --------------------------------------- #


class ReplayBuffer():
    def __init__(self, capacity):
        # 创建一个先进先出的队列，最大长度为capacity，保证经验池的样本量不变
        self.buffer = collections.deque(maxlen=capacity)

    # 将数据以元组形式添加进经验池
    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    # 随机采样batch_size行数据
    def sample(self, batch_size):
        transitions = random.sample(self.buffer, batch_size)  # list, len=32
        # *transitions代表取出列表中的值，即32项
        state, action, reward, next_state, done = zip(*transitions)
        return np.array(state), action, reward, np.array(next_state), done

    # 目前队列长度
    def size(self):
        return len(self.buffer)


# -------------------------------------- #
# 构造深度学习网络，输入状态s，得到各个动作的reward
# -------------------------------------- #

class Net(nn.Module):
    # 构造只有一个隐含层的网络
    def __init__(self, n_states, n_actions):
        super(Net, self).__init__()
        self.online = nn.Sequential(
            nn.Linear(n_states, 2048),
            nn.ReLU(),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, n_actions),
        )
    # 前传
    def forward(self, input):  # [b,n_states]

        return self.online(input)


# class State:
#     def __init__(self, injection_result, token_list):
#         self.injection_result = injection_result
#         self.token_list = token_list
#
#     # def generate_state_representation(self):







# class action_reprensentation:
#     def __init__(self, action_n,paylaod_size):
#         self.action_n = action_n
#         self.paylaod_size = paylaod_size
#
#     def get_best_action_and_position(self, representation):
#         # 找到最大值的索引
#         max_index = np.argmax(representation)
#
#         # 计算对应的动作和位置
#         action = max_index // self.payload_size
#         position = max_index % self.payload_size
#
#         return action, position


# -------------------------------------- #
# 构造深度强化学习模型
# -------------------------------------- #

class DQN:
    # （1）初始化
    def __init__(self, n_states,n_actions,
                 learning_rate, gamma, epsilon,
                 target_update, device):
        # 属性分配
        self.n_states = n_states  # 状态的特征数
        # self.n_hidden = n_hidden  # 隐含层个数
        self.n_actions = n_actions  # 动作数
        self.learning_rate = learning_rate  # 训练时的学习率
        self.gamma = gamma  # 折扣因子，对下一状态的回报的缩放
        self.epsilon = epsilon  # 贪婪策略，有1-epsilon的概率探索
        self.target_update = target_update  # 目标网络的参数的更新频率
        self.device = device  # 在GPU计算
        # 计数器，记录迭代次数
        self.count = 0

        # 构建2个神经网络，相同的结构，不同的参数
        # 实例化训练网络  [b,4]-->[b,2]  输出动作对应的奖励
        self.q_net = Net(self.n_states,self.n_actions)
        # 实例化目标网络
        self.target_q_net = Net(self.n_states, self.n_actions)

        # 优化器，更新训练网络的参数
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.learning_rate)

    # （2）动作选择
    def take_action(self, state_representation, epsilon_new):
        # 维度扩充，给行增加一个维度，并转换为张量shape=[1,4]
        # state = torch.Tensor(state[np.newaxis, :])

        # 生成state_representation
        state_representation = torch.Tensor(state_representation[np.newaxis, :])
        # print(state_representation)
        # 如果小于该值就取最大的值对应的索引
        if np.random.random() < epsilon_new:  # 0-1
            # 前向传播获取该状态对应的动作的reward
            actions_value = self.q_net(state_representation)
            # 获取reward最大值对应的动作索引
            action = actions_value.argmax().item()  # int
        # 如果大于该值就随机探索
        else:
            # 随机选择一个动作
            action = np.random.randint(self.n_actions)
        return action

    # （3）网络训练
    def update(self, transition_dict):  # 传入经验池中的batch个样本
        # 获取当前时刻的状态 array_shape=[b,4]
        states = torch.tensor(transition_dict['states'], dtype=torch.float)
        # 获取当前时刻采取的动作 tuple_shape=[b]，维度扩充 [b,1]
        actions = torch.tensor(transition_dict['actions']).view(-1, 1)
        # 当前状态下采取动作后得到的奖励 tuple=[b]，维度扩充 [b,1]
        rewards = torch.tensor(transition_dict['rewards'], dtype=torch.float).view(-1, 1)
        # 下一时刻的状态 array_shape=[b,4]
        next_states = torch.tensor(transition_dict['next_states'], dtype=torch.float)
        # 是否到达目标 tuple_shape=[b]，维度变换[b,1]
        dones = torch.tensor(transition_dict['dones'], dtype=torch.float).view(-1, 1)

        # 输入当前状态，得到采取各运动得到的奖励 [b,4]==>[b,2]==>[b,1]
        # 根据actions索引在训练网络的输出的第1维度上获取对应索引的q值（state_value）
        q_values = self.q_net(states).gather(1, actions)  # [b,1]
        # 下一时刻的状态[b,4]-->目标网络输出下一时刻对应的动作q值[b,2]-->
        # 选出下个状态采取的动作中最大的q值[b]-->维度调整[b,1]
        max_next_q_values = self.target_q_net(next_states).max(1)[0].view(-1, 1)
        # 目标网络输出的当前状态的q(state_value)：即时奖励+折扣因子*下个时刻的最大回报
        q_targets = rewards + self.gamma * max_next_q_values * (1 - dones)

        # 目标网络和训练网络之间的均方误差损失
        dqn_loss = torch.mean(F.mse_loss(q_values, q_targets))
        # PyTorch中默认梯度会累积,这里需要显式将梯度置为0
        self.optimizer.zero_grad()
        # 反向传播参数更新
        dqn_loss.backward()
        # 对训练网络更新
        self.optimizer.step()

        # 在一段时间后更新目标网络的参数
        if self.count % self.target_update == 0:
            # 将目标网络的参数替换成训练网络的参数
            self.target_q_net.load_state_dict(
                self.q_net.state_dict())

        self.count += 1

    def reward(self, injection_result):
        # 如果出现syntax error
        # if injection_result == "invalidaction":
        #     return -3
        # if injection_result == "nonecommand":
        #     return -2
        # if injection_result == "multiplecommand":
        #     return -1.5
        # if injection_result == "syntaxerror":
        #     return -1
        # if injection_result == "nooutput":
        #     return -1
        # if injection_result == "failedescaping":
        #     return -0.5
        # if injection_result == "true":
        #     return 0
        if injection_result == "invalidaction":
            return -3
        if injection_result == "nonecommand":
            return -2
        if injection_result == "multiplecommand":
            return -3
        if injection_result == "syntaxerror":
            return -1
        if injection_result == "nosuchaction":
            return -0.7
        if injection_result == "false":
            return -0.5
        if injection_result == "true":
            return 1




