from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import json
from goserver_instance import GoServerInstance


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class GoHTTPRequest(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.try_response(200, "not supported")

    def do_GET(self):
        self.try_response(200, "not supported")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf8')
        json_data = json.loads(post_data) if post_data else []
        if self.path != '/gameupdate':
            print(self.path, json_data)
        server = GoServerInstance()

        if self.path == '/login':
            server.login(self, json_data)
        if self.path == '/register':
            server.register(self, json_data)
        if self.path == '/logout':
            server.logout(self, json_data)
        if self.path == '/newgame':
            server.new_game(self, json_data)
        if self.path == '/joininvite':
            server.join_invite(self, json_data)
        if self.path == '/activegames':
            server.get_active_games(self, json_data)
        if self.path == '/gamedata':
            server.get_game_data(self, json_data)
        if self.path == '/putstone':
            server.put_stone(self, json_data)
        if self.path == '/gameupdate':
            server.get_game_update(self, json_data)
        if self.path == '/pass':
            server.skip_turn(self, json_data)
        if self.path == '/message':
            server.send_message(self, json_data)
        if self.path == '/getmessages':
            server.get_messages(self, json_data)
        if self.path == '/gethistory':
            server.get_history(self, json_data)

    def try_response(self, code, message):
        try:
            self.response(code, message)
        except:
            pass

    def response(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(message), "utf8"))
