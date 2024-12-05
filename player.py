import os
import random
import numpy as np
import pandas as pd

import wcwidth


def align_text(text, width):
    """中文对齐"""
    text_width = len(text)
    if text_width < width:
        return text + f'{chr(12288)}' * (width - text_width)
    else:
        return text


COIN_NAMES = ["White", "Blue", "Green", "Red", "Black", "Pink", "Gold"]
CH_COIN_NAMES_TABLE = {
    "White": "白色",
    "Blue": "蓝色",
    "Green": "绿色",
    "Red": "红色",
    "Black": "黑色",
    "Pink": "粉色",
    "Gold": "黄金",
    "Stick": "粘贴",
    "none": "无色",
    "empty": "空缺"
}
CH_FUNC_TABLE = {
    "add": f"{align_text('获取同色硬币', 6)}",
    "recycle": f"{align_text('再来一回合', 6)}",
    "none": f"{align_text('无', 6)}",
    "take": f"{align_text('夺取对手硬币', 6)}",
    "privilege": f"{align_text('获得卷轴', 6)}"
}

PRICE_NAMES = ["White", "Blue", "Green", "Red", "Black", "Pink"]


def get_input(message, valid_list=None, assert_type=None, assert_num=[1]):
    input_value = None
    while True:
        try:
            user_input = input(message)
            ok = True
            input_value = user_input
            if valid_list is not None and input_value not in valid_list:
                print(f"输入不正确，请重新输入， 合法值为{valid_list}")
                ok = False
            if assert_type is not None:
                values = user_input.split()
                if len(values) not in assert_num:
                    print(f"输入不正确，请重新输入，合法数量为{assert_num}")
                    ok = False
                if assert_type == "int":
                    nums = [int(x) for x in values]
                    input_value = nums
                else:
                    input_value = values
            if ok:
                break
        except Exception as e:
            print(e)
    return input_value


class Player:
    def __init__(self, name):
        self.name = name
        self.coins = {x: 10 for x in COIN_NAMES}
        self.cards_power = {x: 0 for x in COIN_NAMES}
        self.crowns = 0
        self.victory_points = 0
        self.reserved_cards = []
        self.privileges = 0

    def add_cards_power(self, color, amount):
        if color in self.cards_power:
            self.cards_power[color] += amount

    def add_victory_points(self, points):
        self.victory_points += points

    def add_crowns(self, crowns):
        self.crowns += crowns

    def add_coins(self, color, amount):
        if color in self.coins:
            self.coins[color] += amount

    def add_privilege(self, amount):
        self.privileges += amount

    def use_privilege(self):
        if self.privileges > 0:
            self.privileges -= 1
            return True
        return False

    def check_victory(self):
        if self.victory_points >= 20 or self.crowns >= 10 or \
                any(self.cards_power[color] >= 10 for color in self.cards_power.keys()):
            return True
        return False

    def print_info(self):
        info_message = f"玩家: {self.name}\n{align_text('硬币', 4)} "
        for key, value in self.coins.items():
            info_message += f"{CH_COIN_NAMES_TABLE[key]} {value} "
        info_message += f"\n{align_text('卡片宝石', 4)} "
        for key, value in self.cards_power.items():
            info_message += f"{CH_COIN_NAMES_TABLE[key]} {value} "
        print(info_message)
        return info_message


class Card:
    def __init__(self,
                 level: int = 0,
                 color: str = None,
                 color_num: int = 0,
                 crowns: int = 0,
                 point: int = 0,
                 price: tuple = None,
                 function: str = None):
        '''
        :param level: 1 2 3
        :param color: # white/blue/green/red/black/stick/none
        :param color_num: 0 1 2
        :param crowns: 0 1 2 3
        :param point: 0-8
        :param price: dict
        :param function: # none/recycle/take/privilege/add/
        '''
        self.level = level
        self.color = color
        self.color_num = color_num
        self.crowns = crowns
        self.point = point
        self.price = price
        self.function = function
        self.price_name = PRICE_NAMES

    def __str__(self):
        message = f"等级 {self.level} 颜色 {CH_COIN_NAMES_TABLE[self.color]:>5} 宝石数 {self.color_num} 分数 {self.point} " \
               f"皇冠 {self.crowns} 功能 {CH_FUNC_TABLE[self.function]} 价格 "
        for idx, item in enumerate(self.price_name):
            message += f"{CH_COIN_NAMES_TABLE[item]} {self.price[idx]}"
            if idx < len(self.price_name) - 1:
                message += " "
        return message


class Board:
    def __init__(self):
        self.board_info = np.ones((5, 5), dtype=np.int64) * -1
        # self.bag = np.array([4, 4, 4, 4, 4, 2, 3])
        self.coin_index_list = np.array([0, 4, 8, 12, 16, 20, 22, 25])
        self.bag = list(range(25))
        self.coin_type = COIN_NAMES

    def refresh(self):
        bag_coin_num = len(self.bag)
        order = [(2, 2), (2, 3), (3, 3), (3, 2), (3, 1), (2, 1), (1, 1), (1, 2), (1, 3), (1, 4),
                 (2, 4), (3, 4), (4, 4), (4, 3), (4, 2), (4, 1), (4, 0), (3, 0), (2, 0), (1, 0),
                 (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        pos_idx = 0
        for i in range(bag_coin_num):
            coin_index = np.random.choice(self.bag)
            self.bag.remove(coin_index)
            while self.board_info[order[pos_idx][0]][order[pos_idx][1]] != -1:
                pos_idx += 1
            self.board_info[order[pos_idx][0]][order[pos_idx][1]] = coin_index

    def get_coin_type(self, coin_index):
        if coin_index == -1:
            rtn = "empty"
        else:
            coin_type = 0
            for j in range(self.coin_index_list.shape[0]):
                if coin_index < self.coin_index_list[j]:
                    break
                else:
                    coin_type = j
            rtn = self.coin_type[coin_type]
        return rtn

    def print_board(self):
        print("当前棋盘")
        for i in range(5):
            for j in range(5):
                print(f" ({i}, {j}){CH_COIN_NAMES_TABLE[self.get_coin_type(self.board_info[i][j])]:<2}", end='')
                if j != 4:
                    print(" ", end='')
                else:
                    print("")

    def get_position_coin(self, x, y, no_gold=False):
        succ = True
        coin_type = None
        if 0 <= x < 5 and 0 <= y < 5:
            if self.board_info[x][y] != -1:
                coin_type = self.get_coin_type(self.board_info[x][y])
                if no_gold and coin_type == "Gold":
                    coin_type = None
                    succ = False
                else:
                    self.board_info[x][y] = -1
            else:
                succ = False
        else:
            succ = False
        return succ, coin_type

    def select(self, direction, start_x, start_y, length):
        # direction start_x start_y length
        # direction up down left right up-right up-left down-left down-right
        coin_num = (0, 0, 0, 0, 0, 0, 0)
        # 判断是否可以拿
        # 拿给玩家
        return coin_num

    def get_coins_list(self, position_list):
        succ = True
        coin_list = []
        opposite_privilege = False
        coin_num = len(position_list) // 2
        position_tuple_list = [(position_list[i*2], position_list[i*2+1]) for i in range(coin_num)]
        position_tuple_list = sorted(position_tuple_list)
        # 坐标判断，是否在同行，同列上，是否连续
        # 是否包含黄金
        include_gold = False
        for i in range(coin_num):
            tmp_x, tmp_y = position_tuple_list[i]
            if self.board_info[tmp_x][tmp_y] == -1:
                succ = False
            if self.get_coin_type(self.board_info[tmp_x][tmp_y]) == 'Gold':
                include_gold = True

        if coin_num == 1:
            pass
        elif coin_num == 2:
            if include_gold:
                succ = False
            first_coin_pos = position_tuple_list[0]
            second_coin_pos = position_tuple_list[1]
            rule_found = False
            if first_coin_pos[0] == second_coin_pos[0] and abs(first_coin_pos[1] - second_coin_pos[1]) == 1:
                rule_found = True
            if first_coin_pos[1] == second_coin_pos[1] and abs(first_coin_pos[0] - second_coin_pos[0]) == 1:
                rule_found = True
            if first_coin_pos[0] - second_coin_pos[0] == first_coin_pos[1] - second_coin_pos[1] \
                    and abs(first_coin_pos[0] - second_coin_pos[0]) == 1:
                rule_found = True
            if not rule_found:
                succ = False
        elif coin_num == 3:
            if include_gold:
                succ = False
            first_coin_pos = position_tuple_list[0]
            second_coin_pos = position_tuple_list[1]
            third_coin_pos = position_tuple_list[2]
            rule_found = False
            if (first_coin_pos[0] == second_coin_pos[0] == third_coin_pos[0]) \
                    and (third_coin_pos[1] - second_coin_pos[1] == second_coin_pos[1] - first_coin_pos[1]) \
                    and abs(first_coin_pos[1] - second_coin_pos[1]) == 1:
                rule_found = True
            if (first_coin_pos[1] == second_coin_pos[1] == third_coin_pos[1]) \
                    and (third_coin_pos[0] - second_coin_pos[0] == second_coin_pos[0] - first_coin_pos[0]) \
                    and abs(first_coin_pos[0] - second_coin_pos[0]) == 1:
                rule_found = True
            if (first_coin_pos[0] - second_coin_pos[0] == first_coin_pos[1] - second_coin_pos[1]
                == second_coin_pos[0] - third_coin_pos[0] ==
                second_coin_pos[1] - third_coin_pos[1]) and abs(first_coin_pos[0] - second_coin_pos[0]) == 1:
                rule_found = True
            if not rule_found:
                succ = False
        else:
            pass
        if succ:
            for i in range(coin_num):
                tmp_x, tmp_y = position_tuple_list[i]
                coin_list.append(self.get_coin_type(self.board_info[tmp_x][tmp_y]))
                self.board_info[tmp_x][tmp_y] = -1
        return succ, coin_list, opposite_privilege




class GameServer:
    def __init__(self):
        self.cards: list[Card] = []
        self.unused_cards: list[Card] = []
        self.load_cards_from_csv()
        self.player1: Player = Player("Boy")
        self.player2: Player = Player("Girl")
        self.table: list[list[Card]] = [[], [], [], []]
        self.board: Board = Board()
        self.cur_player: Player = None
        self.cur_opposite: Player = None
        self.privilege_bank: int = 3

    def load_cards_from_csv(self):
        path = "cards.csv"
        df = pd.read_csv(path)
        for index, row in df.iterrows():
            row_dict = dict(row)
            self.cards.append(Card(
                level=row_dict['level'],
                color=row_dict['color'],
                color_num=row_dict['color_num'],
                point=row_dict['point'],
                crowns=row_dict['crowns'],
                function=row_dict['function'],
                price=(
                    row_dict['price_white'],
                    row_dict['price_blue'],
                    row_dict['price_green'],
                    row_dict['price_red'],
                    row_dict['price_black'],
                    row_dict['price_pink'],
                )
            ))

    def draw_one_card(self, level):
        target_card_list = [idx for idx, card in enumerate(self.cards) if card.level == level
                            and self.unused_cards[idx]]
        target_idx = np.random.choice(target_card_list)
        self.table[level-1].append(self.cards[target_idx])
        self.unused_cards[target_idx] = 0

    def print_table(self):
        for i in [2, 1, 0]:
            print(f"Level {i+1}")
            for j in range(len(self.table[i])):
                print(f"序号 {j+1} 卡片内容: {self.table[i][j]}")

    def decision_get_coin(self):
        succ = True
        while True:
            self.board.print_board()
            position_list = get_input("坐标 x1 y1 x2 y2 x3 y3(退出请输入-1 -1): ", assert_type="int", assert_num=[2, 4, 6])
            if position_list[0] == -1 and position_list[1] == -1:
                succ = False
                break
            print(f"玩家输入坐标 {position_list}")
            succ, coins_list, opposite_privilege = self.board.get_coins_list(position_list)
            if succ:
                for coin in coins_list:
                    print(f"玩家 {self.cur_player.name} 拿到一个 {CH_COIN_NAMES_TABLE[coin]} 硬币")
                    self.cur_player.add_coins(coin, 1)
                if opposite_privilege:
                    print(f"玩家 {self.cur_opposite.name} 获得一个卷轴")
                    self.cur_opposite.add_privilege(1)
                break
            else:
                print("玩家输入的硬币序列不合法，请重新输入")
            self.cur_player.print_info()
            self.cur_opposite.print_info()
        return succ

    def decision_privilege(self):
        while True:
            if self.cur_player.privileges > 0:
                use_privilege = get_input(f"{self.cur_player.name} 当前有{self.cur_player.privileges}个卷轴, 是否使用卷轴? y or n: ", valid_list=['y', 'n'])
            else:
                break
            if use_privilege == 'y':
                position = get_input(f"玩家 {self.cur_player.name} 坐标 x y: ", assert_type="int", assert_num=[2])
                print(f"玩家 {self.cur_player.name} 输入坐标 {position}")
                succ, coin = self.board.get_position_coin(position[0], position[1], no_gold=True)
                print(f"玩家 {self.cur_player.name} 拿到一个 {CH_COIN_NAMES_TABLE[coin]} 硬币")
                self.cur_player.add_coins(coin, 1)
                self.cur_player.add_privilege(-1)
                self.cur_player.print_info()
            else:
                break

    def decision_refresh(self):
        need_refresh = get_input(f"玩家 {self.cur_player.name} 是否使用棋盘刷新? y or n: ", valid_list=['y', 'n'])
        if need_refresh == 'y':
            self.board.refresh()
            print("棋盘刷新成功")
            self.board.print_board()
            if self.privilege_bank == 0:
                print(f"由于银行无卷轴，玩家 {self.cur_player.name} 丢失1个卷轴")
                self.cur_player.add_privileges(-1)
            self.cur_opposite.add_privilege(1)
            print(f"玩家 {self.cur_opposite.name} 获得1个卷轴")

    def decision_buy_card(self):
        succ = True
        while True:
            target_card_info = get_input("请输入购买卡片的(等级, 序号) 退出请输入0 0: ", assert_type="int", assert_num=[2])
            if target_card_info[0] == 0 and target_card_info[1] == 0:
                succ = False
                break
            target_card = self.table[target_card_info[0]-1][target_card_info[1]-1]

            can_afford = True
            gap = 0
            for i in range(len(target_card.price)):
                coin_name = PRICE_NAMES[i]
                if target_card.price[i] > self.cur_player.coins[coin_name] + self.cur_player.cards_power[coin_name]:
                    can_afford = False
                    gap += target_card.price[i] - (self.cur_player.coins[coin_name] +
                                                  self.cur_player.cards_power[coin_name])
            if can_afford:
                pass
            else:
                if gap <= self.cur_player.coins['Gold']:
                    print(f"使用黄金代替 {gap} 枚硬币")
                else:
                    succ = False
            stick_color = None
            while True:
                if target_card.color == "Stick":
                    already_color = False
                    for key, value in self.cur_player.cards_power.items():
                        if value > 0:
                            already_color = True
                    if not already_color:
                        succ = False
                        break
                    else:
                        stick_color = get_input("请选择粘贴颜色 0-4代表白蓝绿红黑", assert_type="int", assert_num=[1])
                        if self.cur_player.cards_power[COIN_NAMES[stick_color]] == 0:
                            print(f"你没有{COIN_NAMES[stick_color]}的卡牌，请重新输入")
                        else:
                            print(f"粘贴在{COIN_NAMES[stick_color]}卡牌上")
                            break
                else:
                    break

            if succ:
                self.cur_player.add_coins('Gold', -gap)
                for i in range(len(target_card.price)):
                    coin_name = PRICE_NAMES[i]
                    self.cur_player.add_coins(coin_name, -target_card.price[i])
                if target_card.color not in ["Stick" and "none"]:
                    self.cur_player.add_cards_power(target_card.color, target_card.color_num)
                if target_card.color == "Stick":
                    self.cur_player.add_cards_power(stick_color, target_card.color_num)
                self.cur_player.add_victory_points(target_card.point)
                self.cur_player.add_crowns(target_card.crowns)
                print(f"玩家 {self.cur_player.name} 购买了 {target_card}")
                self.cur_player.print_info()
                # self.unused_cards[]
                # self.table[target_card_info[0]-1][target_card_info[1]-1]
                # 执行效果
                if target_card.function == 'none':
                    pass
                else:
                    pass
                break
        return succ

    def decision_preorder(self):
        pass
        return True


    def play(self):
        # init cards
        # show current cards
        # play 1 decision
        # play 2 decision

        self.load_cards_from_csv()
        self.unused_cards = [1 for i in range(len(self.cards))]

        self.board.refresh()
        self.board.print_board()

        card_num = [5, 4, 3]
        for idx, num in enumerate(card_num):
            for i in range(num):
                self.draw_one_card(idx+1)
        self.print_table()

        self.cur_player = self.player1
        self.cur_opposite = self.player2

        round_idx = 1
        while True:
            print(f"当前第 {round_idx} 回合， 玩家 {self.cur_player.name} 行动")
            self.player1.print_info()
            self.player2.print_info()
            self.board.print_board()
            self.print_table()

            succ = True
            self.decision_privilege()
            self.decision_refresh()
            decision = get_input(f"玩家 {self.cur_player.name} 操作选择(1 拿币 2 买卡 3 预购卡牌): ", valid_list=['1', '2', '3'])
            if decision == '1':
                succ = self.decision_get_coin()
            elif decision == '2':
                succ = self.decision_buy_card()
            elif decision == '3':
                succ = self.decision_preorder()
            else:
                pass
            self.cur_player.check_victory()
            if succ:
                print(f"玩家 {self.cur_player.name} 的回合结束，轮到 玩家 {self.cur_opposite.name}")
                temp_player = self.cur_player
                self.cur_player = self.cur_opposite
                self.cur_opposite = temp_player

        # 玩家1 接受外部信号， 做选择
        # 卷轴阶段
        # 选择阶段
        # case 1 拿币
        # case 2 买卡
        # case 3 刷新
        # 判定是否请神
        # 特殊操作：再来一回合、抢夺、获得卷轴，获得同色硬币
        # 判定是否胜利


if __name__ == '__main__':
    game_server = GameServer()
    game_server.play()
