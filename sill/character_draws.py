from pico2d import *
import math

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

CIRCLE_CENTER_X = 400
CIRCLE_CENTER_Y = 300
CIRCLE_RADIUS = 200

RECTANGLE_POINTS = [(200, 150), (600, 150), (600, 450), (200, 450)]
RECTANGLE_STEP = 5

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

# 궤적을 따라 움직일 캐릭터
character = load_image('character.png')


def draw_character(x, y):
    print(f'character -> ({x:.0f}, {y:.0f})')
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.02)


def draw_circle():
    print('circle')

    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = CIRCLE_CENTER_X + CIRCLE_RADIUS * math.cos(rad)
        y = CIRCLE_CENTER_Y + CIRCLE_RADIUS * math.sin(rad)
        draw_character(x, y)


def draw_top():
    print('top')


draw_circle()

close_canvas()
