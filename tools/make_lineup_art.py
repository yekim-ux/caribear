# -*- coding: utf-8 -*-
"""
라인업 3종(BASIC / MINI / STICKER) 섹션에 쓸 이미지를 기존 렌더에서 만든다.

  python tools/make_lineup_art.py

입력 : assets/img/_render/bear-<shade>[-angle].png   (Blender 원본 900×1710 RGBA)
출력 : assets/img/lineup-size.webp        BASIC + MINI 크기 비교컷
       assets/img/lineup-mini.webp        MINI 단독컷 (BASIC 과 같은 캔버스, 작게 앉힌다)
       assets/img/sticker-sheet.webp      다이컷 스티커 여러 장
       assets/img/sm/sticker-<shade>.webp 스티커 낱장 (작은 슬롯용)

## 왜 Blender 를 다시 안 도는가

카메라가 **오소(ORTHO)** 라서, 오브젝트를 균등 배율로 줄인 렌더는 그 렌더 이미지를
같은 비율로 축소한 것과 픽셀 단위로 같다. 원근 카메라였다면 다시 렌더해야 하지만
오소에서는 이미지 축소가 곧 정답이다. LANDING_KIT.md §9 의 "균등 배율만 허용" 도 그대로 지킨다.

## 다이컷 스티커

실루엣 알파를 넓혀(dilate) 흰 테두리를 만든다. 래티스 구멍까지 흰색으로 메워지는데,
이건 버그가 아니라 실제 다이컷 스티커의 모양이다 — 구멍 뒤로 흰 배지가 비친다.
"""
import os
from PIL import Image, ImageFilter, ImageChops

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'assets', 'img', '_render')
IMG = os.path.join(ROOT, 'assets', 'img')
SM = os.path.join(IMG, 'sm')

MINI_RATIO = 0.62          # 기본 65×65×95MM -> 미니 40×40×58MM. 선형 비율.
STICKER_SHADES = ['blush', 'mint', 'butter', 'sky', 'rose', 'lilac']


def load(name):
    p = os.path.join(SRC, 'bear-' + name + '.png')
    im = Image.open(p).convert('RGBA')
    return im.crop(im.getbbox())


def save(im, path, q=84):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, 'WEBP', quality=q, method=6)
    print('  %-38s %4dx%-4d %6.0f KB' % (os.path.relpath(path, ROOT),
                                         im.width, im.height,
                                         os.path.getsize(path) / 1024))


def fit_height(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def shadow(alpha, blur, offset, opacity):
    """알파에서 만든 부드러운 그림자 레이어(검정)."""
    sh = alpha.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    layer = Image.new('RGBA', alpha.size, (120, 90, 82, 0))
    layer.putalpha(sh)
    return ImageChops.offset(layer, offset[0], offset[1])


# ---------------------------------------------------------------- 크기 비교컷
def size_pair(shade='blush', big_h=1000, gap_ratio=0.10, pad_ratio=0.05):
    """BASIC 과 MINI 를 바닥 정렬로 나란히. 둘의 비율이 곧 실제 치수 비율이다.
       크기 비교가 목적이므로 **같은 각도(front)** 를 쓴다 — 각도가 다르면 실루엣 폭이
       달라져서 '작아 보이는' 건지 '돌아간' 건지 헷갈린다."""
    big = fit_height(load(shade), big_h)
    small = fit_height(load(shade), int(round(big_h * MINI_RATIO)))

    gap = int(big.width * gap_ratio)
    pad = int(big_h * pad_ratio)
    w = big.width + gap + small.width + pad * 2
    h = big_h + pad * 2
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(big, (pad, pad))
    canvas.alpha_composite(small, (pad + big.width + gap, h - pad - small.height))
    return canvas


def mini_alone(shade='blush', canvas_h=1100):
    """MINI 단독컷. BASIC 컷과 '같은 캔버스'에 작게 앉혀서, 사이트에서 같은 슬롯에
       넣어도 크기 차이가 그대로 보이게 한다."""
    small = fit_height(load(shade + '-three'), int(round(canvas_h * MINI_RATIO)))
    canvas = Image.new('RGBA', (round(canvas_h * 0.5636), canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(small, ((canvas.width - small.width) // 2,
                                   canvas_h - small.height))
    return canvas


# ---------------------------------------------------------------- 다이컷 스티커
def die_cut_from(bear, border_px=None):
    """실루엣을 넓혀 흰 테두리를 만들고 그 위에 곰을 얹는다."""
    pad = int(bear.height * 0.07)
    base = Image.new('RGBA', (bear.width + pad * 2, bear.height + pad * 2), (0, 0, 0, 0))
    base.alpha_composite(bear, (pad, pad))

    alpha = base.getchannel('A')
    b = border_px or max(6, int(bear.height * 0.030))
    grown = alpha
    # MaxFilter 는 홀수 커널만 받는다. 여러 번 돌려서 원하는 두께까지 넓힌다.
    step = 9
    for _ in range(max(1, b // (step // 2))):
        grown = grown.filter(ImageFilter.MaxFilter(step))
    grown = grown.point(lambda v: 255 if v > 40 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 128 else 0)

    white = Image.new('RGBA', base.size, (255, 255, 255, 255))
    white.putalpha(grown)

    out = Image.new('RGBA', base.size, (0, 0, 0, 0))
    out.alpha_composite(shadow(grown, blur=b * 0.9, offset=(0, int(b * 0.5)), opacity=0.30))
    out.alpha_composite(white)
    out.alpha_composite(base)
    return out


# 스티커 팩처럼 흩어 놓기 위한 각도. 규칙적으로 반복되면 인쇄 시트처럼 보여서
# 손으로 뿌려 둔 느낌이 나도록 값을 불규칙하게 잡았다.
SCATTER = [-9, 6, -3, 8, -6, 4]


def sticker_sheet(shades, tile_h=500, cols=3, gap_ratio=0.10):
    tiles = []
    for i, sh in enumerate(shades):
        t = die_cut_from(fit_height(load(sh + ('-three' if i % 2 else '')), tile_h))
        tiles.append(t.rotate(SCATTER[i % len(SCATTER)], resample=Image.BICUBIC,
                              expand=True))
    rows = (len(tiles) + cols - 1) // cols
    tw = max(t.width for t in tiles)
    th = max(t.height for t in tiles)
    gx, gy = int(tw * gap_ratio), int(th * gap_ratio * 0.5)
    canvas = Image.new('RGBA', ((tw + gx) * cols - gx, (th + gy) * rows - gy), (0, 0, 0, 0))
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        x = (tw + gx) * c + (tw - t.width) // 2
        y = (th + gy) * r + (th - t.height) // 2
        canvas.alpha_composite(t, (x, y))
    return canvas


def main():
    print('크기 비교 / 미니 단독')
    save(size_pair(), os.path.join(IMG, 'lineup-size.webp'))
    save(mini_alone(), os.path.join(IMG, 'lineup-mini.webp'))
    save(fit_height(mini_alone(), 420), os.path.join(SM, 'lineup-mini.webp'), q=80)

    print('다이컷 스티커')
    save(sticker_sheet(STICKER_SHADES), os.path.join(IMG, 'sticker-sheet.webp'))
    for s in STICKER_SHADES:
        save(fit_height(die_cut_from(fit_height(load(s), 900)), 420),
             os.path.join(SM, 'sticker-%s.webp' % s), q=80)
    save(fit_height(die_cut_from(fit_height(load('blush'), 1400)), 1100),
         os.path.join(IMG, 'sticker-blush.webp'))


if __name__ == '__main__':
    main()
