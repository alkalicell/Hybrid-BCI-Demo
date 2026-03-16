import numpy as np
from datetime import datetime
import sys
import pygame
from pygame import Surface
from pygame.locals import *
from pathlib import Path
import imageio
from call_api import call_4_images
from final_demo import demo_4_imgs
from PIL import Image
import glob


# --- path ---
path = Path()
total_img_path = path / 'icons'
LOG_PATH = path / 'log.txt'
Calibration_path = path / 'Calibration.txt'


# --- AI ---
SAVE_FOLDER_PATH = path / 'output/printimg_raw'
OUTPUT_4img_PATH = path / 'output' / 'printimg_AIx4'

OUTPUT_LIST = []

# --- constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)



# --- classes ---
class Button():

    def __init__(self, name, color, rect, time, target_f, img=None, text=None):
        self.name = name
        self.color = color
        self.rect = rect
        self.target_f = target_f
        self.delay = 1000 / target_f
        self.time = time + self.delay
        self.show = False
        self.show_portion = 0.5
        self.time_buffer = []
        self.maxBuffer = 16
        self.font_size = 40
        self.font_color = WHITE
        if img:
            self.img = pygame.transform.scale(img, (80, 80))
        else:
            self.img = None
        if text:
            font = pygame.font.SysFont("simhei", self.font_size)
            t = font.render(text, True, self.font_color)
            self.text = t
        else:
            self.text = None

    def draw(self, screen):
        if self.show:
            pygame.draw.rect(screen, self.color, self.rect,border_radius=20)
            pygame.draw.rect(screen, BLACK, self.rect, 5,border_radius=20)
            if self.img:
                screen.blit(
                    self.img, (self.rect[0] + self.rect[2] / 2 - 40, self.rect[1] + self.rect[3] / 2 - 40))
            elif self.text:
                text_width = self.text.get_width()
                text_height = self.text.get_height()
                screen.blit(self.text, (
                    self.rect[0] + self.rect[2] / 2 - text_width / 2,
                    self.rect[1] + self.rect[3] / 2 - text_height / 2))

    def update(self, current_time):
        if current_time >= self.time:
            if self.show:
                # show
                self.time = current_time + self.delay * self.show_portion
            else:
                # no-show
                self.time = current_time + self.delay * (1 - self.show_portion)
            self.show = not self.show
            if self.show:
                self.time_buffer.append(current_time)
                if (len(self.time_buffer) > self.maxBuffer):
                    dif = np.diff(self.time_buffer)
                    actual_f = 1000 / np.mean(dif)
                    if actual_f - self.target_f > 0.05:
                        self.delay += 0.5
                    elif actual_f - self.target_f < 0.05:
                        self.delay -= 0.5
                    self.time_buffer.clear()

    # print the average time interval per blink of the button
    def observe(self):
        if (len(self.time_buffer) > 1):
            dif = np.diff(self.time_buffer)
            actual_f = 1000 / np.mean(dif)
            print(
                f" {self.name} | Sample: {len(self.time_buffer):2d} | Actual Frequency: {actual_f:.5f} Hz | Delay: {self.delay:.5f} ms    \r",
                end="\b")

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect)

class Canvas():

    def __init__(self, color, rect):
        self.color = color
        self.rect = rect
        self.canvas = Surface((rect[2], rect[3])).convert()
        self.canvas.fill(color)

    def draw(self, screen):
        screen.blit(self.canvas, (self.rect[0], self.rect[1]))
        pygame.draw.rect(screen, (100,0,200), self.rect, 1)

    def add_brush(self, color, position, size):
        pygame.draw.circle(self.canvas, color, (position[0] - self.rect[0], position[1] - self.rect[1]), size, 0)

    def add_rect(self, color, rect, size):
        pygame.draw.rect(self.canvas, color, (rect[0] - self.rect[0], rect[1] - self.rect[1], rect[2], rect[3]), size)

    def add_circle(self, color, rect, size):
        pygame.draw.ellipse(self.canvas, color, (rect[0] - self.rect[0], rect[1] - self.rect[1], rect[2], rect[3]),
                            size)

    def reset(self):
        self.canvas.fill(self.color)

    def save(self):
        current_time = datetime.now()
        time_string = current_time.strftime(f"%Y%m%d_%H%M%S")
        name = str(SAVE_FOLDER_PATH) + "/paint_" + time_string + ".png"
        pygame.image.save(self.canvas, name)
        OUTPUT_LIST.append("paint_" + time_string + ".png")
        return name

    def load(self, image_path):
        self.canvas = pygame.image.load(image_path).convert()

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect)



def main():

    # pygame initialize
    pygame.init()

    # UI Settings
    WIDTH, HEIGHT = 1000, 600
    min_width = 1000
    min_height = 600

    W1 = 200
    H1 = 120
    BACKGROUND_COLOR = 255, 255, 225
    CANVAS_COLOR = 255, 255, 255
    CAPTION = "BCI Drawing"
    MARGIN1 = 10
    MARGIN2 = 10
    BRUSH_SIZE = 15
    BRUSH_COLOR = BLACK
    move_step = 15

    CANVAS_W = WIDTH - MARGIN1 * 3 - W1 #1000 - 10*2 -200 = 780
    CANVAS_H =  HEIGHT - MARGIN1 * 2 # 600 - 10 *2 = 580

    start_point = 600, 300
    mouse = start_point[:]

    pygame.display.set_caption(CAPTION)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # build objects
    canvas = Canvas(
        color=CANVAS_COLOR,
        rect=(
            MARGIN1 * 2 + W1,  # x coordinate
            MARGIN1,  # y coordinate
            CANVAS_W,  # width
            CANVAS_H  # height
        )
    )

    # ai_generated_image = pygame.image.load(str(path)+'/outputimg/default.png').convert()
    # ai_generated_image_positon = (MARGIN1 * 2 + W1 + CANVAS_W + MARGIN1,MARGIN1)

    current_time = pygame.time.get_ticks()

    button_A = Button(
        name="Undo/Redo",
        color=BLACK,
        rect=(
            MARGIN1,  # x coordinate
            MARGIN1,  # y coordinate
            W1,  # width
            H1  # height
        ),
        time=current_time,
        target_f=4.3,  # target frequency
        img=pygame.image.load(path / 'icons' / 'undo.png'),
    )

    button_B = Button(
        name="Eraser",
        color=BLACK,
        rect=(
            MARGIN1,  # x coordinate
            MARGIN1 + H1 + 20*MARGIN1,  # y coordinate
            W1,  # width
            H1  # height
        ),
        time=current_time,
        target_f=7.6,  # target frequency
        img=pygame.image.load(path / 'icons' / 'eraser.png'),
    )

    """button_C = Button(
        name="Color",
        color=BLACK,
        rect=(
            MARGIN1,  # x coordinate
            MARGIN1 + 2*H1 + 8*MARGIN1,  # y coordinate
            W1 - MARGIN2,  # width
            H1  # height
        ),
        time=current_time,
        target_f=10,  # target frequency
        img=pygame.image.load(path / 'icons' / 'color.png'),
    )"""

    button_D = Button(
        name="Pencil",
        color=BLACK,
        rect=(
            600-W1/2,  # x coordinate
            300-H1/2,  # y coordinate
            W1,  # width
            H1  # height
        ),
        time=current_time,
        target_f=10,  # target frequency
        img=pygame.image.load(path / 'icons' / 'pencil.png'),
    )

    button_E = Button(
        name="Done",
        color=BLACK,
        rect=(
            MARGIN1,  # x coordinate
            HEIGHT - MARGIN1 - H1,  # y coordinate
            W1,  # width
            H1  # height
        ),
        time=current_time,
        target_f=6,  # target frequency
        img=pygame.image.load(path / 'icons' / 'check.png'),
    )
    button_list = [button_A, button_B, button_D, button_E]

    def play_music(cue):
        # Create a white rectangle in the center of the screen.
        rect_width = 200
        rect_height = 100
        rect = pygame.Rect(WIDTH / 2 - rect_width // 2, HEIGHT / 2 - rect_height // 2,
                           rect_width, rect_height)
        pygame.draw.rect(screen, WHITE, rect)
        pygame.draw.rect(screen, BLACK, rect, 5)

        font = pygame.font.Font(None, 24)
        # Render the text "AI Picture Rendering...".
        text_surface = font.render("-Tutorial-", True, (0, 0, 0))

        # Calculate the position to center the text in the rectangle.
        text_x = WIDTH / 2 - text_surface.get_width() // 2
        text_y = HEIGHT / 2 - text_surface.get_height() // 2

        # Blit the text surface to the screen.
        screen.blit(text_surface, (text_x, text_y))
        pygame.display.update()

        sound_path = "./sounds/" + cue + ".wav"
        pygame.mixer.init()
        pygame.mixer.music.load(str(sound_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    pygame.mixer.music.stop()
                    return

    # --- Clock, fps ---
    """
    fps = 60
    """
    clock = pygame.time.Clock()

    # --- events ---
    running = True
    in_menu = True
    in_check = 0
    last_order = ['','','']
    mode = 'menu'
    pencil_color = BLACK
    #last2save = ["",""]
    #newsave = canvas.save()
    last2save = ["",path / 'icons' / 'default_paper.png']
    SSVEP_input_list = [0, 0, 0, 0]  # ABDE
    SSVEP_threshold = 2

    #standby mode:
    #screen.fill(BACKGROUND_COLOR)
    wallpaper = pygame.image.load(path / 'icons' / 'wallpaper.png')
    wallpaper = pygame.transform.scale(wallpaper, (WIDTH, HEIGHT))
    screen.blit(wallpaper, (0, 0))
    canvas.draw(screen)
    # screen.blit(ai_generated_image, ai_generated_image_positon)

    for button in button_list:
        button.show = True
        button.draw(screen)
    pygame.display.update()

    standby = True
    while standby:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                standby = False
                tutorial = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                standby = False
                tutorial = False
        # start if space is pressed


    if tutorial:
        #tutorial start
        # 清除Calibration文件歷史資料
        with open(Calibration_path, 'a+') as f:
            f.truncate(0)

        # 1. SSVEP control system
        play_music('01')
        threshold = 0
        while threshold < 3:
            with open(LOG_PATH, 'r') as f:
                try:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        SSVEP_input = last_order[2]

                        if SSVEP_input == 'D':
                            threshold += 1
                except:
                    print("Log file is empty")
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    threshold += 1
            for button in button_list[:-1]:
                button.update(current_time)
            button_E.show = False
            screen.blit(wallpaper, (0, 0))
            canvas.draw(screen)
            for button in button_list:
                button.draw(screen)
            pygame.display.update()

        # 2. MI control system
        canvas.load(total_img_path / 't01.png')
        play_music('02')
        screen.blit(wallpaper, (0, 0))
        canvas.draw(screen)
        for button in button_list:
            button.show = False
        button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'pencil.png'),
                                              (80, 80))
        button_A.show = True
        button_A.draw(screen)
        img = pygame.image.load(path / 'icons' / 'cursor.png')
        cursor_size = 50
        img = pygame.transform.scale(img, (cursor_size, cursor_size))
        threshold = 0
        with open(Calibration_path, 'a+') as f:
            f.write('Left\n')
        while threshold < 5:
            with open(LOG_PATH, 'r') as f:
                try:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'Left':
                            mouse = mouse[0] - move_step*2, mouse[1]
                            threshold += 1
                except:
                    print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                    mouse = mouse[0] - move_step*2, mouse[1]
                    threshold += 1
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            pygame.display.update()
        with open(Calibration_path, 'a+') as f:
            f.write('Done\n')

        # 3. SSVEP control system
        play_music('03')
        canvas.reset()
        canvas.draw(screen)
        screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
        pygame.display.update()
        threshold = 0
        while threshold < 3:
            with open(LOG_PATH, 'r') as f:
                try:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'idle':
                            threshold += 1
                except:
                    print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_5:
                    threshold += 1
        threshold = 0
        while threshold < 3:
            with open(LOG_PATH, 'r') as f:
                try:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        SSVEP_input = last_order[2]
                        if SSVEP_input == 'E':
                            threshold += 1
                except:
                    print("Log file is empty")
            current_time = pygame.time.get_ticks()
            button_E.update(current_time)
            screen.blit(wallpaper, (0, 0))
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            for button in button_list:
                button.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    threshold += 1
            pygame.display.update()

        # 4. MI control system
        canvas.load(total_img_path / 't02.png')
        play_music('04')
        img = pygame.image.load(path / 'icons' / 'pencil_cursor.png')
        cursor_size = 80
        img = pygame.transform.scale(img, (cursor_size, cursor_size))
        screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
        canvas.add_brush(
            color=BRUSH_COLOR,
            position=[mouse[0], mouse[1]],
            size=BRUSH_SIZE
        )
        # Go Down
        threshold = 0
        with open(Calibration_path, 'a+') as f:
            f.write('Down\n')
        while threshold < 5:
            try:
                with open(LOG_PATH, 'r') as f:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'Down':
                            for step in range(move_step*2):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=(mouse[0], mouse[1] + step),
                                    size=BRUSH_SIZE
                                )
                            mouse = mouse[0], mouse[1] + move_step*2
                            threshold += 1
            except:
                print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                    for step in range(move_step*2):
                        canvas.add_brush(
                            color=BRUSH_COLOR,
                            position=(mouse[0], mouse[1] + step),
                            size=BRUSH_SIZE
                        )
                    mouse = mouse[0], mouse[1] + move_step*2
                    threshold += 1
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            pygame.display.update()
        with open(Calibration_path, 'a+') as f:
            f.write('Done\n')
        # Go Right
        threshold = 0
        with open(Calibration_path, 'a+') as f:
            f.write('Right\n')
        while threshold < 5:
            try:
                with open(LOG_PATH, 'r') as f:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'Right':
                            for step in range(move_step*2):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=[mouse[0] + step, mouse[1]],
                                    size=BRUSH_SIZE
                                )
                            mouse = mouse[0] + move_step*2, mouse[1]
                            threshold += 1
            except:
                print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                    for step in range(move_step*2):
                        canvas.add_brush(
                            color=BRUSH_COLOR,
                            position=[mouse[0] + step, mouse[1]],
                            size=BRUSH_SIZE
                        )
                    mouse = mouse[0] + move_step*2, mouse[1]
                    threshold += 1
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            pygame.display.update()
        with open(Calibration_path, 'a+') as f:
            f.write('Done\n')
        # Go Up
        threshold = 0
        with open(Calibration_path, 'a+') as f:
            f.write('Up\n')
        while threshold < 5:
            try:
                with open(LOG_PATH, 'r') as f:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'Up':
                            for step in range(move_step*2):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=(mouse[0], mouse[1] - step),
                                    size=BRUSH_SIZE
                                )
                            mouse = mouse[0], mouse[1] - move_step*2
                            threshold += 1
            except:
                print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                    for step in range(move_step*2):
                        canvas.add_brush(
                            color=BRUSH_COLOR,
                            position=(mouse[0], mouse[1] - step),
                            size=BRUSH_SIZE
                        )
                    mouse = mouse[0], mouse[1] - move_step*2
                    threshold += 1
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            pygame.display.update()
        with open(Calibration_path, 'a+') as f:
            f.write('Done\n')

        # 5. SSVEP control system
        play_music('05')
        #canvas.reset()
        canvas.draw(screen)
        screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
        pygame.display.update()
        threshold = 0
        while threshold < 3:
            try:
                with open(LOG_PATH, 'r') as f:
                    last_line = f.readlines()[-1].split(",")
                    if (last_order != last_line):
                        print("get new order:\n" + str(last_line))
                        last_order = last_line
                        MI_input = last_order[1]
                        if MI_input == 'idle':
                            threshold += 1
            except:
                print("Log file is empty")
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_5:
                    threshold += 1
        threshold = 0
        while threshold < 3:
            with open(LOG_PATH, 'r') as f:
                last_line = f.readlines()[-1].split(",")
                if (last_order != last_line):
                    print("get new order:\n" + str(last_line))
                    last_order = last_line
                    SSVEP_input = last_order[2]
                    if SSVEP_input == 'E':
                        threshold += 1
            current_time = pygame.time.get_ticks()
            button_E.update(current_time)
            screen.blit(wallpaper, (0, 0))
            canvas.draw(screen)
            screen.blit(img, (mouse[0] - cursor_size / 2, mouse[1] - cursor_size / 2))
            for button in button_list:
                button.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    threshold += 1
            pygame.display.update()

        # 6. toturial end
        with open(Calibration_path, 'a+') as f:
            f.write('Done\n')
            f.write('End\n')

        play_music('06')
        canvas.reset()



    #start drawing
    while running:
        # clock.tick(fps)


        #read the predict order
        with open(LOG_PATH, 'r') as f:
            try:
                last_line = f.readlines()[-1].split(",")
                if (last_order != last_line):
                    print("get new order:\n" + str(last_line))
                    last_order = last_line
                    MI_input = last_order[1]
                    SSVEP_input = last_order[2]

                    if mode == 'menu' or mode == 'redo_menu':
                        in_menu = True
                        mouse = start_point[:]

                        if SSVEP_input == 'A': #UNDO
                            SSVEP_input_list[0] += 1
                            if SSVEP_input_list[0] == SSVEP_threshold:

                                if mode == 'menu':
                                    SSVEP_input_list = [0, 0, 0, 0]
                                    if last2save[0] != "":
                                        canvas.load(last2save[0])
                                        last2save = [last2save[1], last2save[0]]
                                        mode = 'redo_menu'
                                        button_A.img = pygame.transform.scale(
                                            pygame.image.load(path / 'icons' / 'redo.png'), (80, 80))
                                    print('receive Order: Undo')

                                elif mode == 'redo_menu':
                                    SSVEP_input_list = [0, 0, 0, 0]
                                    if last2save[0] != "":
                                        canvas.load(last2save[0])
                                        last2save = [last2save[1], last2save[0]]
                                        mode = 'menu'
                                        button_A.img = pygame.transform.scale(
                                            pygame.image.load(path / 'icons' / 'undo.png'), (80, 80))
                                    print('receive Order: Redo')

                        #eraser
                        elif SSVEP_input == 'B':
                            SSVEP_input_list[1] += 1
                            if SSVEP_input_list[1] == SSVEP_threshold:
                                SSVEP_input_list = [0, 0, 0, 0]
                                mode = 'cursor_mode'
                                next_mode = 'eraser_mode'
                                in_menu = False
                                print('switch to Eraser mode')
                                button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'eraser.png'),
                                                                      (80, 80))

                        #elif SSVEP_input == 'C':
                        #    mode = 'color_mode'
                        #    print('switch to Color mode')

                        #pencil
                        elif SSVEP_input == 'D':
                            SSVEP_input_list[2] += 1
                            if SSVEP_input_list[2] == SSVEP_threshold:
                                SSVEP_input_list = [0, 0, 0, 0]
                                mode = 'cursor_mode'
                                next_mode = 'pencil_mode'
                                in_menu = False
                                print('switch to Pencil mode')
                                button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'pencil.png'),
                                                                      (80, 80))

                    # EEG-mouse control system
                    elif mode == 'cursor_mode':

                        if SSVEP_input == 'E' and in_check == 3: #END
                            SSVEP_input_list[3] += 1
                            if SSVEP_input_list[3] == SSVEP_threshold:
                                SSVEP_input_list = [0, 0, 0, 0]
                                first_pt = mouse  #not used in current version
                                mode = next_mode
                                in_check = 0
                                button_E.show = False
                                if mode == 'pencil_mode':
                                    COLOR = pencil_color
                                elif mode == 'eraser_mode':
                                    COLOR = WHITE
                                canvas.add_brush(color=COLOR,
                                                 position=mouse,
                                                 size=BRUSH_SIZE)
                                print('receive Order: Done')

                        elif MI_input == 'idle':
                            in_check = min(3,in_check+1)
                        elif MI_input == 'Right':
                            if canvas.get_rect().collidepoint(mouse[0] + move_step, mouse[1]):
                                mouse = mouse[0] + move_step, mouse[1]
                            in_check = max(0,in_check - 1)
                        elif MI_input == 'Left':
                            if canvas.get_rect().collidepoint(mouse[0] - move_step, mouse[1]):
                                mouse = mouse[0] - move_step, mouse[1]
                            in_check = max(0,in_check - 1)
                        elif MI_input == 'Down':
                            if canvas.get_rect().collidepoint(mouse[0], mouse[1] + move_step):
                                mouse = mouse[0], mouse[1] + move_step
                            in_check = max(0,in_check - 1)
                        elif MI_input == 'Up':
                            if canvas.get_rect().collidepoint(mouse[0], mouse[1] - move_step):
                                mouse = mouse[0], mouse[1] - move_step
                            in_check = max(0,in_check - 1)

                    elif mode == 'pencil_mode' or mode == 'eraser_mode':
                        BRUSH_COLOR = pencil_color if mode == 'pencil_mode' else WHITE
                        if SSVEP_input == 'E' and in_check == 3: #END
                            SSVEP_input_list[3] += 1
                            if SSVEP_input_list[3] == SSVEP_threshold:
                                SSVEP_input_list = [0, 0, 0, 0]
                                mode = 'menu'
                                in_menu = True
                                in_check = 0
                                newsave = canvas.save()
                                last2save = [last2save[1], newsave]
                                button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'undo.png'),
                                                                      (80, 80))

                        elif MI_input == 'idle':
                            in_check = min(3,in_check+1)

                        elif MI_input == 'Right':
                            for step in range(move_step):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=[mouse[0] + step, mouse[1]],
                                    size=BRUSH_SIZE
                                )
                            if canvas.get_rect().collidepoint(mouse[0] + move_step, mouse[1]):
                                mouse = mouse[0] + move_step, mouse[1]
                            in_check = max(0,in_check - 1)

                        elif MI_input == 'Left':
                            for step in range(move_step):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=(mouse[0] - step, mouse[1]),
                                    size=BRUSH_SIZE
                                )
                            if canvas.get_rect().collidepoint(mouse[0] - move_step, mouse[1]):
                                mouse = mouse[0] - move_step, mouse[1]
                            in_check = max(0,in_check - 1)

                        elif MI_input == 'Down':
                            for step in range(move_step):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=(mouse[0] , mouse[1]+step),
                                    size=BRUSH_SIZE
                                )
                            if canvas.get_rect().collidepoint(mouse[0], mouse[1] + move_step):
                                mouse = mouse[0], mouse[1] + move_step
                            in_check = max(0,in_check - 1)

                        elif MI_input == 'Up':
                            for step in range(move_step):
                                canvas.add_brush(
                                    color=BRUSH_COLOR,
                                    position=(mouse[0], mouse[1]-step),
                                    size=BRUSH_SIZE
                                )
                            if canvas.get_rect().collidepoint(mouse[0], mouse[1] - move_step):
                                mouse = mouse[0], mouse[1] - move_step
                            in_check = max(0,in_check - 1)
            except:
                print("Log file is empty")

        # Aux func: not control by EEG

        ## --- events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                print("The Pygame window is now " + str(event.w) + " pixels wide and " + str(event.h) + " pixels high")
                WIDTH, HEIGHT = event.size
                if WIDTH < min_width:
                    WIDTH = min_width
                if HEIGHT < min_height:
                    HEIGHT = min_height
                screen = pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE | DOUBLEBUF | RESIZABLE)
                CANVAS_SIZE = (WIDTH - MARGIN1 * 2) / 2, HEIGHT - MARGIN1 * 2
                #screen.fill(BACKGROUND_COLOR)
                screen.blit(wallpaper, (0, 0))
                canvas = pygame.transform.scale(canvas, CANVAS_SIZE)
            elif event.type == pygame.KEYDOWN:
                # Save canvas when "S" is pressed
                if event.key == pygame.K_s:
                    canvas.save()
                # Reset canvas when "R" is pressed
                if event.key == pygame.K_r:
                    canvas.reset()
                    in_menu=True
                    mode = 'menu'
                """# Open/Close button blinking when "F" is pressed
                if event.key == pygame.K_f:
                    is_flashing = not is_flashing"""
                #pencil when "P" is pressed
                if event.key == pygame.K_p:
                    mode = 'cursor_mode'
                    next_mode = 'pencil_mode'
                    in_menu = False
                    button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'pencil.png'),
                                                          (80, 80))
                    print('switch to Pencil mode')
                #eraser when "E" is pressed
                if event.key == pygame.K_e:
                    mode = 'cursor_mode'
                    next_mode = 'eraser_mode'
                    in_menu = False
                    button_A.img = pygame.transform.scale(pygame.image.load(path / 'icons' / 'eraser.png'),
                                                          (80, 80))
                    print('switch to Eraser mode')

                if event.key == pygame.K_UP:
                    if mode == 'cursor_mode':
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] - move_step):
                            mouse = mouse[0], mouse[1] - move_step
                    elif mode == 'pencil_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=pencil_color,
                                position=(mouse[0], mouse[1] - step),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] - move_step):
                            mouse = mouse[0], mouse[1] - move_step
                    elif mode == 'eraser_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=WHITE,
                                position=(mouse[0], mouse[1] - step),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] - move_step):
                            mouse = mouse[0], mouse[1] - move_step
                if event.key == pygame.K_DOWN:
                    if mode == 'cursor_mode':
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] + move_step):
                            mouse = mouse[0], mouse[1] + move_step
                    elif mode == 'pencil_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=pencil_color,
                                position=(mouse[0], mouse[1] + step),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] + move_step):
                            mouse = mouse[0], mouse[1] + move_step
                    elif mode == 'eraser_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=WHITE,
                                position=(mouse[0], mouse[1] + step),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0], mouse[1] + move_step):
                            mouse = mouse[0], mouse[1] + move_step
                if event.key == pygame.K_LEFT:
                    if mode == 'cursor_mode':
                        if canvas.get_rect().collidepoint(mouse[0] - move_step, mouse[1]):
                            mouse = mouse[0] - move_step, mouse[1]
                    elif mode == 'pencil_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=pencil_color,
                                position=(mouse[0] - step, mouse[1]),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0] - move_step, mouse[1]):
                            mouse = mouse[0] - move_step, mouse[1]
                    elif mode == 'eraser_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=WHITE,
                                position=(mouse[0] - step, mouse[1]),
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0] - move_step, mouse[1]):
                            mouse = mouse[0] - move_step, mouse[1]
                if event.key == pygame.K_RIGHT:
                    if mode == 'cursor_mode':
                        if canvas.get_rect().collidepoint(mouse[0] + move_step, mouse[1]):
                            mouse = mouse[0] + move_step, mouse[1]
                    elif mode == 'pencil_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=pencil_color,
                                position=[mouse[0] + step, mouse[1]],
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0] + move_step, mouse[1]):
                            mouse = mouse[0] + move_step, mouse[1]
                    elif mode == 'eraser_mode':
                        for step in range(move_step):
                            canvas.add_brush(
                                color=WHITE,
                                position=[mouse[0] + step, mouse[1]],
                                size=BRUSH_SIZE
                            )
                        if canvas.get_rect().collidepoint(mouse[0] + move_step, mouse[1]):
                            mouse = mouse[0] + move_step, mouse[1]
                #done when "D" is pressed
                if event.key == pygame.K_d:
                    if mode == "cursor_mode":
                        first_pt = mouse #not used in current version
                        mode = next_mode
                        if mode == 'pencil_mode':
                            COLOR = pencil_color
                        elif mode == 'eraser_mode':
                            COLOR = WHITE
                        canvas.add_brush(color=COLOR,
                                         position=mouse,
                                         size=BRUSH_SIZE)
                    elif mode == "pencil_mode" or mode == "eraser_mode":
                        newsave = canvas.save()
                        last2save = [last2save[1], newsave]
                        in_menu = True
                        mode = 'menu'
                        button_A.img = pygame.transform.scale(
                            pygame.image.load(path / 'icons' / 'undo.png'), (80, 80))

                #Undo/Redo when "U" is pressed
                if event.key == pygame.K_u:
                    if last2save[0] != "":
                        if mode == 'menu':
                            canvas.load(last2save[0])
                            last2save = [last2save[1], last2save[0]]
                            mode = 'redo_menu'
                            button_A.img = pygame.transform.scale(
                                pygame.image.load(path / 'icons' / 'redo.png'), (80, 80))
                        elif mode == 'redo_menu':
                            canvas.load(last2save[0])
                            last2save = [last2save[1], last2save[0]]
                            mode = 'menu'
                            button_A.img = pygame.transform.scale(
                                pygame.image.load(path / 'icons' / 'undo.png'), (80, 80))
                    print('switch to Undo mode')

                # back to menu when "M" is pressed
                if event.key == pygame.K_m:
                    in_menu = True
                    mode = 'menu'
                # quit when "Q" is pressed, make animated gif
                if event.key == pygame.K_q:
                    running = False

            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in button_list:
                    if button.get_rect().collidepoint(mouse_pos):
                        print(button.name + " got pressed")
                        if button.name == 'Undo/Redo' and (mode == 'menu' or mode == 'redo_menu'):

                            if last2save[0] != "":
                                if mode == 'menu':
                                    canvas.load(last2save[0])
                                    last2save = [last2save[1], last2save[0]]
                                    mode = 'redo_menu'
                                    button_A.img = pygame.transform.scale(
                                        pygame.image.load(path / 'icons' / 'redo.png'), (80, 80))
                                elif mode == 'redo_menu':
                                    canvas.load(last2save[0])
                                    last2save = [last2save[1], last2save[0]]
                                    mode = 'menu'
                                    button_A.img = pygame.transform.scale(
                                        pygame.image.load(path / 'icons' / 'undo.png'), (80, 80))
                            print('switch to Undo mode')
                        elif button.name == 'Eraser' and (mode == 'menu' or mode == 'redo_menu'):
                            mode = 'eraser_mode'
                            #next_mode = 'eraser_mode'
                            in_menu = False
                            print('switch to Eraser mode')
                        elif button.name == 'Color' and (mode == 'menu' or mode == 'redo_menu'):
                            mode = 'color_mode'
                            print('switch to Color mode')
                        elif button.name == 'Pencil' and (mode == 'menu' or mode == 'redo_menu'):
                            mode = 'pencil_mode'
                            #next_mode = 'pencil_mode'
                            in_menu = False
                            print('switch to Pencil mode')
                        elif button.name == 'Done' and (mode == 'pencil_mode' or mode == 'eraser_mode'):
                            newsave = canvas.save()
                            last2save = [last2save[1], newsave]
                            in_menu = True
                            mode = 'menu'
                            button_A.img = pygame.transform.scale(
                                pygame.image.load(path / 'icons' / 'undo.png'), (80, 80))


        ## mouse in canvas
        if mode == 'pencil_mode':
            if pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                if canvas.get_rect().collidepoint(mouse_pos):
                    canvas.add_brush(
                        color=BRUSH_COLOR,
                        position=mouse_pos,
                        size=BRUSH_SIZE
                    )
        elif mode == 'eraser_mode':
            if pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                if canvas.get_rect().collidepoint(mouse_pos):
                    canvas.add_brush(
                        color=WHITE,
                        position=mouse_pos,
                        size=BRUSH_SIZE
                    )



        # --- SSVEP control system ---
        if in_menu == True:
            current_time = pygame.time.get_ticks()
            for button in button_list[:-1]:
                button.update(current_time)
            button_E.show = False
        else:
            button_A.show = True
            for button in button_list[1:-1]:
                button.show = False
            if in_check >= 3:
                current_time = pygame.time.get_ticks()
                button_E.update(current_time)
            else:
                button_E.show = True



        # --- draws ---
        #screen.fill(BACKGROUND_COLOR)
        screen.blit(wallpaper, (0, 0))
        canvas.draw(screen)
        for button in button_list:
            button.draw(screen)
        # screen.blit(ai_generated_image, ai_generated_image_positon)

        #button_back.observe()     # Uncomment to observe actual frequency of button

        #preview mouse, rect, etc.
        if mode == 'cursor_mode':
            #pygame.draw.circle(screen, RED,mouse, 4)
            img = pygame.image.load(path / 'icons' / 'cursor.png')
            cursor_size = 50
            img = pygame.transform.scale(img, (cursor_size, cursor_size))
            screen.blit(img, (mouse[0]-cursor_size/2,mouse[1]-cursor_size/2))
            #screen.blit(img, mouse_pos-80)
        elif mode == 'eraser_mode':
            pygame.draw.circle(screen, RED,mouse, BRUSH_SIZE)
        elif mode == 'pencil_mode':
            img = pygame.image.load(path / 'icons' / 'pencil_cursor.png')
            cursor_size = 80
            img = pygame.transform.scale(img, (cursor_size, cursor_size))
            screen.blit(img, (mouse[0]-cursor_size/2,mouse[1]-cursor_size/2))
            #screen.blit(img, mouse_pos)

        pygame.display.update()

    # --- end ---
    print("start to make AI generated image")
    # Create a white rectangle in the center of the screen.
    rect_width = 200
    rect_height = 100
    rect = pygame.Rect(WIDTH / 2 - rect_width // 2, HEIGHT / 2 - rect_height // 2,
                       rect_width, rect_height)
    pygame.draw.rect(screen, WHITE, rect)
    pygame.draw.rect(screen, BLACK, rect, 5)

    # Create a font object.
    font = pygame.font.Font(None, 24)
    # Render the text "AI Picture Rendering...".
    text_surface = font.render("Please Wait...", True, (0, 0, 0))

    # Calculate the position to center the text in the rectangle.
    text_x = WIDTH / 2 - text_surface.get_width() // 2
    text_y = HEIGHT / 2 - text_surface.get_height() // 2

    # Blit the text surface to the screen.
    screen.blit(text_surface, (text_x, text_y))
    pygame.display.update()
    original_image_PATH = str(SAVE_FOLDER_PATH / OUTPUT_LIST[-1])
    last_image = Image.open(original_image_PATH)
    name_list = call_4_images(OUTPUT_4img_PATH, last_image)

    for alpha in range(0, 255, 5):
        WHITE_BG = pygame.Surface((WIDTH, HEIGHT))
        WHITE_BG.fill((255, 255, 255))
        WHITE_BG.set_alpha(alpha)
        screen.blit(WHITE_BG, (0, 0))
        pygame.display.update()
        pygame.time.delay(50)
    pygame.quit()

    demo_4_imgs([original_image_PATH,
                 name_list[0], name_list[1], name_list[2], name_list[3]])






    print("END OF PROGRAM")
    # quit
    pygame.display.quit()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()