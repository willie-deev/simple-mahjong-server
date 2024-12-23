from CardType import CardType


class CardUtils:
	def __int__(self):
		pass
def checkCanChow(cardTypes: list[CardType]):
	testCardTypes = cardTypes.copy()
	sortCardTypes(testCardTypes)
	checkCardType: str = getCardTypeWithoutNumber(testCardTypes[0])
	if len(testCardTypes) != 3:
		return False
	if checkIsNumberCard(testCardTypes[0]) is False:
		return False
	for card in testCardTypes:
		if getCardTypeWithoutNumber(card) != checkCardType:
			return False
	if testCardTypes[2].value - testCardTypes[1].value == 1 and testCardTypes[1].value - testCardTypes[0].value == 1:
		return True
	return False

def checkIsNumberCard(cardType: CardType):
	cardName = cardType.name
	if "CHARACTER" in cardName or "DOT" in cardName or "BAMBOO" in cardName:
		return True
	return False

def getCardTypeWithoutNumber(cardType: CardType) -> str | None:
	if "CHARACTER" in cardType.name:
		return "CHARACTER"
	elif "DOT" in cardType.name:
		return "DOT"
	elif "BAMBOO" in cardType.name:
		return "BAMBOO"
	else:
		return None

def sortCardTypes(cardTypes: list[CardType]):
	cardTypes.sort(key=lambda v: v.value, reverse=False)

if __name__ == "__main__":
	cardTypes = [CardType.BAMBOO_2, CardType.BAMBOO_5, CardType.BAMBOO_4]
	print(checkCanChow(cardTypes))