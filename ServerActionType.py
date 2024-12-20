from enum import Enum


class ServerActionType(Enum):
	CHANGE_WIND = 0
	START_SEND_CARDS = 1
	START_FLOWER_REPLACEMENT = 2
	FLOWER_COUNT = 3