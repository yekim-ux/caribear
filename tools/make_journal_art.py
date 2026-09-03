# -*- coding: utf-8 -*-
"""
저널 3편에 쓸 이미지를 기존 렌더에서 만든다.

  python tools/make_journal_art.py [--detail <디테일컷 폴더>] [--frames <턴테이블 프레임 폴더>]

출력
  assets/img/journal-shades-row.webp    8셰이드 한 줄 정렬 (저널 01 히어로)
  assets/img/journal-strip.webp         턴테이블에서 뽑은 회전 6컷 필름 스트립 (저널 02)
  assets/img/journal-macro-<c>.webp     래티스 근접컷
  assets/img/journal-section-<c>.webp   단면컷
  assets/img/journal-structure-<c>.webp 납작한 구조도

디테일컷·프레임은 Blender 로 먼저 뽑아 둔 것을 받아 WebP 로만 바꾼다.
  tools/blender_detail_shots.py   -> 매크로 · 단면 · 구조도
  tools/blender_turntable.py      -> 회전 프레임
"""
import argparse, glob, os
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'assets', 'img', '_render')
IMG = os.path.join(ROOT, 'assets', 'img')

SHADES = ['grey', 'blush', 'peach', 'butter', 'mint', 'sky', 'lilac', 'rose']


def save(im, name, q=84):
    p = os.path.join(IMG, name)
    im.save(p, 'WEBP', quality=q, method=6)
    print('  %-40s %4dx%-5d %6.0f KB' % (name, im.width, im.height,
                                         os.path.getsize(p) / 1024))


def fit_height(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def load_render(name):
    im = Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')
    return im.crop(im.getbbox())


def shades_row(h=560, gap_ratio=0.06):
    """8셰이드를 바닥 정렬로 한 줄. 저널 01 의 히어로."""
    tiles = [fit_height(load_render('bear-' + s), h) for s in SHADES]
    gap = int(h * gap_ratio)
    w = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for t in tiles:
        canvas.alpha_composite(t, (x, h - t.height))
        x += t.width + gap
    return canvas


def turntable_strip(frames_dir, count=6, h=420, gap_ratio=0.05):
    """회전 프레임에서 균등 간격으로 뽑아 필름 스트립처럼 늘어놓는다.
       모든 프레임을 같은 사각형으로 자른다 — 프레임마다 재면 곰이 위아래로 튄다."""
    frames = sorted(glob.glob(os.path.join(frames_dir, '*.png')))
    if not frames:
        return None
    box = None
    for p in frames:
        bb = Image.open(p).convert('RGBA').getbbox()
        if bb is None:
            continue
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]),
                                      max(box[2], bb[2]), max(box[3], bb[3]))
    step = len(frames) / float(count)
    picks = [frames[int(i * step)] for i in range(count)]
    tiles = [fit_height(Image.open(p).convert('RGBA').crop(box), h) for p in picks]
    gap = int(h * gap_ratio)
    w = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for t in tiles:
        canvas.alpha_composite(t, (x, 0))
        x += t.width + gap
    return canvas


def gallery_placeholders(n=9, size=1080):
    """저널 03 자리표시자.

    실사 착용컷을 받기 전까지 그리드를 채운다. 실제 사진처럼 보이면 안 되므로
    사람도 배경도 넣지 않고, 파스텔 면 + 흐린 제품 실루엣 + PENDING 라벨만 둔다.
    실제 컷이 오면 assets/img/styled/ 의 파일만 갈아 끼우면 된다."""
    from PIL import ImageDraw
    out = os.path.join(IMG, 'styled')
    os.makedirs(out, exist_ok=True)
    tones = [(255, 243, 245), (243, 248, 245), (255, 250, 238), (241, 246, 252),
             (250, 242, 246), (246, 243, 252), (253, 245, 240), (243, 250, 248),
             (252, 246, 249)]
    for i in range(n):
        shade = SHADES[i % len(SHADES)]
        canvas = Image.new('RGBA', (size, size), tones[i % len(tones)] + (255,))
        bear = fit_height(load_render('bear-' + shade + '-three'), int(size * 0.52))
        ghost = bear.copy()
        ghost.putalpha(ghost.getchannel('A').point(lambda v: int(v * 0.30)))
        canvas.alpha_composite(ghost, ((size - ghost.width) // 2, int(size * 0.20)))
        d = ImageDraw.Draw(canvas)
        label = 'PHOTO %02d  ·  PENDING' % (i + 1)
        d.text((size // 2, int(size * 0.87)), label, fill=(150, 130, 128, 255), anchor='mm')
        p = os.path.join(out, 'styled-%02d.webp' % (i + 1))
        canvas.convert('RGB').save(p, 'WEBP', quality=78, method=6)
    print('  자리표시자 %d장 -> assets/img/styled/' % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--detail', help='blender_detail_shots.py 결과 폴더')
    ap.add_argument('--frames', help='blender_turntable.py 프레임 폴더')
    ap.add_argument('--placeholders', action='store_true', help='저널 03 자리표시자 생성')
    a = ap.parse_args()

    if a.placeholders:
        print('저널 03 — 갤러리 자리표시자')
        gallery_placeholders()

    print('저널 01 — 8셰이드 한 줄')
    save(shades_row(), 'journal-shades-row.webp')

    if a.frames:
        print('저널 02 — 회전 스트립')
        strip = turntable_strip(a.frames)
        if strip:
            save(strip, 'journal-strip.webp')

    if a.detail:
        print('저널 02 — 구조 컷')
        for p in sorted(glob.glob(os.path.join(a.detail, 'journal-*.png'))):
            stem = os.path.splitext(os.path.basename(p))[0]
            im = Image.open(p).convert('RGBA')
            im = im.crop(im.getbbox())
            if im.height > 1200:
                im = fit_height(im, 1200)
            save(im, stem + '.webp')


if __name__ == '__main__':
    main()
