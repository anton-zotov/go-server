import random
import string
import datetime


class Utilities():
    def random_string(length):
        return ''.join(random.sample(string.ascii_uppercase + string.digits, length))

    def join(lst, delimeter=','):
        return delimeter.join(str(i) for i in lst)

    def create_message(user, message, mine):
    	return {
            'date': Utilities.format_datetime(datetime.datetime.now()),
            'user': user['login'], 'text': message, 'mine': mine
        }

    def format_datetime(dt):
    	return dt.strftime("%H:%M %d.%m.%y")
