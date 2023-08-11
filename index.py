import pygame
import json
import random
import queue

# Initialize Pygame
pygame.init()

# Set the dimensions of the window
WIDTH = 900
HEIGHT = 700

# Sizes
SQUARE_BIG = 80
SQUARE_SMALL = 50

# Game values
GO_BONUS = 100

# UI
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Create the Pygame window
window = pygame.display.set_mode((WIDTH, HEIGHT))

## Font ##
# Set up fonts
font = pygame.font.Font(None, 24)  # You can specify a font file or use None for the default font

## Classes ##

# class Property:
#     def __init__(self, name, cost, rent, housePrice):
#         self.name = name
#         self.cost = cost
#         self.rent = rent
#         self.actualRent = 0
#         self.housePrice = housePrice

#         self.owner = 0
#         self.hotelsAmount = 0

delayTime = 0

class Player:
    def __init__(self, id):
        self.position = 0
        self.previousPosition = 0
        self.screenPosition = (0, 0)
        self.lastRender = 0
        self.money = 1000
        self.properties = []
        self.housesOwned = 0
        self.id = id
        self.cards = []
        self.state = 'free'

        if id == 1:
            self.color = "#ff0000"
            self.buyColor = (150, 0 , 0)
        else:
            self.color = (0, 0, 255)
            self.buyColor = (0, 0 , 150)
        self.textX = 0 if id == 1 else WIDTH // 2

    def executeTurn(self):
        global dices 
        dices = [random.randint(1, 6), random.randint(1, 6)]

        if self.state == 'arrested':
            if dices[0] == dices[1]:
                self.state = 'free'
            else:
                return
            
        self.setPosition(self.position + dices[0] + dices[1])

        if board[self.position]['type'] == 'property':
            self.checkProperty()
        elif board[self.position]['type'] == 'chance':
            global chance
            chance.getCard(self)
        elif board[self.position]['type'] == 'go-to-jail':
            self.setPosition(10)
            self.state = 'arrested'

    def setPosition(self, newPosition):
        self.previousPosition = self.position
        self.position = newPosition

        if self.position > 39:
            self.position -= 40
            self.money += GO_BONUS

    def setScreenPosition(self):
        self.screenPosition = board[self.previousPosition]['center']

    def checkProperty(self):
        property = board[self.position]
        if property['owner'] == 0: # no owner
            self.buyProperty()
            
        elif property['owner'] != self.id:
            self.money -= property['rent'][property['actualRent']]
            players[property['owner']-1].money += property['rent'][property['actualRent']]
            if self.money < 0:
                global running
                print("Player " + str(self.id) + " lost")
                running = False

        elif property['owner'] == self.id:
            self.buyHouse()

    def buyProperty(self):
        property = board[self.position]

        if self.money >= property['cost']:
            property['owner'] = self.id
            property['bigColor'] = self.buyColor
            self.money -= property['cost']
            self.properties.append(self.position)

    def buyHouse(self):
        property = board[self.position]
        if self.money >= property['house'] and property['actualRent'] < 5:
            self.money -= property['house']
            property['actualRent'] += 1
            self.housesOwned += 1

    def checkMoney(self):
        if self.money < 0:
            global running
            print("Player " + str(self.id) + " lost")
            running = False

    def renderText(self):
        width = 0
        texts = [
            "Player " + str(self.id),
            "Money: " + str(self.money),
            "Position " + str(self.position)
        ]
        for string in texts:
            text = font.render(string, True, (255, 255, 255))
            window.blit(text, (self.textX, width))
            width += 20

    def renderPosition(self):
        renderDelay = 100
        if self.position != self.previousPosition:
            if self.lastRender + renderDelay < pygame.time.get_ticks():
                self.previousPosition += 1
                if self.previousPosition > 39:
                    self.previousPosition -= 40
                self.lastRender = pygame.time.get_ticks()
        self.setScreenPosition()
        pygame.draw.rect(window, self.color, (self.screenPosition, (25, 25)))


with open('chance.json', 'r') as json_file:
    chanceJson = json.load(json_file)

class CardDeck:

    def __init__(self, d):
        self.deck = queue.Queue()
        random.shuffle(d)
        for card in d:
            self.deck.put(card)
        self.card = 0

    def getCard(self, player):
        self.card = self.deck.get()
        if not self.card:
            print("Error: No cards to get from deck!")
            return
        print("Getting card. Type: " + str(self.card['type']))
        self.renderCard()
        self.checkCardType(player)
        self.deck.put(self.card)
        self.card = 0

    def checkCardType(self, player):
        if self.card['type'] == 'advance':
            positionToGo = 0

            # if you're finding a railroad or utility, find 
            # the next one then go
            if not isinstance(self.card['amount'], int):
                squareType = board[player.position]['type']
                i = 0
                while squareType != self.card['amount']:
                    i += 1
                    if i + player.position > 39:
                        i -= 40
                    squareType = board[player.position + i]['type']
                positionToGo = player.position + i
            else:
                positionToGo = self.card['amount']
            if player.position > positionToGo:
                player.money += GO_BONUS
            player.setPosition(positionToGo)
        
        elif self.card['type'] == 'earn':
            player.money += self.card['amount'] 
        elif self.card['type'] == 'spend':
            player.money -= self.card['amount']
        elif self.card['type'] == 'jail-card':
            player.cards.append(self.card)
        elif self.card['type'] == 'jail':
            player.setPosition(10)
            player.state = 'arrested'
        elif self.card['type'] == 'earn-each-player':
            for adversary in players:
                adversary.money -= self.card['amount']
                player.money += self.card['amount']
                adversary.checkMoney()
        elif self.card['type'] == 'repairs':
            player.money -= player.housesOwned * 40
            player.checkMoney()
        elif self.card['type'] == 'back':
            player.position -= 3
            player.previousPosition -= 3
        elif self.card['type'] == 'spend-each-player':
            for adversary in players:
                adversary.money += self.card['amount']
                player.money -= self.card['amount']
                player.checkMoney()

    def renderCard(self):
        pygame.draw.rect(window, WHITE, ((WIDTH // 2 - 100, HEIGHT // 2 - 100), (400, 200)))
        text = font.render(self.card['description'], True, BLACK)
        window.blit(text, (WIDTH // 2 - 50, HEIGHT // 2))
        print("Rendering card")
        pygame.display.flip()
        pygame.time.delay(2000)
        
# Open the JSON board file
with open('data.json', 'r') as json_file:
    board = json.load(json_file)

position = [800, 600]
addAxis = 1
valueToAdd = 50

for i in range(len(board)):
    if i % 10 == 0:
        board[i]['size'] = (80, 80)
        board[i]['bigColor'] = (0, 255, 0)

        if i <= 20:
            position[addAxis] -= 30

        addAxis = 1 if addAxis == 0 else 0
        SQUARE_BIG, SQUARE_SMALL = SQUARE_SMALL, SQUARE_BIG
        if i == 20:
            valueToAdd *= -1
        # if valueToAdd > 0:
        #     position[addAxis] -= 30
        # else:
        #     position[addAxis] += 30
    else:
        if i > 20 and i % 10 == 1:
            position[addAxis] += 30
        board[i]['size'] = (SQUARE_BIG, SQUARE_SMALL)
        if i % 2:
            board[i]['bigColor'] = (0, 4*i, 0)
        else:
            board[i]['bigColor'] = (0, 4*i, 0)

    board[i]['position'] = (position[0], position[1])
    board[i]['center'] = ( position[0] + SQUARE_BIG / 2, position[1] + SQUARE_SMALL / 2 )

    if board[i]['type'] == 'property':
        p = board[i]
        board[i]['owner'] = 0
        board[i]['housesAmount'] = 0
        board[i]['actualRent'] = 0
        board[i]['colorRect'] = {'size': 0, 'color': 0}
        if SQUARE_BIG < SQUARE_SMALL:
            board[i]['colorRect']['size'] = (SQUARE_BIG, 20)
        else:
            board[i]['colorRect']['size'] = (20, SQUARE_SMALL)
        board[i]['colorRect']['color'] = board[i]['color']
    if board[i]['type'] == 'chance':
        board[i]['bigColor'] = (255, 255, 255)

    position[addAxis] -= valueToAdd
        

# Set the window title
pygame.display.set_caption("Monopoly")

players = [Player(1), Player(2)]
chance = CardDeck(chanceJson)

playerTurn = 0

turnCooldown = 1000
lastTurn = pygame.time.get_ticks()

dices = [0, 0]

# Game loop
next_round = False
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x:
                running = False
            elif event.key == pygame.K_f:
                next_round = True

    # somente executar o turno se não estiver pausado em delay

    # Clear the screen
    window.fill((0, 0, 0))  # Fill with black

    for square in board:
        pygame.draw.rect(window, square['bigColor'], (square['position'], square['size']))
        if 'colorRect' in square:
            pygame.draw.rect(window, square['colorRect']['color'], (square['position'], square['colorRect']['size']))

    now = pygame.time.get_ticks()
    if lastTurn + turnCooldown < now and next_round:
            lastTurn = now
            next_round = False
            #Check if turn repeats
            players[playerTurn].executeTurn()
            if dices[0] != dices[1]:
                playerTurn += 1
                if playerTurn >= len(players):
                    playerTurn = 0

    for player in players:
        player.renderText()
        player.renderPosition()

    text = font.render("Dice: " + str(dices[0] + dices[1]), True, (255, 255, 255))
    window.blit(text, (WIDTH // 2, HEIGHT // 2))
    
    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
