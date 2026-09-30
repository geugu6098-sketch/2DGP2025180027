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