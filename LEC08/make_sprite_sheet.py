"""스프라이트 시트 생성기.

LEC08/animation_viewer.py 에서 사용할 캐릭터 스프라이트 시트를 만든다.
- 애니메이션 4종(walk / run / jump / attack)을 하나의 PNG 에 담는다.
- 프레임마다 크기가 서로 다른 '복잡한 스프라이트 시트'를 만든다.
- 애니메이션마다 프레임 개수도 서로 다르게 만든다.
- 프레임 위치/크기/기준점 정보는 character_sheet.json 으로 저장한다.
"""

import json
import math
import os

from PIL import Image, ImageDraw

OUTPUT_IMAGE = 'character_sheet.png'
OUTPUT_JSON = 'character_sheet.json'

# 스프라이트 시트를 몇 픽셀 폭까지 채울지 정한다 (shelf packing 기준 폭)
SHEET_MAX_WIDTH = 1024

# 프레임 사이 여백
FRAME_PADDING = 2

COLOR_OUTLINE = (22, 22, 30, 255)
COLOR_SKIN = (255, 216, 178, 255)
COLOR_SHIRT = (64, 126, 214, 255)
COLOR_PANTS = (44, 52, 78, 255)
COLOR_SHOE = (28, 28, 36, 255)
COLOR_SWORD = (226, 234, 244, 255)
COLOR_SWORD_HANDLE = (140, 92, 48, 255)
COLOR_FX = (255, 208, 84, 255)

# 기본 포즈: 모든 값을 명시하지 않은 키는 이 값을 사용한다
DEFAULT_POSE = {
    'bob': 0.0,
    'lean': 0.0,
    'crouch': 0.0,
    'arm_front': -18.0,
    'arm_back': 18.0,
    'leg_front': 12.0,
    'leg_back': -12.0,
    'sword': False,
    'slash': None,
    'dust': 0,
}


def make_pose(**kwargs):
    """기본 포즈를 복사한 뒤 지정된 값만 덮어쓴 포즈를 만든다."""
    pose = dict(DEFAULT_POSE)
    pose.update(kwargs)
    return pose


def rotate_point(x, y, origin_x, origin_y, degrees):
    """(origin_x, origin_y) 기준으로 degrees 만큼 회전한 좌표를 반환한다."""
    rad = math.radians(degrees)
    dx = x - origin_x
    dy = y - origin_y
    return (origin_x + dx * math.cos(rad) - dy * math.sin(rad),
            origin_y + dx * math.sin(rad) + dy * math.cos(rad))


def draw_limb(draw, origin, length, angle, thickness, color):
    """origin 에서 angle(수직 아래가 0도) 방향으로 길이 length 만큼 뻗는 팔다리를 그린다."""
    x0, y0 = origin
    rad = math.radians(angle)
    x1 = x0 + length * math.sin(rad)
    y1 = y0 + length * math.cos(rad)
    draw.line([(x0, y0), (x1, y1)], fill=color, width=thickness)
    return (x1, y1)


def draw_dust(draw, cx, ground, unit, amount):
    """점프 착지/달리기 때 바닥에 먼지를 그린다."""
    for i in range(amount):
        spread = (i - (amount - 1) / 2.0) * unit * 0.8
        radius = unit * (0.22 + 0.05 * (i % 2))
        y = ground - unit * 0.12 * (amount - i)
        draw.ellipse([cx + spread - radius, y - radius,
                      cx + spread + radius, y + radius],
                     fill=(220, 214, 200, 190))


def draw_slash(draw, cx, cy, unit, progress):
    """공격 애니메이션의 참격 궤적을 그린다."""
    if progress is None:
        return
    radius = unit * 3.4
    start = -95.0
    end = start + 110.0 * progress
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(bbox, start, end, fill=COLOR_FX, width=max(2, int(unit * 0.30)))


def render_character(width, height, pose):
    """포즈를 받아 width x height 크기의 캐릭터 프레임 이미지를 만든다."""
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    unit = min(width, height) / 8.0
    cx = width / 2.0
    ground = height - unit * 0.25

    hip_y = ground - unit * 3.1 + pose['crouch'] * unit + pose['bob'] * unit
    shoulder_y = hip_y - unit * 2.0

    # 상체는 hip 을 기준으로 lean 만큼 앞으로 기울인다
    shoulder_x, shoulder_y = rotate_point(cx, shoulder_y, cx, hip_y, pose['lean'])
    head_x, head_y = rotate_point(cx, hip_y - unit * 2.95, cx, hip_y, pose['lean'])

    limb_w = max(2, int(unit * 0.55))

    # 다리 (뒤쪽을 먼저 그려서 앞다리가 위에 오게 한다)
    back_foot = draw_limb(draw, (cx, hip_y), unit * 1.9,
                          pose['leg_back'], limb_w, COLOR_PANTS)
    front_foot = draw_limb(draw, (cx, hip_y), unit * 1.9,
                           pose['leg_front'], limb_w, COLOR_PANTS)

    # 몸통
    draw.line([(cx, hip_y), (shoulder_x, shoulder_y)],
              fill=COLOR_SHIRT, width=max(2, int(unit * 1.05)))

    # 팔
    back_hand = draw_limb(draw, (shoulder_x, shoulder_y), unit * 1.7,
                          pose['arm_back'], limb_w, COLOR_SHIRT)
    front_hand = draw_limb(draw, (shoulder_x, shoulder_y), unit * 1.7,
                           pose['arm_front'], limb_w, COLOR_SHIRT)

    # 머리
    head_r = unit * 0.68
    draw.ellipse([head_x - head_r, head_y - head_r,
                  head_x + head_r, head_y + head_r], fill=COLOR_SKIN)
    draw.ellipse([head_x - head_r * 0.9, head_y - head_r * 1.1,
                  head_x + head_r * 0.9, head_y - head_r * 0.2],
                 fill=COLOR_OUTLINE)
    eye_r = max(1.0, unit * 0.12)
    draw.ellipse([head_x + head_r * 0.15 - eye_r, head_y - eye_r,
                  head_x + head_r * 0.15 + eye_r, head_y + eye_r],
                 fill=COLOR_OUTLINE)

    # 신발
    shoe_w = unit * 0.55
    shoe_h = unit * 0.32
    for foot in (back_foot, front_foot):
        draw.ellipse([foot[0] - shoe_w, foot[1] - shoe_h * 0.4,
                      foot[0] + shoe_w, foot[1] + shoe_h],
                     fill=COLOR_SHOE)

    if pose['sword']:
        sword_rad = math.radians(pose['arm_front'] - 70.0)
        blade_len = unit * 2.6
        hilt = (front_hand[0] - unit * 0.35 * math.sin(sword_rad),
                front_hand[1] - unit * 0.35 * math.cos(sword_rad))
        tip = (hilt[0] + blade_len * math.sin(sword_rad),
               hilt[1] + blade_len * math.cos(sword_rad))
        draw.line([hilt, tip], fill=COLOR_SWORD, width=max(2, int(unit * 0.24)))
        draw.line([front_hand, hilt], fill=COLOR_SWORD_HANDLE,
                  width=max(2, int(unit * 0.30)))

    draw_slash(draw, cx + unit * 0.4, shoulder_y, unit, pose['slash'])

    if pose['dust']:
        draw_dust(draw, cx, ground, unit, pose['dust'])

    return image