# -*- coding: utf-8 -*-
"""
blender_reel.py 가 뽑은 PNG 시퀀스(1..561) 뒤에 워드마크 카드(562..651)를 붙여
릴스용 mp4 하나로 인코딩한다.

    python tools/build_reel.py

원본 릴스에서 잰 아웃트로 스펙 (그대로 맞춘다):
    f561 에서 하드컷 — 페이드 없음. 이후 90프레임(3.0초) 완전 정지 카드.
    배경 #FDFDFD, 글자 상자 x177..542 / y607..672 → 정확히 화면 중앙, 캡높이 66px.

ffmpeg 는 imageio_ffmpeg 가 들고 있는 바이너리를 쓴다. PATH 에 ffmpeg 가 없다.

소리는 넣지 않는다. 원본 릴스의 음악은 남의 저작물이라 그대로 실을 수 없다.
"""
import glob
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
FPS = 30
LAST_3D = 561
TOTAL = 651

CARD_BG = (0xFD, 0xFD, 0xFD)
CARD_INK = (0x1A, 0x1A, 0x1A)
# 레퍼런스 캡 높이는 66px 이지만 그건 7글자(ANDAASH) 기준이다. CARIBEAR 는
# 여덟 글자라 같은 캡 높이로 짜면 글자 덩어리가 화면폭의 60% 를 먹는다
# (레퍼런스는 51%). 카드의 인상은 글자 크기보다 덩어리 크기가 만들어서 60px 로 낮춘다.
CARD_CAP_H = 60
CARD_TRACKING = 0.02       # em 단위. 레퍼런스가 살짝 벌어져 있다
WORDMARK = 'CARIBEAR'

# 사이트 워드마크는 Poppins SemiBold 인데 로컬에 없다. Century Gothic Bold 가
# 같은 지오메트릭 산세라 대체로 쓴다. Poppins 를 설치하면 여기만 바꾸면 된다.
FONT_CANDIDATES = [
    r'C:\Windows\Fonts\GOTHICB.TTF',
    r'C:\Windows\Fonts\Poppins-SemiBold.ttf',
    r'C:\Windows\Fonts\arialbd.ttf',
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, 'assets', 'video', '_reel')
OUT = os.path.join(ROOT, 'assets', 'video', 'caribear-reel.mp4')
OUT_ACTUAL = [OUT]


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def pick_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit('쓸 만한 산세 폰트를 못 찾았다: ' + ', '.join(FONT_CANDIDATES))


def fit_font(path, text, cap_h):
    """캡 높이가 cap_h 픽셀이 되는 폰트 크기를 찾는다.

    대문자만 쓰므로 'CARIBEAR' 의 실제 잉크 높이로 잰다 (어센더/디센더 무시).
    """
    size = int(cap_h / 0.7)
    for _ in range(24):
        f = ImageFont.truetype(path, size)
        box = f.getbbox(text)
        h = box[3] - box[1]
        if h == cap_h:
            break
        size += 1 if h < cap_h else -1
        if size < 8:
            break
    return ImageFont.truetype(path, size)


def draw_card(path):
    """레퍼런스와 같은 정지 카드 한 장. 90프레임 전부 같은 그림이다."""
    font_path = pick_font()
    font = fit_font(font_path, WORDMARK, CARD_CAP_H)
    track = int(round(font.size * CARD_TRACKING))

    widths = [font.getbbox(c)[2] - font.getbbox(c)[0] for c in WORDMARK]
    advances = [font.getlength(c) for c in WORDMARK]
    total = sum(advances) + track * (len(WORDMARK) - 1)

    img = Image.new('RGB', (W, H), CARD_BG)
    d = ImageDraw.Draw(img)
    # 잉크 상자 기준으로 정확히 가운데 — 글리프 베어링 때문에 anchor 만으로는 안 맞는다
    x = (W - total) / 2.0
    box = font.getbbox(WORDMARK)
    y = (H - CARD_CAP_H) / 2.0 - box[1]
    for i, c in enumerate(WORDMARK):
        d.text((x, y), c, font=font, fill=CARD_INK)
        x += advances[i] + track
    img.save(path)
    print('[reel] card: %s  font=%s size=%d' %
          (os.path.basename(path), os.path.basename(font_path), font.size))
    return img


def main():
    """인자 없이 = 전체 릴스(1..561 + 워드마크 카드).

        python tools/build_reel.py <프레임폴더> <프레임수> <출력mp4>

    로 부르면 그 구간만 카드 없이 묶는다. 5초 프리뷰용이다.
    """
    frames, count, out = FRAMES, TOTAL, OUT
    partial = len(sys.argv) > 1
    if partial:
        frames = os.path.abspath(sys.argv[1])
        count = int(sys.argv[2])
        out = os.path.abspath(sys.argv[3])

    have = sorted(glob.glob(os.path.join(frames, 'f*.png')))
    need = count if partial else LAST_3D
    if len(have) < need:
        raise SystemExit('3D 프레임이 모자란다: %d / %d. blender_reel.py 먼저 돌려라.'
                         % (len(have), need))

    if not partial:
        card = draw_card(os.path.join(frames, '_card.png'))
        for n in range(LAST_3D + 1, TOTAL + 1):
            card.save(os.path.join(frames, 'f%04d.png' % n))
        print('[reel] outro %d..%d 채움' % (LAST_3D + 1, TOTAL))

    cmd = [
        ffmpeg_exe(), '-y',
        '-framerate', str(FPS),
        '-start_number', '1',
        '-i', os.path.join(frames, 'f%04d.png'),
        '-frames:v', str(count),
        '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow',
        '-crf', '18', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        out,
    ]
    OUT_ACTUAL[0] = out
    print('[reel] encoding -> %s  (%d프레임 / %.2f초)' % (out, count, count / FPS))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        sys.stdout.write(r.stdout.decode('utf-8', 'replace')[-4000:])
        raise SystemExit('ffmpeg 실패 (%d)' % r.returncode)
    print('[reel] done: %s  %.1f MB'
          % (OUT_ACTUAL[0], os.path.getsize(OUT_ACTUAL[0]) / 1e6))


if __name__ == '__main__':
    main()
