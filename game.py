from utilities import Utilities
from stone_group import StoneGroup
import json
import random

class Game():
    def __init__(self, server, field_size=False):
        self.server = server
        self.id = None
        self.invite = None
        self.field_size = int(field_size)
        self.id_white_player = None
        self.id_black_player = None
        self.last_turn = None
        self.penult_turn = None
        self.game_over = False
        self.turn_number = 0
        if (field_size):
            self.field = '0' * (self.field_size ** 2)
        self.turn = 'black'

    def __construct(server, game_data):
        game = Game(server)
        game.id = game_data['id']
        game.field_size = game_data['field_size']
        game.id_white_player = game_data['id_white_player']
        game.id_black_player = game_data['id_black_player']
        game.field = game_data['field']
        game.turn = game_data['turn']
        game.last_turn = game_data['last_turn']
        game.penult_turn = game_data['penult_turn']
        game.game_over = game_data['game_over']
        game.turn_number = game_data['turn_number']
        return game

    def __get_inversed_turn(self):
        return 'white' if self.turn == 'black' else 'black'

    def __get_user_id_by_color(self, color):
        if color == 'white':
            return self.id_white_player
        if color == 'black':
            return self.id_black_player

    def __get_field_index(self, x, y):
        return int(y) * self.field_size + int(x)

    def __field_to_matrix(self):
        print("ftm", self.field)
        return [[self.field[self.__get_field_index(x, y)].lower() for y in range(self.field_size)] for x in range(self.field_size)]

    def __change_cell(self, content, x, y):
        index = self.__get_field_index(x, y)
        self.__change_cell_by_index(index, content)

    def __change_cell_by_index(self, index, content):
        field_list = list(self.field)
        field_list[index] = content
        self.field = "".join(field_list)

    def __get_surrounding_groups(self, x, y, color):
        groups = []
        processed_cells = [[False for x in range(self.field_size)] for y in range(self.field_size)]
        if x - 1 >= 0 and self.field[self.__get_field_index(x - 1, y)] == color and processed_cells[x - 1][y] is False:
            groups.append(StoneGroup(x - 1, y, self.__field_to_matrix(), processed_cells))
        if (x + 1 < self.field_size and self.field[self.__get_field_index(x + 1, y)] == color and
                processed_cells[x + 1][y] is False):
            groups.append(StoneGroup(x + 1, y, self.__field_to_matrix(), processed_cells))
        if y - 1 >= 0 and self.field[self.__get_field_index(x, y - 1)] == color and processed_cells[x][y - 1] is False:
            groups.append(StoneGroup(x, y - 1, self.__field_to_matrix(), processed_cells))
        if (y + 1 < self.field_size and self.field[self.__get_field_index(x, y + 1)] == color and
                processed_cells[x][y + 1] is False):
            groups.append(StoneGroup(x, y + 1, self.__field_to_matrix(), processed_cells))
        return groups

    def __reset_marked_stone(self):
        self.field = self.field.lower()

    def reset_territory(self):
        self.field = self.field.replace('e', '0')
        self.field = self.field.replace('k', '0')

    def get_opposite_user_id(self, id_user):
        return self.id_black_player if self.id_white_player == id_user else self.id_white_player

    def stone_has_liberties(self, x, y, color=None):
        cell_contents = ['0']
        if color:
            cell_contents.append(color)
        if x - 1 >= 0 and self.field[self.__get_field_index(x - 1, y)] in cell_contents:
            return True
        if x + 1 < self.field_size and self.field[self.__get_field_index(x + 1, y)] in cell_contents:
            return True
        if y - 1 >= 0 and self.field[self.__get_field_index(x, y - 1)] in cell_contents:
            return True
        if y + 1 < self.field_size and self.field[self.__get_field_index(x, y + 1)] in cell_contents:
            return True
        return False

    def get_data(self, id_user):
        data = {'field': self.field, 'field_size': self.field_size, 'your_turn': False,
                'waiting_for_player': False, 'game_over': self.game_over, 'turn_number': self.turn_number}
        if (id_user == self.id_white_player and self.turn == 'white' or
                id_user == self.id_black_player and self.turn == 'black'):
            data['your_turn'] = True
        if not self.id_white_player or not self.id_black_player:
            data['your_turn'] = False
            data['waiting_for_player'] = True
            invite = self.server.database.find_one('game_invite', {'id_game': self.id})
            if invite:
                data['invite'] = invite['code']
        if id_user == self.id_white_player:
            data['color'] = 'white'
        if id_user == self.id_black_player:
            data['color'] = 'black'
        return data

    def save(self):
        fields_dict = {'field': self.field, 'turn': self.turn, 'id_white_player': self.id_white_player,
                       'id_black_player': self.id_black_player, 'field_size': self.field_size,
                       'last_turn': self.last_turn, 'penult_turn': self.penult_turn, 'game_over': self.game_over,
                       'turn_number': self.turn_number}
        if self.id is None:
            # New game
            self.id = self.server.database.insert('game', fields_dict)
            if not self.id_white_player or not self.id_black_player:
                self.invite = Utilities.random_string(4)
                self.server.database.insert('game_invite', {'id_game': self.id, 'code': self.invite})
        else:
            rows = self.server.database.update('game', {'id': self.id}, fields_dict)

    def get_by_invite(server, invite):
        game_data = server.database.find_one('game', {'id': invite['id_game']})
        if not game_data:
            return None
        return Game.__construct(server, game_data)

    def get_by_id(server, id_game):
        game_data = server.database.find_one('game', {'id': id_game})
        if not game_data:
            return None
        return Game.__construct(server, game_data)

    def add_player(self, user):
        if self.has_player(user['id']):
            return False
        result = False
        if not self.id_white_player:
            self.id_white_player = user['id']
            result = True
        if not self.id_black_player:
            self.id_black_player = user['id']
            result = True
        if result:
            Game.event_system.add(self.id, self.get_current_user_id(), {'type': 'your_turn', 'data': ()})
        return result

    def has_player(self, id_user):
        if self.id_white_player == id_user or self.id_black_player == id_user:
            return True
        return False

    def put_stone(self, id_user, x, y):
        if id_user != self.get_current_user_id():
            return False
        index = self.__get_field_index(x, y)
        if self.field[index] != '0' or Utilities.join((x, y)) == self.penult_turn:
            return False
        field_backup = self.field
        self.__reset_marked_stone()
        self.__change_cell_by_index(index, self.turn[0:1].upper())
        cur_group = StoneGroup(x, y, self.__field_to_matrix())
        if not cur_group.has_liberties(self):
            group_dead = False
            print (self.field)
            print (self.__field_to_matrix())
            print ("group_dead", cur_group)
            for group in self.__get_surrounding_groups(x, y, self.__get_inversed_turn()[0:1]):
                if not group.has_liberties(self):
                    group_dead = True
                    break
            if not group_dead:
                self.field = field_backup
                return False

        dead_stones = self.process_dead_groups()
        self.next_turn((x, y), dead_stones)
        self.save()
        if not self.game_over:
            Game.event_system.add(self.id, self.get_current_user_id(), {'type': 'put', 'data': (x, y, self.__get_inversed_turn())})
        return True

    def check_game_end(self):
        if self.penult_turn == self.last_turn == 'pass':
            return True
        return False

    def skip_turn(self, id_user):
        if id_user != self.get_current_user_id():
            return False
        Game.event_system.add(self.id, self.get_other_user_id(), {'type': 'pass'})
        self.__reset_marked_stone()
        self.next_turn('pass')
        self.save()
        return True

    def next_turn(self, cur_turn, dead_stones=[]):
        self.penult_turn = self.last_turn
        if isinstance(cur_turn, tuple):
            cur_turn = Utilities.join(cur_turn)
        self.last_turn = cur_turn
        self.turn_number += 1
        Game.event_system.add(self.id, 'all', {'type': 'turn_number', 'data': self.turn_number})
        self.add_move_to_history(cur_turn, dead_stones)
        if self.check_game_end():
            self.turn = ''
            self.game_over = True
            self.calc_territory()
            Game.event_system.add(self.id, 'all', {'type': 'game_over', 
                'data': (self.field, {'black_score': 1, 'white_score': 2})})
        else:
            self.turn = self.__get_inversed_turn()
            Game.event_system.add(self.id, self.get_current_user_id(), {'type': 'your_turn', 'data': ()})

    def get_current_user_id(self):
        return self.__get_user_id_by_color(self.turn)

    def get_other_user_id(self):
        return self.__get_user_id_by_color(self.__get_inversed_turn())

    def process_dead_groups(self):
        processed_cells = [[0 for x in range(self.field_size)] for y in range(self.field_size)]
        field_color = self.__get_inversed_turn()[0:1]
        groups = []
        for x in range(self.field_size):
            for y in range(self.field_size):
                index = self.__get_field_index(x, y)
                if (self.field[index] == field_color) and (processed_cells[x][y] is not True):
                    groups.append(StoneGroup(x, y, self.__field_to_matrix(), processed_cells))
        die_events = []
        dead_stones = []
        for g in groups:
            if not g.has_liberties(self):
                for x, y in g.stones:
                    self.__change_cell('0', x, y)
                    die_events.append({'type': 'die', 'data': (x, y)})
                    dead_stones.append((x, y))
        if die_events:
            Game.event_system.add(self.id, 'all', die_events)
        return dead_stones

    def send_message(self, user, message):
        if self.server.database.insert('message',
            {'id_game': self.id, 'id_user': user['id'], 'text': message}):
        
            Game.event_system.add(self.id, self.get_opposite_user_id(user['id']), 
                    {'type': 'message', 'data': Utilities.create_message(user, message, False)})

    def get_messages(self, user):
        users = {user['id']: user}
        id_second_user = self.get_opposite_user_id(user['id'])
        users[id_second_user] = self.server.database.find_one('user', {'id': id_second_user})
        messages = self.server.database.find_many('message', {'id_game': self.id})
        result = []
        for message in messages:
            m = {'date': Utilities.format_datetime(message['create_date']), 'user': users[message['id_user']]['login'], 'text': message['text'], 
                'mine': message['id_user'] == user['id']}
            result.append(m)
        return result

    def emulate(self, moves, backwards):
        if not moves:
            return
        if backwards:
            prev_move, *moves = moves
            moves.reverse()
        for move in moves:
            self.__reset_marked_stone()
            print(move['stone_coords'])
            if move['stone_coords'] != 'pass':
                self.__change_cell('0' if backwards else move['color'].upper(), *move['stone_coords'].split(','))
            deads = json.loads(move['deads'])
            if deads:
                for coords in deads:
                    color = '0'
                    if backwards:
                        color = 'w' if move['color'] == 'b' else 'b'
                    self.__change_cell(color, *coords)
        if backwards:
            self.__reset_marked_stone()
            if prev_move['stone_coords'] != 'pass':
                self.__change_cell(prev_move['color'].upper(), *prev_move['stone_coords'].split(','))

    def calc_territory(self):
        self.field = ''.join([random.choice('ek') if cell == '0' else cell for cell in self.field])

    def add_move_to_history(self, move, dead_stones):
        self.server.database.insert('moves_history', 
            {'id_game': self.id, 'turn_number': self.turn_number, 'color': self.turn[0], 
            'stone_coords': move, 'deads': json.dumps(dead_stones, separators=(',', ':'))})
