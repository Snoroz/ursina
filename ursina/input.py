import sys
from collections import defaultdict


class Input(object):

    def __init__(self):
        self.control = False
        self.left_control = False
        self.right_control = False

        self.shift = False
        self.left_shift = False
        self.right_shift = False

        self.alt = False
        self.left_alt = False
        self.right_alt = False

        self.held_keys = defaultdict(lambda: 0)


    def input(self, key):
        if key.endswith('up'):
            self.held_keys[key[:-3]] = 0
        else:
            self.held_keys[key] = 1


sys.modules[__name__] = Input()