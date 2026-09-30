"""character_play.png 스프라이트 시트를 분석해 재생용 메타데이터를 만든다.

원본 시트는 흰 배경 위에 4행 x 8열로 나열되어 있다.
  - 행  : 그림이 그려진 구간(행 밴드)을 자동 검출해 4개로 분리한다.
  - 열  : 인접 스프라이트가 서로 겹치는 곳이 있으므로 균일 분할을 쓰지 않는다.
          각 경계 후보 주변에서 잉크가 가장 적은 골짜기(plateau)를 찾아
          그 중앙을 경계로 삼아, 서로의 그림이 섞이거나 잘리지 않게 한다.
  - 프레임: 셀 안의 실제 그림자 경계(tight bbox)로 자른다.

흰 배경은 투명 처리한 시트 character_play_alpha.png 도 함께 만든다.
테두리와 연결된 흰색만 지우므로 캐릭터 안의 흰색은 그대로 남는다.

실행:  py make_play_metadata.py
"""

import json

import numpy as np
from PIL import Image

SHEET_IMAGE = 'character_play.png'
ALPHA_IMAGE = 'character_play_alpha.png'
OUTPUT_JSON = 'character_play.json'

COLUMN_COUNT = 8

# 행 순서에 대응하는 애니메이션 이름
ROW_NAMES = ['walk', 'punch', 'kick', 'jump']

# 프레임당 표시 시간(초). 빠른 동작일수록 짧게 표시한다.
ROW_FRAME_TIME = [0.12, 0.09, 0.09, 0.15]

# 흰색(255, 255, 255)과의 차이 합이 이 값보다 크면 그림으로 판단한다.
INK_THRESHOLD = 24

# 겹친 스프라이트의 경계를 찾을 때, 균일 경계 주변을 살펴보는 폭(픽셀)
SPLIT_WINDOW = 30

# 투명 처리할 때 흰색으로 간주하는 차이 합
ALPHA_THRESHOLD = 18


def deficit(pixel):
    """흰색에서 얼마나 벗어났는지(0 이면 순백색)."""
    r, g, b = pixel[:3]
    return (255 - r) + (255 - g) + (255 - b)


def is_ink(pixel):
    return deficit(pixel) > INK_THRESHOLD


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


def column_profile(image, top, bottom):
    """한 행 밴드에서 각 열에 그려진 잉크 픽셀 수."""
    width = image.size[0]
    pixels = image.load()
    return [sum(1 for y in range(top, bottom + 1) if is_ink(pixels[x, y]))
            for x in range(width)]


def find_splits(profile, width, count):
    """열 경계를 찾는다.

    균일하게 8등분하면 서로 겹친 스프라이트가 잘린다. 그래서 각 경계 후보 주변에서
    잉크가 가장 적은 골짜기를 찾고, 그 골짜기의 중앙을 경계로 삼는다.
    """
    splits = [0]
    report = []

    for k in range(1, count):
        nominal = int(round(k * width / float(count)))
        lo = max(1, nominal - SPLIT_WINDOW)
        hi = min(width - 1, nominal + SPLIT_WINDOW)

        segment = profile[lo:hi + 1]
        lowest = min(segment)
        hits = [lo + i for i, v in enumerate(segment) if v == lowest]
        split = hits[len(hits) // 2]

        splits.append(split)
        report.append((k, nominal, split, lowest))

    splits.append(width)
    return splits, report


def tight_box(image, left, top, right, bottom):
    """셀 안에서 실제로 그림이 있는 최소 사각형을 구한다.

    여백을 두지 않는다. 경계 근처에 이웃 스프라이트의 잉크가 있을 수 있기 때문에
    여백을 넣으면 그것까지 딸려서 이전 동작의 일부분이 화면에 나오게 된다.
    """
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

    return min_x, min_y, max_x, max_y


def write_alpha_sheet(image, out_path):
    """테두리와 연결된 흰색 배경만 투명 처리한 시트를 저장한다.

    흰색을 무조건 지우면 캐릭터 안의 흰색(눈, 옷 등)까지 사라지므로,
    이미지 테두리에서 시작해서 흰색만 따라가는 범위 채우기를 쓴다.
    """
    rgba = image.convert('RGBA')
    width, height = rgba.size
    data = np.asarray(rgba).astype(np.int16).copy()

    blank = ((255 - data[:, :, 0]) + (255 - data[:, :, 1])
             + (255 - data[:, :, 2])) <= ALPHA_THRESHOLD

    reached = np.zeros((height, width), dtype=bool)
    stack = []

    for x in range(width):
        for y in (0, height - 1):
            if blank[y, x] and not reached[y, x]:
                reached[y, x] = True
                stack.append((y, x))
    for y in range(height):
        for x in (0, width - 1):
            if blank[y, x] and not reached[y, x]:
                reached[y, x] = True
                stack.append((y, x))

    while stack:
        y, x = stack.pop()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < height and 0 <= nx < width:
                if blank[ny, nx] and not reached[ny, nx]:
                    reached[ny, nx] = True
                    stack.append((ny, nx))

    data[:, :, 3][reached] = 0
    Image.fromarray(data.astype(np.uint8), 'RGBA').save(out_path)
    return int(reached.sum())


def build():
    image = Image.open(SHEET_IMAGE).convert('RGB')
    sheet_width, sheet_height = image.size

    bands = find_row_bands(image)
    if len(bands) != len(ROW_NAMES):
        raise SystemExit('행 개수 불일치: 시트 %d행 / 설정 %d행'
                         % (len(bands), len(ROW_NAMES)))

    animations = []
    notes = []

    for row, (top, bottom) in enumerate(bands):
        profile = column_profile(image, top, bottom)
        splits, report = find_splits(profile, sheet_width, COLUMN_COUNT)

        frames = []
        for col in range(COLUMN_COUNT):
            box = tight_box(image, splits[col], top,
                            splits[col + 1] - 1, bottom)
            if box is None:
                raise SystemExit('%d행 %d열: 그림을 찾을 수 없다' % (row, col))
            frames.append({'x': box[0], 'y': box[1],
                           'w': box[2] - box[0] + 1,
                           'h': box[3] - box[1] + 1})

        for k, nominal, split, lowest in report:
            notes.append('%d행 %d열경계: 균일 %d -> 실제 %d (겹침 잉크 %dpx)'
                         % (row, k, nominal, split, lowest))

        animations.append({
            'name': ROW_NAMES[row],
            'row': row,
            'row_top': top,
            'row_bottom': bottom,
            'frame_time': ROW_FRAME_TIME[row],
            'frames': frames,
        })

    cleared = write_alpha_sheet(image, ALPHA_IMAGE)

    meta = {
        'sheet_image': ALPHA_IMAGE,
        'source_image': SHEET_IMAGE,
        'sheet_width': sheet_width,
        'sheet_height': sheet_height,
        'column_count': COLUMN_COUNT,
        'row_count': len(bands),
        'row_names': ROW_NAMES,
        'animations': animations,
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=2)

    return meta, notes, cleared


if __name__ == '__main__':
    result, log, cleared = build()

    print('시트 %dx%d, %d행 x %d열' % (
        result['sheet_width'], result['sheet_height'],
        result['row_count'], result['column_count']))

    for line in log:
        print('  ' + line)

    print()
    for anim in result['animations']:
        sizes = ['%dx%d' % (f['w'], f['h']) for f in anim['frames']]
        print('  %-6s %d프레임  크기 %s' % (
            anim['name'], len(anim['frames']), ' '.join(sizes)))

    print()
    print('%s 생성, %s 투명 처리 (%d px)' % (OUTPUT_JSON, ALPHA_IMAGE, cleared))
