from enum import Enum


class CardActionType(Enum):
	NOTHING = 0
	CHOW = 1,
	PUNG = 2,
	KONG = 3,
	READY = 4,
	WIN = 5