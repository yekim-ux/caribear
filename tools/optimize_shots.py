# -*- coding: utf-8 -*-
"""
Blender 렌더 PNG -> 웹용 WebP

  입력 : assets/img/bear-*.png   (blender_render_bear.py 결과, 900x1710 RGBA, 장당 1.5MB)
  출력 : assets/img/bear-*.webp      큰 슬롯용 (히어로·대표컷·PDP 메인·저널)
         assets/img/sm/bear-*.webp   작은 슬롯용 (무드 칩·썸네일·카드·카트)
  원본 PNG 는 assets/img/_render/ 로 옮긴다. 다시 뽑고 싶으면 Blender 스크립트를 돌리면 된다.

투명 여백을 알파 바운딩박스로 잘라 내는 게 핵심이다. 렌더는 어느 각도로 돌려도
안 잘리게 넉넉히 잡아 두기 때문에 그대로 쓰면 곰이 작게 박혀 나온다.
잘라낸 뒤 모든 컷을 '가장 큰 컷' 기준의 같은 캔버스에 다시 앉혀서,
색·각도를 바꿔도 곰이 튀지 않게 한다.
"""
import io, os, shutil, sys
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
IMG = os.path.join(ROOT, 'assets', 'img')
SM = os.path.join(IMG, 'sm')
KEEP = os.path.join(IMG, '_render')

BIG_H = 1100     # 큰 슬롯: 히어로가 1x 에서 530px -> 레티나 2x 여유
SM_H = 420       # 작은 슬롯: 칩 126px, 썸네일 90px -> 넉넉
Q_BIG = 82
Q_SM = 80


def main():
    srcs = sorted(f for f in os.listdir(IMG)
                  if f.startswith('bear-') and f.endswith('.png'))
    if not srcs:
        print('assets/img/ 에 bear-*.png 가 없다. 먼저 Blender 렌더를 돌릴 것.')
        return
    os.makedirs(SM, exist_ok=True)
    os.makedirs(KEEP, exist_ok=True)

    # 1) 알파 바운딩박스를 전부 재서 공통 캔버스를 정한다
    boxes = {}
    for f in srcs:
        im = Image.open(os.path.join(IMG, f)).convert('RGBA')
        bb = im.getbbox()                       # 알파 0 인 여백 제외
        if bb is None:
            print('  ! 빈 이미지:', f)
            continue
        boxes[f] = bb
    cw = max(b[2] - b[0] for b in boxes.values())
    ch = max(b[3] - b[1] for b in boxes.values())
    print('공통 캔버스 %dx%d (컷 %d장)' % (cw, ch, len(boxes)))

    total_before = total_big = total_sm = 0
    for f, bb in boxes.items():
        path = os.path.join(IMG, f)
        total_before += os.path.getsize(path)
        im = Image.open(path).convert('RGBA').crop(bb)

        # 가운데(가로) · 바닥 맞춤(세로)으로 공통 캔버스에 앉힌다
        canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(im, ((cw - im.width) // 2, ch - im.height))

        stem = os.path.splitext(f)[0]
        for out_dir, h, q, acc in ((IMG, BIG_H, Q_BIG, 'big'), (SM, SM_H, Q_SM, 'sm')):
            s = h / float(ch)
            im2 = canvas.resize((max(1, round(cw * s)), h), Image.LANCZOS) if s < 1 else canvas
            dst = os.path.join(out_dir, stem + '.webp')
            im2.save(dst, 'WEBP', quality=q, method=6)
            n = os.path.getsize(dst)
            if acc == 'big':
                total_big += n
            else:
                total_sm += n

        shutil.move(path, os.path.join(KEEP, f))

    print('PNG  %5.1f MB' % (total_before / 1e6))
    print('WebP %5.1f MB (큰 컷) + %.1f MB (작은 컷)' % (total_big / 1e6, total_sm / 1e6))
    print('원본 PNG -> assets/img/_render/')


if __name__ == '__main__':
    main()
