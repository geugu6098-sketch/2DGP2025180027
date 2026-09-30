"""애니메이션 뷰어 (Drill #8)

스프라이트 시트 한 장에서 여러 애니메이션을 골라 순서대로 재생한다.
기본 시트는 character_play.png 이고, SPACE 키로 복잡한 시트를 갈아킬 수 있다.

스프라이트 시트
  - character_play.png : 4행 x 8열. 행마다 높이가 다르고 프레임마다 크기가 다르다.
  - character_sheet.png : 4종 애니메이션. 프레임 개수와 크기가 모두 다르다.

재생 규칙
  각 애니메이션을 5회 반복한 뒤 1초 정지하고, 다음 애니메이션으로 넘어간다.
  마지막 애미테이션까지 마치면 처음부터 다시 무한 반복한다.
"""

import json
import os
import time

import pico2d
from pico2d import *

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# (이미지 파일, 메타데이터 파일, 화면에 보여줄 이름)
# 첫 번째 항목이 실행 시 기본으로 사용된다.
SHEETS = [
    ('character_play.png', 'character_play.json', 'CHARACTER PLAY'),
    ('character_sheet.png', 'character_sheet.json', 'COMPLEX SHEET'),
]
ACTIVE_SHEET = 0

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

# 1초 정지 중에는 화면을 갱신하면서 남은 시간을 세는 데 쓰는 간격
IDLE_TICK = 1.0 / 60.0

running = True
sheet = None
sheet_height = 0
animations = []
active = None
current = None


def load_sheet(index):
    """스프라이트 시트와 메타데이터를 읽고 화면에 그릴 수 있는 형태로 가공한다.

    프레임마다 크기가 다르므로 애니메이션별로 다음 두 값을 미리 구한다.
      scale_height : 해당 애니메이션에서 가장 높은 프레임의 높이 (확대 기준)
      baseline     : 해당 애니메이션에서 가장 낮은 발밑 위치 (정렬 기준)
    """
    image_name, meta_name, label = SHEETS[index]
    image = load_image(image_name)

    with open(meta_name, encoding='utf-8-sig') as fp:
        data = json.load(fp)

    prepared = []
    for anim in data['animations']:
        frames = anim['frames']
        prepared.append({
            'name': anim['name'],
            'frame_time': anim['frame_time'],
            'frames': frames,
            'scale_height': max(f['h'] for f in frames),
            'baseline': max(f['y'] + f['h'] for f in frames),
        })

    return image, data['sheet_height'], prepared, label


def switch_sheet():
    """SPACE 키로 스프라이트 시트를 바꾼다."""
    global sheet, sheet_height, animations, active
    global ACTIVE_SHEET, current

    ACTIVE_SHEET = (ACTIVE_SHEET + 1) % len(SHEETS)
    sheet, sheet_height, animations, active = load_sheet(ACTIVE_SHEET)
    current = new_state()
    start_animation(0, False)

    print('[sheet] %s  %d animations' % (active, len(animations)))


def new_state():
    """현재 재생 상태를 담는 딕셔너리를 만든다."""
    return {
        'anim_index': 0,
        'repeat': 1,
        'frame_index': 0,
        'frame_count': 0,
        'frame': None,
        'state': 'play',
        'pause_until': 0.0,
        'pause_left': 0.0,
        'cycle': 0,
    }


def start_animation(index, cycle_increment):
    """지정한 애니메이션을 1회째 프레임부터 다시 재생한다."""
    if cycle_increment:
        current['cycle'] += 1

    anim = animations[index]
    current['anim_index'] = index
    current['repeat'] = 1
    current['frame_index'] = 0
    current['frame_count'] = len(anim['frames'])
    current['frame'] = anim['frames'][0]
    current['state'] = 'play'
    current['pause_left'] = 0.0

    print('[%d] %-6s start (%d frames, %.2fs/frame)' % (
        current['cycle'], anim['name'], current['frame_count'],
        anim['frame_time']))


def advance_one_frame():
    """다음 프레임으로 넘어간다. 한 번의 반복이 끝나면 정지하고, 끝나면 다음 애니메이션."""
    anim = animations[current['anim_index']]
    frames = anim['frames']

    current['frame_index'] += 1

    if current['frame_index'] < current['frame_count']:
        current['frame'] = frames[current['frame_index']]
        return

    current['frame_index'] = 0
    current['frame'] = frames[0]
    current['repeat'] += 1

    if current['repeat'] <= REPEAT_COUNT:
        print('   %s repeat %d/%d done' % (
            anim['name'], current['repeat'] - 1, REPEAT_COUNT))
        return

    # 5회를 다 돌았으면 1초 정지 후 다음 애니메이션으로 넘어간다.
    current['repeat'] = 0
    current['state'] = 'pause'
    current['pause_until'] = time.time() + PAUSE_TIME
    current['pause_left'] = PAUSE_TIME
    print('   %s 5 repeats done -> pause %.1fs' % (anim['name'], PAUSE_TIME))


def tick_time():
    """이번 반복에서 화면을 얼마나 띄워야 하는지(초)를 돌려준다."""
    if current['state'] == 'pause':
        return IDLE_TICK
    return animations[current['anim_index']]['frame_time']


def handle_events():
    """창 닫기 / ESC 키 / SPACE 키를 처리한다."""
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            switch_sheet()


def frame_source_bottom(frame):
    """clip_draw 는 이미지 아래쪽을 기준으로 좌표를 받으므로 y 좌표를 뒤집어 준다."""
    return sheet_height - frame['y'] - frame['h']


def draw_ground():
    """캐릭터가 서 있는 바닥과 그림자를 그린다."""
    draw_rectangle(CANVAS_WIDTH * 0.10, GROUND_LINE - 5,
                   CANVAS_WIDTH * 0.90, GROUND_LINE,
                   255, 255, 255, 40, filled=True)

    draw_line(CANVAS_WIDTH * 0.10, GROUND_LINE,
              CANVAS_WIDTH * 0.90, GROUND_LINE,
              226, 232, 240, 200)


def draw_frame(anim, frame):
    """프레임 하나를 확대해서 화면 중앙에 그린다.

    애니메이션마다 확대 비율을 하나로 맞춰 캐릭터 크기가 흔들리지 않게 하고,
    발밑(pivot 이쪽 끝)을 GROUND_LINE 에 맞춘다. 점프처럼 프레임의 발밑이
    높은 위치인 프레임은 그 차이만큼 위로 떠서 그려진다.
    """
    scale = CHARACTER_HEIGHT / anim['scale_height']
    width = frame['w'] * scale
    height = frame['h'] * scale

    lift = (anim['baseline'] - (frame['y'] + frame['h'])) * scale
    center_x = CANVAS_WIDTH / 2
    top_y = GROUND_LINE - lift - height

    sheet.clip_draw(frame['x'],
                    frame_source_bottom(frame),
                    frame['w'],
                    frame['h'],
                    center_x - width / 2,
                    top_y,
                    width,
                    height)


def draw_header():
    """화면 상단에 제목, 재생 규칙, 애니메이션 목록을 표시한다."""
    draw_rectangle(0, 0, CANVAS_WIDTH, 78, 30, 34, 44, 255, filled=True)

    title_font.draw(24, 14, 'ANIMATION VIEWER', (255, 255, 255))
    info_font.draw(24, 48, 'each animation x%d, then pause %.1fs   [SPACE] %s' % (
        REPEAT_COUNT, PAUSE_TIME, active.lower()), (170, 180, 196))

    x = CANVAS_WIDTH - 24
    name = animations[current['anim_index']]['name']
    for anim in reversed(animations):
        label = anim['name'].upper()
        color = (255, 208, 84) if label == name.upper() else (96, 104, 120)
        info_font.draw(x - 8 * len(label) * 9, 48, label, color)
        x -= 8 * len(label) * 9 + 24


def draw_status():
    """현재 애니메이션 / 반복 횟수 / 프레임 정보를 화면에 표시한다."""
    if current['state'] == 'pause':
        label = 'PAUSE %.1fs' % current['pause_left']
        color = (226, 122, 84)
    else:
        label = animations[current['anim_index']]['name'].upper()
        color = (70, 76, 92)

    info_font.draw(CANVAS_WIDTH / 2 - 40, GROUND_LINE + 18, label, color)

    info_font.draw(24, CANVAS_HEIGHT - 30,
                   'repeat %d / %d   cycle %d   frame %d / %d' % (
                       current['repeat'], REPEAT_COUNT,
                       current['cycle'],
                       current['frame_index'] + 1,
                       current['frame_count']),
                   (170, 180, 196))


def draw_scene():
    """한 프레임의 장면을 완성해서 그린다."""
    anim = animations[current['anim_index']]

    clear_canvas()
    draw_header()
    draw_ground()
    draw_frame(anim, current['frame'])
    draw_status()
    update_canvas()


open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)

title_font = load_font(FONT_PATH, 28)
info_font = load_font(FONT_PATH, 18)

sheet, sheet_height, animations, active = load_sheet(ACTIVE_SHEET)
current = new_state()

print('sheet %s  %d animations, %d frames total' % (
    active, len(animations), sum(len(a['frames']) for a in animations)))

start_animation(0, False)
current['cycle'] = 1

while running:
    handle_events()

    if current['state'] == 'pause':
        current['pause_left'] = current['pause_until'] - time.time()
        if current['pause_left'] <= 0:
            next_index = (current['anim_index'] + 1) % len(animations)
            start_animation(next_index, next_index == 0)
    else:
        advance_one_frame()

    draw_scene()
    delay(tick_time())

close_canvas()
