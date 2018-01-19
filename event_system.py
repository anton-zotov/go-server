import time


class EventSystem():
    def __init__(self):
        self.events = {}
        self.locked = False

    def __lock(self):
        """We don't want the events dict to be changed while we are working with it"""
        while self.locked:
            time.sleep(0.01)
        self.locked = True

    def __release(self):
        """We are done editing events"""
        self.locked = False

    def add(self, id_game, id_user, event):
        """Add an event in game id_game for user id_user"""
        self.__lock()
        if id_game not in self.events:
            self.events[id_game] = {}
        t = time.time()
        if t not in self.events[id_game]:
            self.events[id_game][t] = []
        if isinstance(event, list):  # We got a list
            for e in event:
                self.events[id_game][t].append((id_user, e))
        else:
            self.events[id_game][t].append((id_user, event))
        self.__release()

    def get(self, id_game, id_user, last_update):
        """Get events in game id_game for user id_user since last_update"""
        if id_game not in self.events:
            return []
        result = []
        for t, event_list in self.events[id_game].items():
            if t >= last_update:
                for event_user, event_data in event_list:
                    if event_user == id_user or event_user == 'all':
                        result.append(event_data)
        return result

    def clear_old_events(self):
        self.__lock()
        clear_interval = 15
        current = time.time()
        for id_game, game_events in self.events.copy().items():
            for t in game_events.copy():
                if current - t >= clear_interval:
                    del game_events[t]
            if len(game_events) == 0:
                del self.events[id_game]
        self.__release()
