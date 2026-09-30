"""character_play.png 스프라이트 시트의 메타데이터를 만든다.

이 시트는 흰 배경에 4행 x 8열로 나열된 실사 스프라이트 시트다.
- 열은 균일한 간격(시트 폭 / 8)으로 나뉜다.
- 행은 그림자가 그려진 영역(밴드)마다 하나씩이고, 행마다 높이가 다르다.
- 각 프레임은 셀 안의 실제 그림자 경계(tight bbox)로 잘라 낸다.
  따라서 프레임마다 크기가 서로 다르고, 점프 프레임은 발밑 위치도 다르다.

실행:  py make_play_metadata.py
출력:  character_play.json
"""

import json

from PIL import Image

SHEET_IMAGE = 'character_play.png'
OUTPUT_JSON = 'character_play.json'

# 시트를 나누는 열 개수 (시트 폭을 균등 분할한다)
COLUMN_COUNT = 8

# 행 순서에 대응하는 애니메이션 이름
ROW_NAMES = ['walk', 'punch', 'kick', 'jump']

# 프레임당 표시 시간(초). 빠른 동작일수록 짧게 표시한다.
ROW_FRAME_TIME = [0.12, 0.10, 0.10, 0.16]

# 흰색(255, 255, 255)과의 차이 합이 이 값보다 크면 그림으로 판단한다.
INK_THRESHOLD = 24

# 프레임 주위에 남길 여백(픽셀)
PADDING = 2


def is_ink(pixel):
    """흰색 배경이 아닌 픽셀이면 True."""
    r, g, b = pixel[:3]
    return (255 - r) + (255 - g) + (255 - b) > INK_THRESHOLD


def find_row_bands(image):
    """그림이 그려진 행 구간들을 찾아 (시작, 끝) 목록으로 돌려준다."""
    width, height = image.size
    pixels = image.load()

    inked = [any(is_ink(pixels[x, y]) for x in range(width))
             for y in range(height)]

    bands = []
    start = None
    for y in range(height):
        if inked[y] and start is None:
            start = y
        elif not inked[y] and start is not None:
            bands.append((start, y - 1))
            start = None
    if start is not None:
        bands.append((start, height - 1))

    return bands


def tight_box(image, left, top, right, bottom):
    """셀 안에서 실제로 그림이 있는 최소 사각형을 구한다."""
    width, height = image.size
    left = max(0, left)
    top = max(0, top)
    right = min(width - 1, right)
    bottom = min(height - 1, bottom)
    pixels = image.load()

    min_x, min_y, max_x, max_y = width, height, -1, -1
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if is_ink(pixels[x, y]):
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x < 0:
        return None

    return (max(left, min_x - PADDING), max(top, min_y - PADDING),
            min(right, max_x + PADDING), min(bottom, max_y + PADDING))


def build():
    image = Image.open(SHEET_IMAGE).convert('RGB')
    sheet_width, sheet_height = image.size

    bands = find_row_bands(image)
    if len(bands) != len(ROW_NAMES):
        raise SystemExit('행 개수 불일치: 시트 %d행 / 설정 %d행'
                         % (len(bands), len(ROW_NAMES)))

    pitch = sheet_width / float(COLUMN_COUNT)

    animations = []
    for row, (top, bottom) in enumerate(bands):
        frames = []
        for col in range(COLUMN_COUNT):
            left = int(round(col * pitch))
            right = int(round((col + 1) * pitch)) - 1

            box = tight_box(image, left, top, right, bottom)
            if box is None:
                raise SystemExit('%d행 %d열: 그림을 찾을 수 없다' % (row, col))

            min_x, min_y, max_x, max_y = box
            frames.append({
                'x': min_x,
                'y': min_y,
                'w': max_x - min_x + 1,
                'h': max_y - min_y + 1,
            })

        animations.append({
            'name': ROW_NAMES[row],
            'row': row,
            'row_top': top,
            'row_bottom': bottom,
            'frame_time': ROW_FRAME_TIME[row],
            'frames': frames,
        })

    meta = {
        'sheet_image': SHEET_IMAGE,
        'sheet_width': sheet_width,
        'sheet_height': sheet_height,
        'column_count': COLUMN_COUNT,
        'row_count': len(bands),
        'row_names': ROW_NAMES,
        'animations': animations,
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=2)

    return meta


if __name__ == '__main__':
    result = build()
    print('시트 %dx%d, %d행 x %d열' % (
        result['sheet_width'], result['sheet_height'],
        result['row_count'], result['column_count']))
    for anim in result['animations']:
        sizes = ['%dx%d' % (f['w'], f['h']) for f in anim['frames']]
        print('  %-6s %d프레임  행 y %d..%d  크기 %s' % (
            anim['name'], len(anim['frames']), anim['row_top'],
            anim['row_bottom'], ' '.join(sizes)))
    print('%s 생성 완료' % OUTPUT_JSON)
