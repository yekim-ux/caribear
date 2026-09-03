# -*- coding: utf-8 -*-
"""
턴테이블 PNG 시퀀스 -> 히어로용 투명 WebM (VP9 + 알파)

  입력 : <frames_dir>/f_0001.png ...   (blender_turntable.py --png-frames 결과)
  출력 : assets/video/bear-<color>-turntable.webm

  python tools/encode_turntable.py <frames_dir> --color blush

핵심 두 가지:

1. **모든 프레임을 같은 사각형으로 자른다.** optimize_shots.py 는 컷마다 알파
   바운딩박스를 재서 자르지만, 그걸 애니메이션에 하면 실루엣이 프레임마다 조금씩
   달라져 곰이 위아래로 떤다. 여기서는 전 프레임의 합집합 박스 하나로만 자른다.

2. **정지컷과 같은 세로 스케일을 맞춘다.** 히어로는 poster(정지 WebP)를 먼저 보여 주고
   영상이 로드되면 갈아탄다. 둘의 곰 크기가 다르면 갈아타는 순간 튄다.
   `assets/img/_render/bear-*.png` 의 합집합 높이를 기준으로 잡아 둔다.

ffmpeg 는 imageio_ffmpeg 에 들어 있는 것을 쓴다 (시스템에 ffmpeg 가 없어도 된다).
Blender 5.2 빌드에는 FFMPEG 출력이 빠져 있어서 Blender 로는 직접 못 뽑는다.
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
STILLS = os.path.join(ROOT, 'assets', 'img', '_render')
OUT_DIR = os.path.join(ROOT, 'assets', 'video')


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which('ffmpeg') or sys.exit('ffmpeg 를 못 찾았다.')


def union_box(paths):
    box = None
    for p in paths:
        bb = Image.open(p).convert('RGBA').getbbox()
        if bb is None:
            continue
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]),
                                      max(box[2], bb[2]), max(box[3], bb[3]))
    return box


def stills_height():
    """정지컷 파이프라인이 쓰는 공통 캔버스 높이 (optimize_shots.py 와 같은 계산)."""
    pngs = sorted(glob.glob(os.path.join(STILLS, 'bear-*.png')))
    if not pngs:
        return None
    return max(Image.open(p).convert('RGBA').getbbox()[3] -
               Image.open(p).convert('RGBA').getbbox()[1] for p in pngs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames_dir')
    ap.add_argument('--color', default='blush')
    ap.add_argument('--height', type=int, default=880, help='출력 세로 픽셀')
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--crf', type=int, default=36)
    a = ap.parse_args()

    frames = sorted(glob.glob(os.path.join(a.frames_dir, '*.png')))
    if not frames:
        sys.exit('프레임이 없다: ' + a.frames_dir)

    box = union_box(frames)
    cw, ch = box[2] - box[0], box[3] - box[1]
    sh = stills_height()
    print('프레임 %d장 · 합집합 박스 %dx%d · 정지컷 공통 높이 %s' % (len(frames), cw, ch, sh))
    if sh and abs(sh - ch) > 6:
        print('  ! 정지컷 높이와 %dpx 차이 — poster 에서 영상으로 갈아탈 때 튈 수 있다' % (sh - ch))

    scale = a.height / float(ch)
    w = int(round(cw * scale)) // 2 * 2          # VP9 는 짝수 폭을 원한다
    h = a.height // 2 * 2

    tmp = tempfile.mkdtemp(prefix='caribear_tt_')
    try:
        for i, p in enumerate(frames, 1):
            im = Image.open(p).convert('RGBA').crop(box).resize((w, h), Image.LANCZOS)
            im.save(os.path.join(tmp, 'f_%04d.png' % i))
        os.makedirs(OUT_DIR, exist_ok=True)
        dst = os.path.join(OUT_DIR, 'bear-%s-turntable.webm' % a.color)
        cmd = [ffmpeg_exe(), '-y', '-framerate', str(a.fps),
               '-i', os.path.join(tmp, 'f_%04d.png'),
               '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
               '-b:v', '0', '-crf', str(a.crf), '-row-mt', '1',
               '-g', str(a.fps * 2), '-an', dst]
        print('$', ' '.join(cmd[-14:]))
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print('%s  %dx%d  %.0f KB' % (os.path.relpath(dst, ROOT), w, h,
                                      os.path.getsize(dst) / 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
