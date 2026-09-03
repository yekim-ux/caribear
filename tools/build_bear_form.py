# -*- coding: utf-8 -*-
"""
CARIBEAR 웹용 곰 형태 — 제품 사진(7색 래티스 곰 정렬컷)의 실루엣을 그대로 구현한다.
→ assets/data/bear-form-shape.json

이 파일이 형태 정본이다. 형태를 바꾸려면 아래 PARTS 만 고치고 재실행한다.
JSON 이나 렌더러 좌표는 손대지 않는다.

사진에서 읽은 규정 (2026-09-01 지시: 각도는 바꿔도 되지만 형태는 변형 금지):
  - 귀   : 크고 납작한 잎 모양 2개. 머리 위쪽 옆에서 바깥·위로 35° 벌어진다.
  - 고리 : 정수리 중앙의 작은 링. 래티스가 아니라 꽉 찬 solid 로 읽혀야 한다.
  - 머리 : 둥근 덩어리. 얼굴 없음. 아래에 짧은 목이 있어 몸통과 잘록하게 갈린다.
  - 몸통 : 세로로 선 라운드 박스.
  - 팔   : 어깨에서 바깥·아래로 뻗는 로브. 몸통 실루엣 밖으로 나온다.
  - 발   : 바닥에 둥근 발 2개, 사이에 틈.
  - 비율 : 귀 끝 폭 : 전체 높이 = 1 : 1.75
  - 셀   : 사진의 보로노이 셀은 전체 높이의 4~5% 로 굵고 시원하게 뚫려 있다.

방식:
  1. 프리미티브 SDF 를 하드 min 으로 합친다 (스무스 min 을 쓰면 어깨·고관절
     크리즈가 뭉개져서 팔다리가 사라진다).
  2. 그리드에서 표면 근처 셀을 고르고, 격자 티가 남지 않도록 지터를 준 뒤
     뉴턴 스텝으로 표면에 붙인다.
  3. 포아송 디스크(블루 노이즈)로 솎아낸다. 격자 스냅으로 솎으면 스트럿이
     바둑판이 돼서 보로노이가 아니라 와이어프레임으로 보인다.
     고리만 훨씬 촘촘하게 따로 뽑아 solid 로 읽히게 한다.
  4. 노멀은 SDF 기울기.
"""
import io, json, math, os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'assets', 'data', 'bear-form-shape.json')
GRID_LONG = 210      # 최장축 그리드 해상도
BODY_PTS = 1250      # 몸체 포인트 수 — 사진처럼 셀이 크게 뚫리는 밀도
RING_R = 0.026       # 고리 포아송 반지름 (몸체보다 촘촘 → solid 로 보인다)


# ---------------------------------------------------------------- 프리미티브
def sd_ellipsoid(p, c, r):
    q = (p - c) / r
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / r, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_ellipsoid_rz(p, c, r, deg):
    """z축으로 deg 만큼 기울인 타원체 — 벌어진 귀"""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    d = p - c
    lx = d[:, 0] * ca + d[:, 1] * sa      # Rz(-a)
    ly = -d[:, 0] * sa + d[:, 1] * ca
    local = np.stack([lx, ly, d[:, 2]], axis=1)
    return sd_ellipsoid(local, np.zeros(3), r)


def sd_round_box(p, c, b, r):
    q = np.abs(p - c) - b
    outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
    inside = np.minimum(q.max(axis=1), 0.0)
    return outside + inside - r


def sd_capsule(p, a, b, r):
    pa = p - a
    ba = b - a
    h = np.clip((pa @ ba) / float(ba @ ba), 0.0, 1.0)[:, None]
    return np.linalg.norm(pa - ba * h, axis=1) - r


def sd_torus_z(p, c, R, r):
    """축이 z 인 토러스 — 정면에서 보이는 키링 고리"""
    l = p - c
    q0 = np.hypot(l[:, 0], l[:, 1]) - R
    return np.hypot(q0, l[:, 2]) - r


# ---------------------------------------------------------------- 형태 정의
A = np.array

RING = lambda p: sd_torus_z(p, A([0.0, 1.940, 0.0]), 0.145, 0.042)

PARTS = [
    # 발 2개 — 바닥에 둥근 발, 사이에 틈. 몸통보다 살짝 바깥으로 나온다
    ('foot_l', lambda p: sd_ellipsoid(p, A([-0.255, -0.340, 0.040]), A([0.225, 0.260, 0.250]))),
    ('foot_r', lambda p: sd_ellipsoid(p, A([ 0.255, -0.340, 0.040]), A([0.225, 0.260, 0.250]))),

    # 몸통 — 세로로 선 라운드 박스
    ('torso',  lambda p: sd_round_box(p, A([0.0, 0.420, 0.0]), A([0.200, 0.280, 0.170]), 0.220)),

    # 팔 2개 — 어깨에서 바깥·아래로. 몸통 밖으로 확실히 나와야 팔로 읽힌다
    ('arm_l',  lambda p: sd_capsule(p, A([-0.340, 0.800, 0.0]), A([-0.500, 0.200, 0.0]), 0.165)),
    ('arm_r',  lambda p: sd_capsule(p, A([ 0.340, 0.800, 0.0]), A([ 0.500, 0.200, 0.0]), 0.165)),

    # 목 — 머리와 몸통 사이 잘록함을 만든다
    ('neck',   lambda p: sd_capsule(p, A([0.0, 0.980, 0.0]), A([0.0, 1.140, 0.0]), 0.200)),

    # 머리 — 둥근 덩어리, 얼굴 없음
    ('head',   lambda p: sd_ellipsoid(p, A([0.0, 1.400, 0.0]), A([0.355, 0.400, 0.335]))),

    # 귀 2개 — 크고 납작한 잎 모양, 바깥·위로 32° 벌어져 머리 위로 솟는다
    ('ear_l',  lambda p: sd_ellipsoid_rz(p, A([-0.530, 1.720, 0.0]), A([0.235, 0.320, 0.105]),  32.0)),
    ('ear_r',  lambda p: sd_ellipsoid_rz(p, A([ 0.530, 1.720, 0.0]), A([0.235, 0.320, 0.105]), -32.0)),

    # 키링 고리 — 정수리 중앙
    ('ring',   RING),
]

BBOX_MIN = A([-0.86, -0.68, -0.52])
BBOX_MAX = A([ 0.86,  2.24,  0.52])


def sdf(p):
    """하드 min 합집합 — 접합부 크리즈를 남긴다"""
    out = None
    for _, f in PARTS:
        d = f(p)
        out = d if out is None else np.minimum(out, d)
    return out


def sdf_chunked(p, chunk=400000):
    if len(p) <= chunk:
        return sdf(p)
    return np.concatenate([sdf(p[i:i + chunk]) for i in range(0, len(p), chunk)])


def gradient(p, eps):
    g = np.empty_like(p)
    for ax in range(3):
        o = np.zeros(3)
        o[ax] = eps
        g[:, ax] = sdf_chunked(p + o) - sdf_chunked(p - o)
    n = np.linalg.norm(g, axis=1, keepdims=True)
    return g / np.maximum(n, 1e-9)


# ---------------------------------------------------------------- 1. 표면 후보
span = BBOX_MAX - BBOX_MIN
cell = span.max() / GRID_LONG
dims = np.maximum((span / cell).astype(int) + 1, 2)
print('grid', tuple(int(v) for v in dims), 'cell %.4f' % cell)

cands = []
for iy in range(dims[1]):                      # y 슬랩 단위로 돌려 메모리를 아낀다
    y = BBOX_MIN[1] + iy * cell
    gx = BBOX_MIN[0] + np.arange(dims[0]) * cell
    gz = BBOX_MIN[2] + np.arange(dims[2]) * cell
    X, Z = np.meshgrid(gx, gz, indexing='ij')
    slab = np.stack([X.ravel(), np.full(X.size, y), Z.ravel()], axis=1)
    d = sdf_chunked(slab)
    keep = np.abs(d) < cell * 1.1
    if keep.any():
        cands.append(slab[keep])

P = np.concatenate(cands, axis=0).astype(np.float64)
print('surface candidates', len(P))

# ---------------------------------------------------------------- 2. 표면에 붙이기
rng = np.random.default_rng(20260901)
P += rng.uniform(-0.7, 0.7, P.shape) * cell     # 격자 정렬을 깬다

for _ in range(4):
    d = sdf_chunked(P)
    P -= gradient(P, cell * 0.25) * d[:, None]

resid = np.abs(sdf_chunked(P))
P = P[resid < cell * 0.12]
print('projected', len(P), 'max resid %.5f' % np.abs(sdf_chunked(P)).max())


# ---------------------------------------------------------------- 3. 포아송 디스크
def poisson(pts, rad, order):
    """반지름 rad 안에 이웃이 없을 때만 채택 — 블루 노이즈"""
    inv = 1.0 / rad
    grid = {}
    keep = []
    r2 = rad * rad
    for i in order:
        x, y, z = pts[i]
        gx, gy, gz = int(x * inv), int(y * inv), int(z * inv)
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((gx + dx, gy + dy, gz + dz), ()):
                        px, py, pz = pts[j]
                        if (px - x) ** 2 + (py - y) ** 2 + (pz - z) ** 2 < r2:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            grid.setdefault((gx, gy, gz), []).append(i)
            keep.append(i)
    return keep


# 고리 표면 위의 점과 몸체를 갈라 밀도를 따로 준다
on_ring = np.abs(RING(P)) < cell * 0.6
BODY, RINGP = P[~on_ring], P[on_ring]
print('body cands', len(BODY), '/ ring cands', len(RINGP))

order = rng.permutation(len(BODY))
lo, hi, best = cell * 1.0, cell * 30.0, None
for _ in range(12):
    mid = (lo + hi) * 0.5
    got = poisson(BODY, mid, order)
    if len(got) > BODY_PTS:
        lo = mid
    else:
        hi = mid
        best = got
    if best is not None and abs(len(best) - BODY_PTS) < BODY_PTS * 0.03:
        break
body = BODY[best if best is not None else poisson(BODY, hi, order)]
print('body pts', len(body), '(spacing ~%.3f)' % hi)

ring = RINGP[poisson(RINGP, RING_R, rng.permutation(len(RINGP)))]
print('ring pts', len(ring))

S = np.concatenate([body, ring], axis=0)

# ---------------------------------------------------------------- 4. 노멀 · 저장
N = gradient(S, cell * 0.25)

# x·z 중심 정렬 (y 는 그대로 두고 bounds 로 넘긴다)
S[:, 0] -= (S[:, 0].max() + S[:, 0].min()) * 0.5
S[:, 2] -= (S[:, 2].max() + S[:, 2].min()) * 0.5

minY, maxY = float(S[:, 1].min()), float(S[:, 1].max())
w = float(S[:, 0].max() - S[:, 0].min())
print('bounds y %.3f..%.3f  width %.3f  ratio 1:%.2f' % (minY, maxY, w, (maxY - minY) / w))

data = {
    'note': '제품 사진(7색 정렬컷) 실루엣 기준 절차 생성 — tools/build_bear_form.py. 형태 변경은 이 스크립트의 PARTS 에서만.',
    'bounds': {'minY': round(minY, 4), 'maxY': round(maxY, 4)},
    'p': [round(float(v), 4) for v in S.ravel()],
    'n': [round(float(v), 4) for v in N.ravel()],
}
out = os.path.normpath(OUT)
with io.open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
print('wrote', os.path.basename(out), os.path.getsize(out) // 1024, 'KB', len(S), 'pts')
