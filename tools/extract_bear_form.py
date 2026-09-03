# -*- coding: utf-8 -*-
"""
곰돌이키링_테스트출력.obj (460MB · 5M verts · 실제 래티스 출력물)
→ 웹에서 쓸 '형태'(외곽 솔리드)만 뽑아 포인트 클라우드 JSON으로.

핵심: 래티스는 구멍투성이라 고해상도 복셀로는 속이 뚫린다.
셀 크기보다 큰 굵은 복셀(≈2mm)로 점유를 잡으면 래티스가 자연스럽게
하나의 솔리드로 합쳐진다. 그 다음 부드럽게 업샘플해서 표면을 뽑는다.
"""
import io, json, os, sys
import numpy as np

SRC = r"C:\Users\carima\Desktop\작업\ETC\곰돌이 키링\곰돌이키링_테스트출력.obj"
OUT = r"C:\Users\carima\Desktop\작업\클로드\웹사이트\assets\data\bear-form.json"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verts.npy')  # 정점 캐시(약 60MB, 재실행 가속용)

GRID = 120        # 복셀 그리드 (최장축) — 0.69mm
BALL = 4          # 롤링볼 반경(복셀) ≈ 2.8mm. 래티스 구멍보다 크고 귀·고리 틈보다 작다
UP = 2            # 업샘플 배율
TARGET_PTS = 3400 # 최종 포인트 수


def load_vertices(path):
    chunks, buf, n = [], [], 0
    with io.open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line[0] != 'v' or line[1] != ' ':
                continue
            buf.append(line[2:])
            n += 1
            if n % 500000 == 0:
                chunks.append(np.array(''.join(buf).split(), dtype=np.float32).reshape(-1, 3))
                buf = []
    if buf:
        chunks.append(np.array(''.join(buf).split(), dtype=np.float32).reshape(-1, 3))
    return np.concatenate(chunks, axis=0)


if os.path.exists(CACHE):
    V = np.load(CACHE)
else:
    print('reading obj...')
    V = load_vertices(SRC)
    np.save(CACHE, V)
print('vertices:', V.shape)

ext = V.max(0) - V.min(0)
order = np.argsort(-ext)
ax_y, ax_x, ax_z = order[0], order[1], order[2]
print('bbox', ext, 'height=%d width=%d depth=%d' % (ax_y, ax_x, ax_z))
P = np.stack([V[:, ax_x], V[:, ax_y], V[:, ax_z]], axis=1)
del V

lo = P.min(0)
ext = P.max(0) - lo
vsize = ext.max() / GRID
PAD = BALL + 3
dims = np.ceil(ext / vsize).astype(int) + 2 * PAD + 1
idx = np.floor((P - lo) / vsize).astype(np.int32) + PAD
occ = np.zeros(dims, dtype=bool)
occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True
print('grid', dims, 'voxel %.2fmm  ball %.1fmm' % (vsize, BALL * vsize))
del P, idx


def dilate(a):
    out = a.copy()
    for ax in (0, 1, 2):
        out |= np.roll(a, 1, axis=ax)
        out |= np.roll(a, -1, axis=ax)
    return out


def erode(a):
    out = a.copy()
    for ax in (0, 1, 2):
        out &= np.roll(a, 1, axis=ax)
        out &= np.roll(a, -1, axis=ax)
    return out


# ---------- 롤링볼 외곽 추출 ----------
# 래티스는 구멍투성이라 단순 플러드필은 속으로 새어 들어간다.
# 반지름 BALL 의 공이 굴러 들어갈 수 있는 빈 공간만 '바깥'으로 친다.
# 래티스 셀(작음)에는 못 들어가고, 귀 사이·고리 구멍(큼)에는 들어간다.
free = ~occ
probe = free
for _ in range(BALL):
    probe = erode(probe)

outside = np.zeros_like(probe)
outside[0] = outside[-1] = True
outside[:, 0] = outside[:, -1] = True
outside[:, :, 0] = outside[:, :, -1] = True
outside &= probe
while True:
    grown = dilate(outside) & probe
    if grown.sum() == outside.sum():
        break
    outside = grown
for _ in range(BALL):
    outside = dilate(outside)
outside &= free
solid = ~outside
print('solid %.1f%% of bbox' % (100 * solid.mean()))

# ---------- 업샘플 + 스무딩 → 매끈한 표면 ----------
f = solid.astype(np.float32)
f = np.repeat(np.repeat(np.repeat(f, UP, 0), UP, 1), UP, 2)
for _ in range(2):
    acc = f * 2.0
    for ax in (0, 1, 2):
        acc += np.roll(f, 1, axis=ax) + np.roll(f, -1, axis=ax)
    f = acc / 8.0

ISO = 0.5
inside = f >= ISO
shell = inside & ~(
    np.roll(inside, 1, 0) & np.roll(inside, -1, 0) &
    np.roll(inside, 1, 1) & np.roll(inside, -1, 1) &
    np.roll(inside, 1, 2) & np.roll(inside, -1, 2)
)
sx, sy, sz = np.nonzero(shell)
print('surface voxels:', len(sx))

gx, gy, gz = np.gradient(f)
nrm = -np.stack([gx[sx, sy, sz], gy[sx, sy, sz], gz[sx, sy, sz]], axis=1)
ln = np.linalg.norm(nrm, axis=1, keepdims=True)
ln[ln == 0] = 1
nrm /= ln
pts = np.stack([sx, sy, sz], axis=1).astype(np.float32)

# ---------- 균등 다운샘플 ----------
rng = np.random.default_rng(11)
perm = rng.permutation(len(pts))
pts, nrm = pts[perm], nrm[perm]
cell = 1.0
for _ in range(24):                       # 목표 개수에 맞는 최소간격을 이분 탐색
    seen, keep = set(), []
    for i, p in enumerate(pts):
        k = (int(p[0] / cell), int(p[1] / cell), int(p[2] / cell))
        if k in seen:
            continue
        seen.add(k)
        keep.append(i)
    if len(keep) <= TARGET_PTS * 1.08:
        break
    cell *= 1.08
pts, nrm = pts[keep], nrm[keep]
print('final points: %d (cell %.2f)' % (len(pts), cell))

# ---------- 정규화: y 위쪽 +, 높이 2.59, 바닥 y=-0.68 ----------
mn, mx = pts.min(0), pts.max(0)
scale = 2.59 / (mx[1] - mn[1])
c = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2], dtype=np.float32)
q = (pts - c) * scale
q[:, 1] -= 0.68

# 고리 쪽이 위로 오도록 정렬 — 고리 끝단은 단면이 아주 작다
ylo, yhi = q[:, 1].min(), q[:, 1].max()
band = (yhi - ylo) * 0.05
n_hi = int(((q[:, 1] > yhi - band)).sum())
n_lo = int(((q[:, 1] < ylo + band)).sum())
print('end slice counts  top=%d bottom=%d' % (n_hi, n_lo))
if n_hi > n_lo:
    q[:, 1] = (yhi + ylo) - q[:, 1]
    nrm[:, 1] *= -1
    print('flipped vertically')

data = {
    'note': 'from 곰돌이키링_테스트출력.obj — 실측 형태',
    'bounds': {'minY': float(q[:, 1].min()), 'maxY': float(q[:, 1].max())},
    'p': [round(float(v), 4) for v in q.reshape(-1)],
    'n': [round(float(v), 3) for v in nrm.reshape(-1)],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False))
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')

# ---------- ASCII 미리보기 ----------
W, H = 44, 44
mnx, mxx = q[:, 0].min(), q[:, 0].max()
mny, mxy = q[:, 1].min(), q[:, 1].max()
g = np.zeros((H, W), int)
ix = ((q[:, 0] - mnx) / (mxx - mnx) * (W - 1)).astype(int)
iy = ((mxy - q[:, 1]) / (mxy - mny) * (H - 1)).astype(int)
np.add.at(g, (iy, ix), 1)
ch = ' .:-=+*#%@'
for r in g:
    print(''.join(ch[min(len(ch) - 1, v)] for v in r))
