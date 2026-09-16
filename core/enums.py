from enum import Enum as PyEnum


class Levels(str, PyEnum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class Topics(str, PyEnum):
    GEOGRAPHY = 'geography'
    HISTORY = 'history'
    CURRENT_AFFAIRS = 'current_affairs'
    MOVIES = 'movies'
    FOOD = 'food'

class Status(str, PyEnum):
    ACTIVE = 'active'
    ENDED = 'ended'
