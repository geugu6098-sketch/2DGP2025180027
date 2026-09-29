from pico2d import *
import math

# ------------------------------------------------------------
# character_draws.py
# 캐릭터를 원 / 사각형 / 삼각형 궤적을 따라 무한 반복 이동시킨다.
# 창을 닫거나 ESC 키를 누르면 종료한다.
# ------------------------------------------------------------

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# 원운동 궤적
CIRCLE_CENTER_X = 400
CIRCLE_CENTER_Y = 300
CIRCLE_RADIUS = 200
CIRCLE_STEP_DEG = 5

# 사각형 궤적: 왼쪽 위 -> 오른쪽 위 -> 오른쪽 아래 -> 왼쪽 아래
RECTANGLE_POINTS = [(200, 150), (600, 150), (600, 450), (200, 450)]
RECTANGLE_STEP = 5

# 삼각형 궤적: 위 꼭짓점 -> 오른쪽 아래 -> 왼쪽 아래
TRIANGLE_POINTS = [(400, 140), (600, 460), (200, 460)]
TRIANGLE_STEPS = 90

# 한 프레임에서 기다리는 시간(초)
FRAME_DELAY = 0.02

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

# 궤적을 따라 움직일 캐릭터
character = load_image('character.png')

running = True

print('start: circle -> rectangle -> triangle')


# 창 닫기 / ESC 키 처리
def handle_events():
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


# 한 프레임 그리기: 이전 프레임을 지우고 캐릭터의 다음 위치를 표시
def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(FRAME_DELAY)


# 원운동: 중심에서 일정 거리만큼 떨어진 곳을 한 바퀴 돈다
def draw_circle():
    print('circle')

    for deg in range(0, 360, CIRCLE_STEP_DEG):
        rad = math.radians(deg)
        x = CIRCLE_CENTER_X + CIRCLE_RADIUS * math.cos(rad)
        y = CIRCLE_CENTER_Y + CIRCLE_RADIUS * math.sin(rad)
        draw_character(x, y)


# 사각형 각 변을 시계 방향으로 따라간다
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


# 두 점을 잇는 선분을 따라 캐릭터를 이동
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


# 원 -> 사각형 -> 삼각형을 끊임없이 반복
while running:
    handle_events()

    draw_circle()
    draw_rectangle()
    draw_triangle()

print('finished')
close_canvas()
