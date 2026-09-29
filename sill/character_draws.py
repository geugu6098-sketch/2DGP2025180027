from pico2d import *
import math

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

CIRCLE_CENTER_X = 400
CIRCLE_CENTER_Y = 300
CIRCLE_RADIUS = 200

RECTANGLE_POINTS = [(200, 150), (600, 150), (600, 450), (200, 450)]
RECTANGLE_STEP = 5

TRIANGLE_POINTS = [(400, 140), (600, 460), (200, 460)]
TRIANGLE_STEPS = 90

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

# 궤적을 따라 움직일 캐릭터
character = load_image('character.png')

running = True


def handle_events():
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


def draw_character(x, y):
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
    for x in range(RECTANGLE_POINTS[0][0], RECTANGLE_POINTS[1][0], RECTANGLE_STEP):
        draw_character(x, RECTANGLE_POINTS[0][1])


def draw_right():
    for y in range(RECTANGLE_POINTS[1][1], RECTANGLE_POINTS[2][1], RECTANGLE_STEP):
        draw_character(RECTANGLE_POINTS[1][0], y)


def draw_bottom():
    for x in range(RECTANGLE_POINTS[2][0], RECTANGLE_POINTS[3][0], -RECTANGLE_STEP):
        draw_character(x, RECTANGLE_POINTS[2][1])


def draw_left():
    for y in range(RECTANGLE_POINTS[3][1], RECTANGLE_POINTS[0][1], -RECTANGLE_STEP):
        draw_character(RECTANGLE_POINTS[3][0], y)


def draw_rectangle():
    print('rectangle')

    draw_top()
    draw_right()
    draw_bottom()
    draw_left()


def draw_triangle_side(start, end):
    for i in range(TRIANGLE_STEPS + 1):
        t = i / TRIANGLE_STEPS
        draw_character(start[0] + (end[0] - start[0]) * t,
                       start[1] + (end[1] - start[1]) * t)


def draw_triangle():
    print('triangle')

    draw_triangle_side(TRIANGLE_POINTS[0], TRIANGLE_POINTS[1])
    draw_triangle_side(TRIANGLE_POINTS[1], TRIANGLE_POINTS[2])
    draw_triangle_side(TRIANGLE_POINTS[2], TRIANGLE_POINTS[0])


while running:
    handle_events()

    draw_circle()
    draw_rectangle()
    draw_triangle()

close_canvas()
