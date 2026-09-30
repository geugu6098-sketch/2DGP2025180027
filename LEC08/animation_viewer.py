"""애니메이션 뷰어 (Drill #8)

복잡한 스프라이트 시트 한 장에서 여러 애니메이션을 골라 재생한다.
- 스프라이트 시트: character_sheet.png (프레임마다 크기가 서로 다르다)
- 프레임 정보   : character_sheet.json (애니메이션마다 프레임 개수가 다르다)

재생 규칙: 각 애니메이션을 5회 반복한 뒤 1초 정지하고, 다음 애니메이션으로 넘어간다.
          마지막 애니메이션까지 마치면 처음부터 다시 무한 반복한다.
"""

import json
import os

import pico2d
from pico2d import *

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

SHEET_IMAGE = 'character_sheet.png'
SHEET_META = 'character_sheet.json'

# pico2d 가 함께 배포하는 폰트 (경로는 설치 위치에 의존하지 않는다)
FONT_PATH = os.path.join(os.path.dirname(pico2d.__file__),
                         'data', 'ConsolaMalgun.ttf')

# 화면에 표시할 캐릭터의 목표 높이. 캔버스 높이(600)의 55% 로,
# 요구사항인 "화면의 절반 이상"을 만족한다.
CHARACTER_HEIGHT = 330

# 캐릭터의 발밑이 놓이는 y 좌표 (캔버스의 세로 중앙에 맞춘다)
GROUND_LINE = CANVAS_HEIGHT / 2 + CHARACTER_HEIGHT / 2

# 한 애니메이션을 몇 번 반복한 뒤 멈출지
REPEAT_COUNT = 5
PAUSE_TIME = 1.0

running = True


def handle_events():
    """창 닫기 / ESC 키를 처리한다."""
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


def frame_source_bottom(frame):
    """clip_draw 는 이미지 아래쪽을 기준으로 좌표를 받으므로 y 좌표를 뒤집어 준다."""
    return sheet_height - frame['y'] - frame['h']


def frame_scale(frame):
    """프레임마다 크기가 다르므로 목표 높이 기준으로 확대 비율을 구한다."""
    return CHARACTER_HEIGHT / frame['h']


def draw_ground():
    """캐릭터가 서 있는 바닥과 그림자를 그린다."""
    set_color(255, 255, 255, 40)
    draw_rectangle(CANVAS_WIDTH * 0.10, GROUND_LINE - 5,
                   CANVAS_WIDTH * 0.90, GROUND_LINE, filled=True)

    set_color(226, 232, 240, 200)
    draw_line(CANVAS_WIDTH * 0.10, GROUND_LINE,
              CANVAS_WIDTH * 0.90, GROUND_LINE)


def draw_frame(frame):
    """프레임 하나를 확대해서 화면 중앙에 그린다.

    모든 프레임의 발밑(pivot 이쪽 끝)이 GROUND_LINE 에 맞춰지므로
    점프처럼 프레임 크기가 달라져도 캐릭터가 자연스럽게 제자리에서 움직인다.
    """
    scale = frame_scale(frame)
    width = frame['w'] * scale
    height = frame['h'] * scale

    center_x = CANVAS_WIDTH / 2
    center_y = GROUND_LINE - height / 2

    sheet.clip_draw(frame['x'],
                    frame_source_bottom(frame),
                    frame['w'],
                    frame['h'],
                    center_x,
                    center_y,
                    width,
                    height)


def animation_names():
    """등록된 애니메이션 이름을 순서대로 돌려준다."""
    return [anim['name'] for anim in animations]


def play_once(anim):
    """애니메이션을 한 번 반복 재생한다.

    애니메이션마다 프레임 개수와 프레임당 표시 시간이 서로 다르므로
    메타데이터에 적힌 값을 그대로 사용한다.
    """
    print('%s 재생 (%d프레임, %.2f초/프레임)' % (
        anim['name'], len(anim['frames']), anim['frame_time']))

    for frame in anim['frames']:
        clear_canvas()
        draw_ground()
        draw_frame(frame)
        update_canvas()
        delay(anim['frame_time'])


open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

sheet = load_image(SHEET_IMAGE)

with open(SHEET_META, encoding='utf-8') as fp:
    meta = json.load(fp)

sheet_height = meta['sheet_height']
animations = meta['animations']

print('애니메이션 %d종, 전체 프레임 %d개' % (
    len(animations), sum(len(a['frames']) for a in animations)))

while running:
    handle_events()

    for anim in animations:
        if not running:
            break
        play_once(anim)

close_canvas()