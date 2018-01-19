from go_http_request import GoHTTPRequest, ThreadedHTTPServer
from event_system import EventSystem
from goserver_instance import GoServerInstance
from game import Game


class GoServer():
    def __init__(self):
        GoServerInstance.event_system = Game.event_system = GoServer.event_system = EventSystem()
        print('starting server...')
        server_address = ('', 61366)

        httpd = ThreadedHTTPServer(server_address, GoHTTPRequest)
        print('running server...')
        httpd.serve_forever()
