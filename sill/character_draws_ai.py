from pico2d import *
import math

# ---------------------------------------------------------------
# character_draws_ai.py
# AI 가 작성한 버전.
# 캐릭터를 원 / 사각형 / 삼각형 궤적을 따라 무한 반복 이동시킨다.
# 창을 닫거나 ESC 키를 누르면 종료한다.
# ---------------------------------------------------------------

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# 한 프레임에서 기다리는 시간(초)
FRAME_DELAY = 0.02

# --- 원 궤적: 중심 좌표와 반지름 ---------------------------------
CIRCLE_CENTER = (400, 300)
CIRCLE_RADIUS = 200
CIRCLE_STEP_DEG = 5

# --- 다각형 궤적: 꼭짓점 목록을 순서대로 잇는다 -------------------
RECTANGLE_POINTS = [(200, 150), (600, 150), (600, 450), (200, 450)]
TRIANGLE_POINTS = [(400, 140), (600, 460), (200, 460)]

# 선분을 따라 움직일 때의 최소 이동 간격(픽셀)
LINE_STEP = 4

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

character = load_image('character.png')

running = True


def handle_events():
    """창 닫기 / ESC 키를 감지해 실행을 종료한다."""
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


def draw_character(x, y):
    """이전 프레임을 지운 뒤 (x, y) 에 캐릭터를 그린다."""
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(FRAME_DELAY)


def draw_circle():
    """원 궤적을 한 바퀴 돈다."""
    print('circle')
    center_x, center_y = CIRCLE_CENTER

    for deg in range(0, 360, CIRCLE_STEP_DEG):
        rad = math.radians(deg)
        draw_character(center_x + CIRCLE_RADIUS * math.cos(rad),
                       center_y + CIRCLE_RADIUS * math.sin(rad))


def draw_segment(start, end, step=LINE_STEP):
    """start 에서 end 까지 등간격으로 이동한다."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    steps = max(1, int(math.hypot(dx, dy) // step))

    for i in range(steps + 1):
        t = i / steps
        draw_character(start[0] + dx * t, start[1] + dy * t)


def draw_polygon(points):
    """꼭짓점 목록을 닫힌 다각형으로 순회한다."""
    for i in range(len(points)):
        draw_segment(points[i], points[(i + 1) % len(points)])


def draw_rectangle():
    """사각형 궤적을 한 바퀴 돈다."""
    print('rectangle')
    draw_polygon(RECTANGLE_POINTS)


def draw_triangle():
    """삼각형 궤적을 한 바퀴 돈다."""
    print('triangle')
    draw_polygon(TRIANGLE_POINTS)


def draw_paths():
    """원 -> 사각형 -> 삼각형을 한 번씩 실행한다."""
    draw_circle()
    draw_rectangle()
    draw_triangle()


# 무한 반복
while running:
    handle_events()
    draw_paths()

close_canvas()
