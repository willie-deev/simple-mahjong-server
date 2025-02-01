from itertools import combinations

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

def filterCardTypes(cardTypes: list[CardType]) -> tuple[list[CardType], list[CardType], list[CardType], list[CardType]]:
	characterList: list[CardType] = []
	dotList: list[CardType] = []
	bambooList: list[CardType] = []
	nonNumberList: list[CardType] = []
	for cardType in cardTypes:
		if "CHARACTER" in cardType.name:
			characterList.append(cardType)
		elif "DOT" in cardType.name:
			dotList.append(cardType)
		elif "BAMBOO" in cardType.name:
			bambooList.append(cardType)
		else:
			nonNumberList.append(cardType)
	return characterList, dotList, bambooList, nonNumberList

def getNonNumberCardsAllCombinableCount(cardTypes: list[CardType]) -> tuple[list, list, list]:
	testCardTypes: list[CardType] = cardTypes[:]
	pungCards: list[CardType] = []
	pairCards: list[CardType] = []
	noneCards: list[CardType] = []
	i = 0
	while i < len(testCardTypes):
		if i < len(testCardTypes) - 2 and testCardTypes[i] == testCardTypes[i + 1] and testCardTypes[i] == testCardTypes[i + 2]:
			pungCards.append(testCardTypes[i])
			i+=3
		elif i < len(testCardTypes) - 1 and testCardTypes[i] == testCardTypes[i + 1]:
			pairCards.append(testCardTypes[i])
			i+=2
		else:
			noneCards.append(testCardTypes[i])
			i += 1
	return pungCards, pairCards, noneCards

def calCardTypesCanWin(cardTypes: list[CardType], needPair = None) -> tuple[CardType | None, int] | None:
	if needPair is None:
		if len(cardTypes) % 3 == 2:
			needPair = True
		else:
			needPair = False
	cardNumbers = cardTypesToNumberList(cardTypes)
	pairs, pungs = getAllPairsPungs(cardNumbers)
	if needPair is False:
		pairs = [None]
	for pair in pairs:
		pairTestCards = cardNumbers[:]
		currentPair = None
		if pair is not None:
			currentPair = (pair, pair + 1)
			pairTestCards[pair:pair + 2] = [None, None]
		for i in range(len(pungs) + 1):
			for pungList in combinations(pungs, i):
				pungTestCards = pairTestCards[:]
				currentPungs = [(pung, pung + 1, pung + 2) for pung in pungList]
				for pung in pungList:
					pungTestCards[pung:pung + 3] = [None, None, None]
				allChowIndexList, leftCards = getAllChowIndexList(pungTestCards)
				if all(card is None for card in leftCards):
					currentChows = [tuple(chow) for chow in allChowIndexList]
					finalPairCardType: CardType | None = None
					if currentPair is not None:
						finalPairCardType = getCardTypeByNameAndNumber(getCardTypeWithoutNumber(cardTypes[0]), cardNumbers[currentPair[0]])
					finalPungCount = len(currentPungs)
					finalChowCount = len(currentChows)
					finalCombineCount = finalPungCount + finalChowCount
					return finalPairCardType, finalCombineCount
	return None

def cardTypesToNumberList(cardTypes: list[CardType]) -> list[int]:
	numberList: list[int] = []
	for cardType in cardTypes:
		numberList.append(getNumberByCardType(cardType))
	return numberList

def getNumberByCardType(cardType: CardType):
	if "CHARACTER" in cardType.name:
		number = int(cardType.name.strip("CHARACTER_"))
	elif "DOT" in cardType.name:
		number = int(cardType.name.strip("DOT_"))
	elif "BAMBOO" in cardType.name:
		number = int(cardType.name.strip("BAMBOO_"))
	else:
		return None
	return number

def getAllPairsPungs(cards: list):
	pairs = []
	pungs = []
	i = 0
	while i < len(cards) - 1:
		if cards[i] is None:
			i += 1
			continue
		if cards[i] == cards[i + 1]:
			pairs.append(i)
			if i < len(cards) - 2 and cards[i] == cards[i + 2]:
				pungs.append(i)
			i += 1
		i += 1
	return pairs, pungs

def getAllChowIndexList(cards: list):
	leftCards = cards[:]
	chows = []
	for i in range(len(cards)):
		if cards[i] is None:
			continue
		chow = getNextChowIndexList(leftCards, i)
		if chow:
			chows.append(chow)
			for index in chow:
				leftCards[index] = None
	return chows, leftCards

def getNextChowIndexList(cards: list, firstIndex):
	if cards[firstIndex] is None:
		return None
	chow = [firstIndex]
	for target in (cards[firstIndex] + 1, cards[firstIndex] + 2):
		nextIndex = getNextNumberIndex(cards, target, chow[-1] + 1)
		if nextIndex is None:
			return None
		chow.append(nextIndex)
	return chow

def getNextNumberIndex(cards: list, number: int, startFrom=0):
	for i in range(startFrom, len(cards)):
		if cards[i] == number:
			return i
		if cards[i] is not None and cards[i] > number:
			break
	return None

def getCardTypeByNameAndNumber(cardName: str, number: int) -> CardType | None:
	for cardType in CardType:
		if cardType.name == cardName + "_" + str(number):
			return cardType
	return None

def calOneTypeCanReady(cardTypes: list[CardType]) -> bool:
	cardTypeWithoutNumber = getCardTypeWithoutNumber(cardTypes[0])
	for cardType in CardType:
		if getCardTypeWithoutNumber(cardType) != cardTypeWithoutNumber:
			continue
		testCardTypes = cardTypes[:]
		testCardTypes.append(cardType)
		testCardTypes.sort(key=lambda cardType: cardType.value)
		if calCardTypesCanWin(testCardTypes) is not None:
			return True
	return False

def calCanReady(cardTypes: list[CardType]):
	characterList, dotList, bambooList, nonNumberList = filterCardTypes(cardTypes)
	pungCards, pairCards, noneCards = getNonNumberCardsAllCombinableCount(nonNumberList)
	if len(noneCards) >= 1:
		return 0
	cantWinCount = 0
	cantWinList: list[CardType] = []
	pairList: list[CardType] = pairCards

	result = calCardTypesCanWin(characterList)
	if result is None:
		cantWinCount += 1
		cantWinList = characterList
	else:
		if result[0] is not None:
			pairList.append(result[0])

	result = calCardTypesCanWin(dotList)
	if result is None:
		cantWinCount += 1
		cantWinList = dotList
	else:
		if result[0] is not None:
			pairList.append(result[0])

	result = calCardTypesCanWin(bambooList)
	if calCardTypesCanWin(bambooList) is None:
		cantWinCount += 1
		cantWinList = bambooList
	else:
		if result[0] is not None:
			pairList.append(result[0])
	if cantWinCount == 0 and len(pairList) == 1:
		return 2
	if (cantWinCount == 1 and len(pairList) == 0) or (len(pairList) == 2 and cantWinCount == 0):
		if calOneTypeCanReady(cantWinList) is True:
			return 1
		return 0
	if cantWinCount == 1 and len(pairList) == 1:
		if calOneTypeCanReady(cantWinList) is True:
			return 1
	return 0

def calCanWin(cardTypes: list[CardType]) -> bool:
	characterList, dotList, bambooList, nonNumberList = filterCardTypes(cardTypes)
	pungCards, pairCards, noneCards = getNonNumberCardsAllCombinableCount(nonNumberList)
	if len(noneCards) >= 1:
		return False
	cantWinCount = 0
	cantWinList: list[CardType] = []
	pairList: list[CardType] = pairCards

	result = calCardTypesCanWin(characterList)
	if result is None:
		cantWinCount += 1
		cantWinList = characterList
	else:
		if result[0] is not None:
			pairList.append(result[0])

	result = calCardTypesCanWin(dotList)
	if result is None:
		cantWinCount += 1
		cantWinList = dotList
	else:
		if result[0] is not None:
			pairList.append(result[0])

	result = calCardTypesCanWin(bambooList)
	if calCardTypesCanWin(bambooList) is None:
		cantWinCount += 1
		cantWinList = bambooList
	else:
		if result[0] is not None:
			pairList.append(result[0])
	if cantWinCount == 0 and len(pairList) == 1:
		return True
	return False

if __name__ == "__main__":
	cardTypes = [CardType.BAMBOO_2, CardType.BAMBOO_5, CardType.BAMBOO_4]
	print(checkCanChow(cardTypes))