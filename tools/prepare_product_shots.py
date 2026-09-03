# -*- coding: utf-8 -*-
"""
제품 사진 -> 웹용 컬러별 누끼 PNG

  입력 : assets/img/_src/  에 넣어 둔 원본 사진 (PNG/JPG)
  출력 : assets/img/bear-<color>.png  (배경 투명, 여백 정리, 긴 변 1200px)

쓰는 법:
    python tools/prepare_product_shots.py

동작:
  - 사진 네 귀퉁이에서 배경색을 재고, 배경색과의 색거리로 알파를 만든다.
    (밝기로 자르면 노란 곰이 같이 날아간다 - 반드시 색거리로 자른다)
  - 가로로 여러 마리가 늘어선 정렬컷이면 세로 빈 칸을 찾아 자동으로 쪼갠다.
    7마리면 사진 순서대로 red, orange, yellow, green, blue, purple, black 로 본다.
    한 마리만 있으면 파일 이름을 그대로 색 이름으로 쓴다.
  - 바닥 반사(그림자)는 알파가 옅으므로, 진한 픽셀이 끝나는 행에서 잘라 버린다.

핑크:
  사진은 7색이고 사이트는 8색이다. --pink-from red 를 주면 빨강 곰의 색상만
  핑크(#FF2E88)로 돌려 bear-pink.png 를 만든다. 명암은 원본 그대로 쓰므로
  다른 7색과 같은 조명·같은 각도로 남는다.
"""
import io, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'assets', 'img', '_src')
DST = os.path.join(ROOT, 'assets', 'img')

# 사진 정렬 순서 (사용자가 보낸 7색 정렬컷 기준: 왼쪽 -> 오른쪽)
ROW_ORDER = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black']

MAX_EDGE = 1200      # 저장할 긴 변 픽셀
CUT_LO = 26          # 배경색과의 색거리 - 이 아래는 완전 투명
CUT_HI = 60          # 이 위는 완전 불투명 (사이는 부드럽게)
PINK = (0xFF, 0x2E, 0x88)


def alpha_from_bg(rgb):
    """배경색과의 색거리로 알파를 만든다"""
    h, w, _ = rgb.shape
    k = max(8, min(h, w) // 40)
    corners = np.concatenate([
        rgb[:k, :k].reshape(-1, 3), rgb[:k, -k:].reshape(-1, 3),
        rgb[-k:, :k].reshape(-1, 3), rgb[-k:, -k:].reshape(-1, 3),
    ])
    bg = np.median(corners, axis=0)
    d = np.linalg.norm(rgb.astype(np.float32) - bg, axis=2)
    a = np.clip((d - CUT_LO) / float(CUT_HI - CUT_LO), 0.0, 1.0)
    return a, bg


def runs(mask1d, gap):
    """True 구간을 gap 이하 간격이면 이어 붙여 돌려준다"""
    idx = np.flatnonzero(mask1d)
    if not len(idx):
        return []
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > gap:
            out.append((s, p))
            s = i
        p = i
    out.append((s, p))
    return out


def cut_reflection(a, x0, x1):
    """진한 픽셀이 끝나는 행 아래(=바닥 반사)를 잘라 낸다"""
    strong = (a[:, x0:x1 + 1] > 0.85).sum(axis=1)
    rows = np.flatnonzero(strong > 1)
    return (rows[0], rows[-1]) if len(rows) else (0, a.shape[0] - 1)


def save(rgb, a, box, name):
    x0, x1, y0, y1 = box
    pad = max(4, int((x1 - x0) * 0.02))
    x0 = max(0, x0 - pad); x1 = min(rgb.shape[1] - 1, x1 + pad)
    y0 = max(0, y0 - pad); y1 = min(rgb.shape[0] - 1, y1 + pad)

    crop = rgb[y0:y1 + 1, x0:x1 + 1]
    ca = a[y0:y1 + 1, x0:x1 + 1]
    out = np.dstack([crop, (ca * 255).astype(np.uint8)])
    im = Image.fromarray(out, 'RGBA')

    s = MAX_EDGE / float(max(im.size))
    if s < 1:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

    path = os.path.join(DST, 'bear-%s.png' % name)
    im.save(path, optimize=True)
    print('  -> bear-%s.png  %dx%d  %dKB' % (name, im.width, im.height,
                                             os.path.getsize(path) // 1024))
    return path


def recolor_to_pink(src_path):
    """빨강 곰의 색상만 핑크로 돌린다 - 명암은 원본 그대로"""
    im = Image.open(src_path).convert('RGBA')
    arr = np.asarray(im).astype(np.float32)
    rgb, al = arr[..., :3], arr[..., 3:]

    mx = rgb.max(axis=2, keepdims=True)
    mn = rgb.min(axis=2, keepdims=True)
    v = mx / 255.0                       # 명도
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)   # 채도

    target = np.array(PINK, dtype=np.float32) / 255.0
    # 채도 있는 곳은 핑크 램프로, 무채색(하이라이트)은 원래 밝기로 남긴다
    tinted = (target[None, None, :] * v) * 255.0
    outrgb = tinted * s + rgb * (1 - s)

    out = np.dstack([np.clip(outrgb, 0, 255).astype(np.uint8), al.astype(np.uint8)])
    path = os.path.join(DST, 'bear-pink.png')
    Image.fromarray(out, 'RGBA').save(path, optimize=True)
    print('  -> bear-pink.png (red 에서 색상만 이동)  %dKB' % (os.path.getsize(path) // 1024))


def process(path, pink_from):
    print(os.path.basename(path))
    im = Image.open(path).convert('RGB')
    rgb = np.asarray(im)
    a, bg = alpha_from_bg(rgb)
    print('  배경색 %s / %dx%d' % (tuple(int(v) for v in bg), im.width, im.height))

    col = (a > 0.6).sum(axis=0)
    lim = max(3, int(im.height * 0.01))
    segs = [r for r in runs(col > lim, gap=max(6, im.width // 120))
            if (r[1] - r[0]) > im.width * 0.02]
    print('  피사체 %d개' % len(segs))
    if not segs:
        print('  ! 피사체를 못 찾았다. 배경이 흰색/단색인지 확인할 것.')
        return

    if len(segs) == len(ROW_ORDER):
        names = ROW_ORDER
    elif len(segs) == 1:
        names = [os.path.splitext(os.path.basename(path))[0].lower()]
    else:
        names = ['%02d' % (i + 1) for i in range(len(segs))]
        print('  ! 7마리도 한 마리도 아니라 번호로 저장한다. 파일명을 확인할 것.')

    made = {}
    for (x0, x1), name in zip(segs, names):
        y0, y1 = cut_reflection(a, x0, x1)
        made[name] = save(rgb, a, (x0, x1, y0, y1), name)

    if pink_from and pink_from in made:
        recolor_to_pink(made[pink_from])


def main():
    pink_from = None
    if '--pink-from' in sys.argv:
        pink_from = sys.argv[sys.argv.index('--pink-from') + 1]

    if not os.path.isdir(SRC):
        os.makedirs(SRC)
    files = [os.path.join(SRC, f) for f in sorted(os.listdir(SRC))
             if os.path.splitext(f)[1].lower() in ('.png', '.jpg', '.jpeg', '.webp')]
    if not files:
        print('assets/img/_src/ 가 비어 있다. 원본 사진을 넣고 다시 실행할 것.')
        print('경로:', SRC)
        return
    for f in files:
        process(f, pink_from)


if __name__ == '__main__':
    main()
