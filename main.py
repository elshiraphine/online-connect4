import pygame
import math
from ast import literal_eval
import json

from board import Board
import minimax

import socket
import sys
from threading import Thread

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip_address = "127.0.0.1"
port = 8081

server.connect((ip_address, port))

client_id = int(server.recv(2048).decode().split()[-1])
print("Connected to server with ID", client_id)

json_data = {
    "game": []
}

# Get initial game data from server
data = server.recv(2048).decode()
try:
    json_data = json.loads(data)
except ValueError as e:
    sys.stdout.write(data)

group_id = 0

def send_msg(sock, inp=-1):
    while True:
        if inp == -1:
            continue

        sock.send((str(client_id) + ":" + inp).encode())
        inp = -1

def recv_msg(sock):
    while True:
        data = sock.recv(2048).decode()

        try:
            global json_data
            json_data = json.loads(data)
        except ValueError as e:
            sys.stdout.write(data)


BOARD_WIDTH = 7
BOARD_HEIGHT = 6

WINDOW_SIZE = 800

TILE_SIZE = 100

BLUE = (20, 50, 150)
BLACK = (30, 30, 30)
RED = (193, 18, 31)
YELLOW = (255, 209, 102)


class Button:
    gameMode = 0

    def __init__(self, text, width, height, pos, elevation):
                
        #Core attributes 
        self.pressed = False
        self.elevation = elevation
        self.dynamic_elecation = elevation
        self.original_y_pos = pos[1]

        gui_font = pygame.font.SysFont(None,30)

        # top Rectangle
        self.top_rect = pygame.Rect(pos, (width, height))
        self.top_color = '#FFC20E'

        # bottom rectangle 
        self.bottom_rect = pygame.Rect(pos,(width,height))
        self.bottom_color = '#86230E'

        #text
        self.text_surf = gui_font.render(text, True, '#000000')
        self.text_rect = self.text_surf.get_rect(center = self.top_rect.center)
    
    def draw(self, surface):
        # Initiate button display state
        action = False

        # elevation logic 
        self.top_rect.y = self.original_y_pos - self.dynamic_elecation
        self.text_rect.center = self.top_rect.center 

        self.bottom_rect.midtop = self.top_rect.midtop
        self.bottom_rect.height = self.top_rect.height + self.dynamic_elecation
                
        pygame.draw.rect(surface,self.bottom_color, self.bottom_rect,border_radius = 12)
        pygame.draw.rect(surface,self.top_color, self.top_rect,border_radius = 12)
        surface.blit(self.text_surf, self.text_rect)

        mouse_pos = pygame.mouse.get_pos()
        if self.top_rect.collidepoint(mouse_pos):
            self.top_color = '#D74B4B'
            if pygame.mouse.get_pressed()[0]:
                self.dynamic_elecation = 0
                self.pressed = True
            else:
                self.dynamic_elecation = self.elevation
                if self.pressed:
                    action = True
                    print('click')
                    self.pressed = False
        else:
            self.dynamic_elecation = self.elevation
            self.top_color = '#FFC20E'


        return action

    def update(self, new_text, new_position):
        self.image = pygame.font.SysFont("Arial", 48, bold=True).render(new_text, True, (0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topleft = new_position


class Game:
    gameMode = 0

    def __init__(self, tile_size):
        self.tile_size = tile_size

    def init_pygame(self):
        pygame.init()
        self.width = BOARD_WIDTH * self.tile_size
        self.height = (BOARD_HEIGHT + 1) * self.tile_size
        self.size = (self.width, self.height)
        self.screen = pygame.display.set_mode(self.size)
        self.RADIUS = int(self.tile_size / 2 - 5)

        pygame.display.update()

        self.textFont = pygame.font.SysFont("Helvetica", 48, bold=True)

    # Human turn
    def humanChoice(self, board, slot):
        # Pick slot/column
        while True:
            if board.checkOpen(slot) == 1:
                return slot
            else:
                print("Slot is full")

    def choice(self, player, board, depth, letter, slot=0):
        if Game.gameMode == 1 or player == 1:
            return self.humanChoice(board, slot)
        else:
            boardArray = board.getArray()
            output = minimax.minimaxChoice(boardArray, depth, letter)
            print("%s Pick slot %d" % (letter, output + 1))
            return output

    def draw_board(self, board):
        for c in range(BOARD_HEIGHT):
            for r in range(BOARD_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    BLUE,
                    (
                        r * self.tile_size,
                        c * self.tile_size + self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    ),
                )
                pygame.draw.circle(
                    self.screen,
                    BLACK,
                    (
                        int(r * self.tile_size + self.tile_size / 2),
                        int(c * self.tile_size + self.tile_size + self.tile_size / 2),
                    ),
                    self.RADIUS,
                )

        for c in range(BOARD_HEIGHT):
            for r in range(BOARD_WIDTH):
                if board[r][c] == "X":
                    pygame.draw.circle(
                        self.screen,
                        RED,
                        (
                            int(r * self.tile_size + self.tile_size / 2),
                            self.height - int(c * self.tile_size + self.tile_size / 2),
                        ),
                        self.RADIUS,
                    )
                elif board[r][c] == "O":
                    pygame.draw.circle(
                        self.screen,
                        YELLOW,
                        (
                            int(r * self.tile_size + self.tile_size / 2),
                            self.height - int(c * self.tile_size + self.tile_size / 2),
                        ),
                        self.RADIUS,
                    )
        pygame.display.update()

    def draw_message(self, message, color):
        pygame.draw.rect(self.screen, BLACK, (0, 0, self.width, self.tile_size))
        text = self.textFont.render(message, True, color)
        text_rect = text.get_rect(center=(self.width / 2, self.tile_size / 2))
        self.screen.blit(text, text_rect)

    def run(self):
        if Game.gameMode == 2:
            turnMessage = "Computer turn"
        else:
            turnMessage = "Player 2 turn"

        gameBoard = Board()
        running = True
        turns = 0
        depth = 6

        # set Background
        bgImage = pygame.image.load("img/bg.png").convert_alpha()
        bgSize = pygame.transform.scale(bgImage, (800, 800))
        self.screen.blit(bgSize, (0,0))

        # Load Button
        pvp = pygame.image.load("img/pvp.png").convert_alpha()
        pvc = pygame.image.load("img/pvc.png").convert_alpha()
        online = pygame.image.load("img/online.png").convert_alpha()
        play = pygame.image.load("img/play.png").convert_alpha()
        create = pygame.image.load("img/create.png").convert_alpha()
        join = pygame.image.load("img/join.png").convert_alpha()
        roomSelection = pygame.image.load("img/example room 0.png").convert_alpha()
        quit = pygame.image.load("img/quit.png").convert_alpha()
        back = pygame.image.load("img/back.png").convert_alpha()
        close = pygame.image.load("img/close.png").convert_alpha()

        # new Button Class
        # (self, text, width, height, pos)
        playButton = Button('Play', 200, 40, (250, 250), 5)
        pvpButton = Button('Player V Player', 160, 100, (100, 250), 5)
        pvcButton = Button('Player V AI', 160, 100, (275, 250), 5)
        onlineButton = Button('Multi Player', 160, 100, (450, 250), 5)
        quitButton = Button('Quit', 200, 40, (250, 350), 5)
        backButton = Button('Back', 100, 40, (100, 100), 5)
        closeButton = Button('Close', 100, 40, (500, 100), 5)
        createButton = Button('Create', 200, 40, (250, 250), 5)
        joinButton = Button('Join', 200, 40, (250, 320), 5)

        roomSelectionButtons = []

        x_position = 260
        y_position = 250

        button_spacing = 80

        for i, room in enumerate(json_data["game"]):
            gid = room["room"]
            button_text = "Room " + str(gid)
            button_position = (x_position, y_position)
            roomSelectionButton = Button(button_text, 200, 40, (button_position[0], button_position[1]), 5)
            roomSelectionButton.update(button_text, button_position)
            roomSelectionButtons.append(roomSelectionButton)

            y_position += button_spacing

        # Screen State
        playScreen = False
        gameModeSet = False
        roomSet = False
        roomSelection = False

        sendMessage = -1

        global board
        board = gameBoard.getArray()

        global group_id

        while running:
            for event in pygame.event.get():
                if playScreen:
                    if gameModeSet and (
                        Game.gameMode != 3
                        or (Game.gameMode == 3 and roomSet and roomSelection)
                    ):
                        # Check if game is over
                        try:
                            game_over = json_data["game"][group_id]["game_over"]
                            waiting_player = True if json_data["game"][group_id]["player"]["yellow_id"] == -1 else False

                        except:
                            game_over = False
                            waiting_player = True

                        if Game.gameMode == 3 and game_over:
                            print("Game Over")

                            # Check if client is the winner
                            if client_id == json_data["game"][group_id]["winner_id"]:
                                message = "You Win!"
                            else:
                                message = "You Lose!"

                            # Check if red win
                            if json_data["game"][group_id]["winner_id"] == json_data["game"][group_id]["player"]["red_id"]:
                                self.draw_message(message, RED)
                            else:
                                self.draw_message(message, YELLOW)

                            running = False

                        elif Game.gameMode == 3 and waiting_player:
                            self.draw_message("Waiting for player...", RED)

                        if Game.gameMode == 3 and turns > 0:
                            self.draw_board(json_data["game"][group_id]["board"])
                        else:
                            self.draw_board(board)

                        if event.type == pygame.QUIT:
                            running = False
                            server.close()
                            pygame.display.quit()
                            pygame.quit()
                            sys.exit()
                            break

                        if Game.gameMode == 2 and turns % 2 == 1:
                            print(turnMessage)
                            gameBoard.dropLetter(
                                self.choice(2, gameBoard, depth, "O"), "O"
                            )

                            if gameBoard.detectWin() == "O" and Game.gameMode == 2:
                                message = "Computer Win!"
                                print(message + "\n")
                                self.draw_message(message, YELLOW)
                                running = False

                            board = gameBoard.getArray()
                            self.draw_board(board)

                            turns += 1

                            if turns == 50:
                                print("Draw!\n")
                                running = False

                        if event.type == pygame.MOUSEMOTION and (Game.gameMode != 3 or (Game.gameMode == 3 and not waiting_player)):
                            pygame.draw.rect(
                                self.screen, BLACK, (0, 0, self.width, self.tile_size)
                            )
                            posx = int(event.pos[0]//self.tile_size*self.tile_size + self.tile_size/2)
                            if turns % 2 == 0:
                                pygame.draw.circle(
                                    self.screen,
                                    RED,
                                    (posx, int(self.tile_size / 2)),
                                    self.RADIUS,
                                )
                            else:
                                pygame.draw.circle(
                                    self.screen,
                                    YELLOW,
                                    (posx, int(self.tile_size / 2)),
                                    self.RADIUS,
                                )
                            pygame.display.update()

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            pygame.draw.rect(
                                self.screen, BLACK, (0, 0, self.width, self.tile_size)
                            )

                            posx = event.pos[0]
                            col = int(math.floor(posx / self.tile_size))

                            if Game.gameMode == 3:
                                Thread(
                                    target=send_msg,
                                    args=(
                                        server,
                                        str(col + 1),
                                    ),
                                ).start()
                                turns += 2

                                self.draw_board(json_data["game"][group_id]["board"])

                            else:
                                if turns % 2 == 0:
                                    gameBoard.dropLetter(
                                        self.choice(1, gameBoard, depth, "X", col), "X"
                                    )

                                    if gameBoard.detectWin() == "X":
                                        message = "Player 1 Win!"
                                        print(message + "\n")
                                        self.draw_message(message, RED)
                                        running = False

                                else:
                                    gameBoard.dropLetter(
                                        self.choice(2, gameBoard, depth, "O", col), "O"
                                    )

                                    if (
                                        gameBoard.detectWin() == "O"
                                        and Game.gameMode == 1
                                    ):
                                        message = "Player 2 Win!"
                                        print(message + "\n")
                                        self.draw_message(message, YELLOW)
                                        running = False

                                board = gameBoard.getArray()
                                self.draw_board(board)

                                turns += 1

                            if turns == 50:
                                print("Draw!\n")
                                self.draw_message("Draw!", BLACK)
                                running = False

                        if not running:
                            pygame.time.wait(3000)

                    elif gameModeSet and Game.gameMode == 3 and not roomSet:
                        Thread(target=recv_msg, args=(server,)).start()

                        # Display Create or Join Room Screen
                        self.screen.blit(bgSize, (0,0))
                        if createButton.draw(self.screen):
                            server.send((str(client_id) + ":1").encode())
                            roomSet = True
                            roomSelection = True
                            group_id = len(json_data["game"])
                            print("Room Created")
                        if len(json_data["game"]) > 0 and joinButton.draw(self.screen):
                            server.send((str(client_id) + ":2").encode())
                            roomSet = True
                            print("Room Joining")
                        if backButton.draw(self.screen):
                            gameModeSet = False
                        if closeButton.draw(self.screen):
                            running = False
                            server.close()
                            pygame.display.quit()
                            pygame.quit()
                            sys.exit()
                            break
                        pygame.display.update()

                    elif (
                        gameModeSet
                        and Game.gameMode == 3
                        and not roomSelection
                        and roomSet
                    ):
                        # Display Room Selection Screen
                        self.screen.blit(bgSize, (0,0))

                        for roomSelectionButton in roomSelectionButtons:
                            i = roomSelectionButtons.index(roomSelectionButton)
                            if roomSelectionButton.draw(self.screen):
                                group_id = i
                                server.send((str(client_id) + ":" + str(i)).encode())
                                roomSelection = True
                                turns += 1
                                self.screen.fill(BLACK)

                        if backButton.draw(self.screen):
                            roomSet = False
                        if closeButton.draw(self.screen):
                            running = False
                            server.close()
                            pygame.display.quit()
                            pygame.quit()
                            sys.exit()
                            break
                        pygame.display.update()

                    else:
                        # Display Game Mode Screen
                        pygame.time.wait(20)
                        self.screen.blit(bgSize, (0,0))
                        pygame.event.wait(10)
                        if pvpButton.draw(self.screen):
                            Game.gameMode = 1
                            print("Masuk mode 1")
                            gameModeSet = True
                            self.screen.fill(BLACK)
                        if pvcButton.draw(self.screen):
                            Game.gameMode = 2
                            print("Masuk mode 2")
                            gameModeSet = True
                            self.screen.fill(BLACK)
                        if onlineButton.draw(self.screen):
                            Game.gameMode = 3
                            print("Masuk mode 3")
                            gameModeSet = True
                        if backButton.draw(self.screen):
                            playScreen = False
                        if closeButton.draw(self.screen):
                            running = False
                            server.close()
                            pygame.display.quit()
                            pygame.quit()
                            sys.exit()
                            break
                        pygame.display.update()
                else:
                    # Display Home Page Screen
                    self.screen.blit(bgSize, (0,0))
                    if playButton.draw(self.screen):
                        playScreen = True
                        pygame.event.wait(10)
                    if quitButton.draw(self.screen):
                        running = False
                        server.close()
                        pygame.display.quit()
                        pygame.quit()
                        sys.exit()
                        break
                    pygame.display.update()


if __name__ == "__main__":
    game = Game(TILE_SIZE)
    game.init_pygame()

    game.run()

    pygame.display.quit()
    pygame.quit()
    Thread(target=send_msg, args=(server,)).join()
    Thread(target=recv_msg, args=(server,)).join()
    server.close()
    sys.exit()
