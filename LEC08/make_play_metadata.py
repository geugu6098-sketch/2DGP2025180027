"""character_play.png 스프라이트 시트를 분석해 재생용 메타데이터를 만든다.

원본 시트는 흰 배경 위에 4행 x 8열로 나열되어 있다.
  - 행  : 그림이 그려진 구간(행 밴드)을 자동 검출해 4개로 분리한다.
  - 열  : 인접 스프라이트가 서로 겹치는 곳이 있으므로 균일 분할을 쓰지 않고,
          경계 후보 주변에서 잉크가 가장 적은 골짜기(plateau)의 중앙을 경계로
          삼는다.
  - 겹침 : 펀치/킥처럼 팔이나 다리가 옆 프레임 안까지 뻗어 있다. 그래서 겹친
          부분을 통째로 잘라내면 진짜 다리가 사라진다. 대신 행 밴드 전체를 한 번
          연결 요소로 나누고, 각 요소의 픽셀이 가장 많이 들어 있는 칸(프레임)에
          그 요소의 주인을 정한다. 그 칸의 프레임만 그 요소를 쓰고, 다른 칸은
          버린다. 그러면 옆 프레임의 팔다리가 화면에 섞이지 않는다.
  - 프레임: 위 처리를 마친 칸 안에서 실제 그림자 경계(tight bbox)로 자른다.

버린 요소는 character_play_alpha.png 에서 투명 처리해 화면에 남지 않게 한다.
흰 배경은 테두리와 연결된 흰색만 지우므로 캐릭터 안의 흰색은 그대로 남는다.

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

# 애니메이션별 바닥 보정값(시트 픽셀). 값이 클수록 화면에서 더 위에 선다.
# 점프는 착지가 ground line 에 딱 붙어 바닥에 잠기는 느낌이라 띄워 준다.
ROW_GROUND_OFFSET = [0, 0, 0, 20]

# 흰색(255, 255, 255)과의 차이 합이 이 값보다 크면 그림으로 판단한다.
INK_THRESHOLD = 24

# 겹친 스프라이트의 경계를 찾을 때, 균일 경계 주변을 살펴보는 폭(픽셀)
SPLIT_WINDOW = 30

# 투명 처리할 때 흰색으로 간주하는 차이 합
ALPHA_THRESHOLD = 18


def ink_mask(image):
    """각 픽셀이 그림인지 나타내는 불리언 배열."""
    array = np.asarray(image.convert('RGB')).astype(np.int16)
    return (765 - array.sum(axis=2)) > INK_THRESHOLD


def find_row_bands(ink):
    """그림이 그려진 행 구간들을 찾아 (시작, 끝) 목록으로 돌려준다."""
    height = ink.shape[0]
    inked = ink.any(axis=1)

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


def column_profile(ink, top, bottom):
    """한 행 밴드에서 각 열에 그려진 잉크 픽셀 수."""
    return ink[top:bottom + 1].sum(axis=0).astype(int).tolist()


def find_splits(profile, width, count):
    """열 경계와 각 경계의 최소 잉크량을 찾는다."""
    splits = [0]
    levels = [0]

    for k in range(1, count):
        nominal = int(round(k * width / float(count)))
        lo = max(1, nominal - SPLIT_WINDOW)
        hi = min(width - 1, nominal + SPLIT_WINDOW)

        segment = profile[lo:hi + 1]
        lowest = min(segment)
        hits = [lo + i for i, v in enumerate(segment) if v == lowest]
        splits.append(hits[len(hits) // 2])
        levels.append(lowest)

    splits.append(width)
    levels.append(0)
    return splits, levels


def cell_edges(splits):
    """프레임별 가로 범위."""
    return [(splits[i], splits[i + 1] - 1) for i in range(len(splits) - 1)]


def label_components(mask):
    """상하좌우로 이어진 그림 덩어리마다 번호를 붙이고 크기를 돌려준다."""
    height, width = mask.shape
    labels = np.zeros((height, width), np.int32)
    sizes = {}

    ys, xs = np.nonzero(mask)
    current = 0

    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if labels[y0, x0]:
            continue
        current += 1
        labels[y0, x0] = current
        stack = [(y0, x0)]
        size = 0

        while stack:
            y, x = stack.pop()
            size += 1
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < height and 0 <= nx < width:
                    if mask[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))

        sizes[current] = size

    return labels, sizes


def assign_owners(labels, sizes, edges):
    """각 그림 덩어리를 픽셀이 가장 많이 들어 있는 프레임에게 배정한다."""
    owners = {}
    xs_of = {}

    for component in sizes:
        xs_of[component] = np.nonzero(labels == component)[1]

    for component, columns in xs_of.items():
        counts = []
        for left, right in edges:
            counts.append(int(((columns >= left) & (columns <= right)).sum()))
        owners[component] = int(np.argmax(counts))

    return owners, xs_of


def tight_box(mask):
    """그림이 남은 칸 안에서 실제 최소 사각형을 구한다."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def write_alpha_sheet(image, dropped, out_path):
    """테두리와 연결된 흰색 배경과, 버린 그림 덩어리를 투명 처리한다.

    흰색을 무조건 지우면 캐릭터 안의 흰색(눈, 옷 등)까지 사라지므로,
    이미지 테두리에서 시작해서 흰색만 따라가는 범위 채우기를 쓴다.
    """
    rgba = np.asarray(image.convert('RGBA')).astype(np.int16).copy()
    height, width = rgba.shape[:2]

    blank = ((255 - rgba[:, :, 0]) + (255 - rgba[:, :, 1])
             + (255 - rgba[:, :, 2])) <= ALPHA_THRESHOLD

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

    rgba[:, :, 3][reached | dropped] = 0
    Image.fromarray(rgba.astype(np.uint8), 'RGBA').save(out_path)
    return int((reached | dropped).sum())


def build():
    image = Image.open(SHEET_IMAGE).convert('RGB')
    sheet_width, sheet_height = image.size
    ink = ink_mask(image)

    bands = find_row_bands(ink)
    if len(bands) != len(ROW_NAMES):
        raise SystemExit('행 개수 불일치: 시트 %d행 / 설정 %d행'
                         % (len(bands), len(ROW_NAMES)))

    dropped = np.zeros(ink.shape, dtype=bool)
    animations = []
    notes = []

    for row, (top, bottom) in enumerate(bands):
        band = ink[top:bottom + 1]
        profile = column_profile(ink, top, bottom)
        splits, levels = find_splits(profile, sheet_width, COLUMN_COUNT)
        edges = cell_edges(splits)

        labels, sizes = label_components(band)
        owners, _ = assign_owners(labels, sizes, edges)

        frames = []
        for col in range(COLUMN_COUNT):
            left, right = edges[col]
            keep = np.zeros(band.shape, dtype=bool)
            for component, owner in owners.items():
                if owner == col:
                    keep |= labels == component

            if not keep.any():
                raise SystemExit('%s %d프레임: 남길 그림이 없다'
                                 % (ROW_NAMES[row], col + 1))

            removed = int((band[:, left:right + 1]
                           & ~keep[:, left:right + 1]).sum())
            if removed:
                dropped[top:top + band.shape[0], left:right + 1] |= \
                    band[:, left:right + 1] & ~keep[:, left:right + 1]
                notes.append('%s %d프레임에서 옆 프레임 그림 %dpx 제거'
                             % (ROW_NAMES[row], col + 1, removed))

            box = tight_box(keep[:, left:right + 1])
            frames.append({'x': left + box[0], 'y': top + box[1],
                           'w': box[2] - box[0] + 1,
                           'h': box[3] - box[1] + 1})

        notes.append('%s 열 경계 %s (경계 잉크 %s px)'
                     % (ROW_NAMES[row], splits[1:-1], levels[1:-1]))

        animations.append({
            'name': ROW_NAMES[row],
            'row': row,
            'row_top': top,
            'row_bottom': bottom,
            'frame_time': ROW_FRAME_TIME[row],
            'ground_offset': ROW_GROUND_OFFSET[row],
            'frames': frames,
        })

    cleared = write_alpha_sheet(image, dropped, ALPHA_IMAGE)

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

    return meta, notes, int(dropped.sum()), cleared


if __name__ == '__main__':
    result, log, dropped_count, cleared = build()

    print('시트 %dx%d, %d행 x %d열' % (
        result['sheet_width'], result['sheet_height'],
        result['row_count'], result['column_count']))

    for line in log:
        print('  ' + line)

    print()
    for anim in result['animations']:
        sizes = ['%dx%d' % (f['w'], f['h']) for f in anim['frames']]
        print('  %-6s %d프레임  ground_offset=%2d  크기 %s' % (
            anim['name'], len(anim['frames']), anim['ground_offset'],
            ' '.join(sizes)))

    print()
    print('%s 생성, %s 투명 처리 (기존 %dpx + 버린 그림 %dpx)'
          % (OUTPUT_JSON, ALPHA_IMAGE, cleared - dropped_count, dropped_count))
