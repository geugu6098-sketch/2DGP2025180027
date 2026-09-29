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

    for x in range(RECTANGLE_POINTS[0][0], RECTANGLE_POINTS[1][0], RECTANGLE_STEP):
        draw_character(x, RECTANGLE_POINTS[0][1])


def draw_right():
    print('right')

    for y in range(RECTANGLE_POINTS[1][1], RECTANGLE_POINTS[2][1], RECTANGLE_STEP):
        draw_character(RECTANGLE_POINTS[1][0], y)


def draw_bottom():
    print('bottom')

    for x in range(RECTANGLE_POINTS[2][0], RECTANGLE_POINTS[3][0], -RECTANGLE_STEP):
        draw_character(x, RECTANGLE_POINTS[2][1])


def draw_left():
    print('left')

    for y in range(RECTANGLE_POINTS[3][1], RECTANGLE_POINTS[0][1], -RECTANGLE_STEP):
        draw_character(RECTANGLE_POINTS[3][0], y)


def draw_rectangle():
    print('rectangle')

    draw_top()


draw_circle()

close_canvas()
