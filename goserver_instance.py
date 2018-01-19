import time
import datetime
from game import Game
from utilities import Utilities
from database import Database, Criteria


class GoServerInstance():
    def __init__(self):
        self.database = Database()

    def __add_user(self, login, password):
        return self.database.insert('user', {'login': login, 'password': password})

    def __user_exist(self, login):
        return self.database.count('user', {'login': login}) > 0

    def __get_user_by_credentials(self, login, password):
        return self.database.find_one('user', {'login': login, 'password': password})

    def __get_user_by_token(self, token, ip):
        session = self.database.find_one('session', {'token': token, 'ip': ip})
        if not session:
            return False
        return self.database.find_one('user', {'id': session['id_user']})

    def __create_session(self, id_user, ip):
        token = Utilities.random_string(20)
        self.database.insert('session', {'id_user': id_user, 'ip': ip, 'token': token})
        return token

    def __get_game(self, http_con, data):
        user = self.__get_user_by_token(data['token'], http_con.client_address[0])
        if not user:
            http_con.try_response(500, {'success': False, 'message': 'Invalid token'})
            return (False, None, None)
        game = Game.get_by_id(self, data['id_game'])
        if not game or not game.has_player(user['id']):
            http_con.try_response(500, {'success': False, 'message': 'Invalid game id'})
            return (False, None, None)
        return (True, user, game)

    def register(self, http_con, data):
        if self.__user_exist(data['login']):
            message = {'success': False, 'message': 'User already exists'}
        else:
            id_user = self.__add_user(data['login'], data['password'])
            if id_user:
                token = self.__create_session(id_user, http_con.client_address[0])
                message = {'success': True, 'token': token}
            else:
                message = {'success': False, 'message': 'Cannot create user'}
        http_con.try_response(200, message)

    def login(self, http_con, data):
        user = self.__get_user_by_credentials(data['login'], data['password'])
        if user:
            token = self.__create_session(user['id'], http_con.client_address[0])
            message = {'success': True, 'token': token}
        else:
            message = {'success': False, 'message': 'login or password is incorrect'}
        http_con.try_response(200, message)

    def logout(self, http_con, data):
        self.database.delete('session', {'token': data['token']})
        message = {'success': True, 'message': 'logged out'}
        http_con.try_response(200, message)

    def new_game(self, http_con, data):
        user = self.__get_user_by_token(data['token'], http_con.client_address[0])
        if not user:
            return http_con.try_response(500, {'success': False, 'message': 'Invalid token'})
        game = Game(self, data['field_size'])
        game.id_black_player = user['id']
        game.save()
        message = {'success': True, 'id_game': game.id, 'invite': game.invite}
        http_con.try_response(200, message)

    def join_invite(self, http_con, data):
        user = self.__get_user_by_token(data['token'], http_con.client_address[0])
        if not user:
            return http_con.try_response(500, {'success': False, 'message': 'Invalid token'})
        game_invite = self.database.find_one('game_invite', {'code': data['invite']})
        if not game_invite:
            return http_con.try_response(500, message={'success': False, 'message': 'Invalid invite'})
        game = Game.get_by_invite(self, game_invite)
        if not game:
            return http_con.try_response(500, message={'success': False, 'message': 'Invalid invite'})
        if not game.add_player(user):
            return http_con.try_response(500, message={'success': False, 'message': 'Unable to join game'})
        game.save()
        self.database.delete('game_invite', {'id': game_invite['id']})
        http_con.try_response(200, {'success': True, 'id_game': game.id})

    def get_active_games(self, http_con, data):
        user = self.__get_user_by_token(data['token'], http_con.client_address[0])
        if not user:
            return http_con.try_response(500, {'success': False, 'message': 'Invalid token'})
        q = Criteria()
        q.add_search({'id_white_player': user['id'], 'id_black_player': user['id']}, fields_join='OR')
        q.add_search({'game_over': False})
        games = self.database.find_many('game', q)
        game_list = []
        for game in games:
            name = game['id']
            game_list.append({'id': game['id'], 'name': name, 'create_date': Utilities.format_datetime(game['create_date']), 'current_turn': game['turn']})
        http_con.try_response(200, {'success': True, 'games': game_list})

    def get_game_data(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            http_con.try_response(200, {'success': True, 'game_data': game.get_data(user['id']),
                                        'timestamp': time.time()})

    def put_stone(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            if game.put_stone(user['id'], data['x'], data['y']):
                return http_con.try_response(200, {'success': True})
        return http_con.try_response(200, {'success': False})

    def get_game_update(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            for i in range(100):
                time.sleep(0.1)
                events = GoServerInstance.event_system.get(game.id, user['id'], data['last_update'])
                if i % 10 == 0:
                    GoServerInstance.event_system.clear_old_events()
                if events:
                    break
            http_con.try_response(200, {'success': True,
                                        'events': events,
                                        'timestamp': time.time()})

    def skip_turn(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            if game.skip_turn(user['id']):
                return http_con.try_response(200, {'success': True})
        return http_con.try_response(200, {'success': False})

    def send_message(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            game.send_message(user, data['message'])
            return http_con.try_response(200, 
                {'success': True, 'message': Utilities.create_message(user, data['message'], True)})
        return http_con.try_response(200, {'success': False})

    def get_messages(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            messages = game.get_messages(user)
            return http_con.try_response(200, {'success': True, 'messages': messages})
        return http_con.try_response(200, {'success': False})

    def get_history(self, http_con, data):
        success, user, game = self.__get_game(http_con, data)
        if success:
            backwards = False
            if data['turn'] > game.turn_number / 2:
                backwards = True
            q = Criteria()
            q.add_search({'id_game': game.id})
            if backwards:
                q.add_condition(('turn_number', '>=', data['turn']))
            else:
                q.add_condition(('turn_number', '<=', data['turn']))
            moves = self.database.find_many('moves_history', q)
            temp_game = Game(False, game.field_size)
            if backwards:
                temp_game.field = game.field
                if len(moves) > 1:
                    temp_game.reset_territory()
            temp_game.emulate(moves, backwards)
            return http_con.try_response(200,
                {'success': True, 'game_data': {'field':temp_game.field}})
        return http_con.try_response(200, {'success': False})
