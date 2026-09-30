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


def build_walk():
    """걷기: 6 프레임. 프레임마다 크기가 조금씩 다르다."""
    sizes = [(64, 64), (66, 66), (64, 64), (62, 64), (64, 64), (66, 66)]
    frames = []
    for i, (w, h) in enumerate(sizes):
        phase = 2.0 * math.pi * i / len(sizes)
        swing = math.sin(phase)
        frames.append(((w, h), make_pose(
            leg_front=swing * 22.0,
            leg_back=-swing * 22.0,
            arm_front=-swing * 20.0,
            arm_back=swing * 20.0,
            bob=abs(math.cos(phase)) * 0.18,
        )))
    return frames


def build_run():
    """뛰기: 8 프레임. 걷기보다 폭이 넓고 상체가 앞으로 기울어진다."""
    sizes = [(84, 88), (88, 90), (92, 88), (88, 86),
             (84, 90), (88, 92), (92, 88), (86, 86)]
    frames = []
    for i, (w, h) in enumerate(sizes):
        phase = 2.0 * math.pi * i / len(sizes)
        swing = math.sin(phase)
        pose = make_pose(
            lean=14.0,
            leg_front=swing * 38.0,
            leg_back=-swing * 38.0,
            arm_front=-swing * 34.0 - 20.0,
            arm_back=swing * 34.0 - 20.0,
            bob=abs(math.cos(phase)) * 0.42,
        )
        if i % 4 == 0:
            pose['dust'] = 3
        frames.append(((w, h), pose))
    return frames


def build_jump():
    """점프: 5 프레임. 프레임 높이가 웅크림->발사->정점->하강->착지 순으로 달라진다."""
    specs = [
        ((70, 84), dict(crouch=0.55, leg_front=26.0, leg_back=-26.0,
                        arm_front=-30.0, arm_back=30.0, bob=0.10)),
        ((76, 104), dict(crouch=0.10, leg_front=-18.0, leg_back=22.0,
                         arm_front=-150.0, arm_back=150.0)),
        ((92, 128), dict(leg_front=-24.0, leg_back=20.0,
                         arm_front=-165.0, arm_back=160.0, bob=-0.15)),
        ((86, 116), dict(leg_front=16.0, leg_back=-22.0,
                         arm_front=-140.0, arm_back=120.0)),
        ((72, 86), dict(crouch=0.60, leg_front=30.0, leg_back=-28.0,
                        arm_front=-50.0, arm_back=50.0, dust=4)),
    ]
    return [(size, make_pose(**params)) for size, params in specs]


def build_attack():
    """공격: 10 프레임. 예비 동작은 좁고, 참격 순간은 좌우로 길게 늘어난다."""
    specs = [
        ((72, 96), dict(lean=-8.0, arm_front=-40.0, arm_back=60.0,
                        leg_front=16.0, leg_back=-16.0, sword=True)),
        ((70, 96), dict(lean=-14.0, arm_front=-70.0, arm_back=80.0,
                        leg_front=20.0, leg_back=-18.0, sword=True)),
        ((72, 96), dict(lean=-18.0, arm_front=-110.0, arm_back=95.0,
                        leg_front=24.0, leg_back=-20.0, sword=True)),
        ((76, 96), dict(lean=-20.0, arm_front=-140.0, arm_back=100.0,
                        leg_front=28.0, leg_back=-22.0, sword=True)),
        ((96, 96), dict(lean=6.0, arm_front=40.0, arm_back=-40.0,
                        leg_front=30.0, leg_back=-24.0, sword=True, slash=0.35)),
        ((112, 96), dict(lean=12.0, arm_front=70.0, arm_back=-50.0,
                         leg_front=34.0, leg_back=-26.0, sword=True, slash=0.80)),
        ((104, 96), dict(lean=10.0, arm_front=95.0, arm_back=-45.0,
                         leg_front=30.0, leg_back=-24.0, sword=True, slash=1.00)),
        ((92, 96), dict(lean=4.0, arm_front=110.0, arm_back=-30.0,
                        leg_front=24.0, leg_back=-20.0, sword=True)),
        ((84, 96), dict(lean=0.0, arm_front=100.0, arm_back=-10.0,
                        leg_front=18.0, leg_back=-16.0, sword=True)),
        ((80, 96), dict(lean=-2.0, arm_front=20.0, arm_back=18.0,
                        leg_front=14.0, leg_back=-14.0, sword=True)),
    ]
    return [(size, make_pose(**params)) for size, params in specs]


# (애니메이션 이름, 프레임 생성 함수, 한 프레임 재생 시간(초))
ANIMATIONS = [
    ('walk', build_walk, 0.12),
    ('run', build_run, 0.07),
    ('jump', build_jump, 0.11),
    ('attack', build_attack, 0.06),
]


def pack_frames(frames, max_width):
    """프레임들을 가로줄(shelf) 방식으로 시트에 배치하고 좌표를 돌려준다.

    frames: [(image, (w, h)), ...]
    반환:    [((x, y, w, h), (pivot_x, pivot_y)), ...]
    """
    placed = []
    x = FRAME_PADDING
    y = FRAME_PADDING
    row_height = 0

    for image, (w, h) in frames:
        if x + w + FRAME_PADDING > max_width and row_height > 0:
            x = FRAME_PADDING
            y += row_height + FRAME_PADDING
            row_height = 0

        placed.append(((x, y, w, h), (w / 2.0, h)))

        x += w + FRAME_PADDING
        row_height = max(row_height, h)

    sheet_width = max_width
    sheet_height = y + row_height + FRAME_PADDING
    return placed, sheet_width, sheet_height


def build_sheet():
    """모든 애니메이션을 하나의 스프라이트 시트 PNG 와 JSON 메타데이터로 만든다."""
    blocks = []
    for name, builder, frame_time in ANIMATIONS:
        rendered = []
        for (w, h), pose in builder():
            rendered.append((render_character(w, h, pose), (w, h)))
        blocks.append((name, rendered, frame_time))

    # 전체 프레임을 순서대로 이어붙인 뒤 한 번에 패킹한다
    flat = []
    for _, frames, _ in blocks:
        flat.extend(frames)

    placed, sheet_w, sheet_h = pack_frames(flat, SHEET_MAX_WIDTH)
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (0, 0, 0, 0))

    cursor = 0
    animations = []
    for name, frames, frame_time in blocks:
        records = []
        for image, (w, h) in frames:
            (x, y, pw, ph), (pivot_x, pivot_y) = placed[cursor]
            cursor += 1
            sheet.paste(image, (x, y))
            records.append({
                'x': x,
                'y': y,
                'w': pw,
                'h': ph,
                'pivot_x': round(pivot_x, 2),
                'pivot_y': round(pivot_y, 2),
            })
        animations.append({
            'name': name,
            'frame_time': frame_time,
            'frames': records,
        })

    sheet.save(OUTPUT_IMAGE)
    print('%s (%dx%d) 저장' % (OUTPUT_IMAGE, sheet_w, sheet_h))

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as fp:
        json.dump({
            'image': OUTPUT_IMAGE,
            'sheet_width': sheet_w,
            'sheet_height': sheet_h,
            'uniform_frame_size': False,
            'animations': animations,
        }, fp, ensure_ascii=False, indent=2)
    print('%s 저장' % OUTPUT_JSON)

    for anim in animations:
        print('  %-7s 프레임 %2d개  크기 %s' % (
            anim['name'],
            len(anim['frames']),
            sorted({(f['w'], f['h']) for f in anim['frames']}),
        ))


if __name__ == '__main__':
    build_sheet()