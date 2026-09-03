# -*- coding: utf-8 -*-
"""
CARIBEAR 릴스 — ANDAASH "in love" 릴스(C6s8L5opEFu)의 구조를 그대로 두고
에어팟 + 크롬 리본 자리에 곰돌이 키링을 넣는다.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/blender_reel.py -- \
        --obj "C:/Users/carima/Desktop/작업/ETC/곰돌이 키링/곰돌이키링.obj" \
        --out assets/video/_reel --res 720 --samples 48

레퍼런스에서 계측한 값 (원본 mp4 를 프레임 단위로 뜯어서 얻음):
    720x1280 · 30fps · 651프레임 · 21.70초
    컷: f90 / f180 / f270 / f380 / f561  -> 6샷
    배경: 위아래 라벤더핑크(#E4C9E1), 가운데 흰기(#EAE5E7) — 세로 그라디언트
    6샷(f562-651)은 흰 배경 + 워드마크. 그건 Blender 가 아니라 build_reel.py 가 만든다.

여기서는 1..561 (샷 1-5) 만 PNG 시퀀스로 뽑는다.

원칙:
  - 형태는 손대지 않는다. 균등 배율과 회전만. (LANDING_KIT.md 9)
  - 정지컷과 달리 카메라는 퍼스펙티브다. 레퍼런스가 퍼스펙티브 + 얕은 심도이고,
    이건 제품 비교컷이 아니라 무드 영상이라 '모든 컷이 같은 카메라' 규칙을 안 받는다.
  - 곰은 전부 파스텔 무광 레진이다. 크롬은 쓰지 않는다 (2026-09-02 지시).
  - 모델은 래티스 출력물 원본(곰돌이키링_테스트출력.obj, 5M verts)을 그대로 쓴다.
    형태를 다시 만들거나 단순화하지 않는다.
  - **형태 변형 금지 규칙의 예외**: 제품의 특징이 '유연함'이라 사용자가 이를
    영상에 넣으라고 명시했다. 3-4샷에서 스쿼시와 벤드를 준다. 이건 제품 비교컷이
    아니라 물성 시연이다. 정지 제품컷(blender_render_bear.py)에는 옮기지 말 것.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

R = math.radians

# 사이트 정본 8색 (tools/blender_render_bear.py PRODUCT 와 같아야 한다)
PRODUCT = {
    'blush':  (0xFF, 0xC2, 0xCE),
    'peach':  (0xFF, 0xC4, 0x9B),
    'butter': (0xFF, 0xE4, 0x9A),
    'mint':   (0xA9, 0xE0, 0xC8),
    'sky':    (0xA9, 0xD2, 0xF2),
    'lilac':  (0xCB, 0xBC, 0xF0),
    'rose':   (0xF5, 0x8B, 0xA5),
    'milk':   (0xF2, 0xEC, 0xEA),
}

# 레퍼런스 배경 실측
BG_EDGE = (0xE4, 0xC9, 0xE1)
BG_MID = (0xEA, 0xE5, 0xE7)

# 원본과 같은 컷 자리 (start, end)
CUTS = [(1, 90), (91, 180), (181, 270), (271, 380), (381, 561)]


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb, a=1.0):
    return tuple([srgb_to_linear(c) for c in rgb] + [a])


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--obj', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--res', type=int, default=720)
    p.add_argument('--samples', type=int, default=48)
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--end', type=int, default=561)
    p.add_argument('--no-flip', dest='flip', action='store_false', default=True)
    p.add_argument('--motion-blur', dest='mblur', action='store_true',
                   help='켜면 프레임당 렌더가 약 1.7배 느려진다 (래티스 기준).')
    p.add_argument('--frames', default='',
                   help='쉼표로 찍은 프레임만 렌더한다. 룩 확인용.')
    return p.parse_args(argv)


# ---------------------------------------------------------------- 곰 원본

def import_bear(path):
    print('[reel] importing', path)
    bpy.ops.wm.obj_import(filepath=path, forward_axis='NEGATIVE_Z', up_axis='Y')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        raise SystemExit('메시를 못 읽었다: ' + path)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def normalize(ob, flip):
    """가장 긴 축을 +Z 로 세우고 원점 중심 · 높이 2.0. 균등 배율·직각 회전만."""
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    dims = list(ob.dimensions)
    up = dims.index(max(dims))
    if up == 0:
        ob.rotation_euler = (0, 0, R(90))
        bpy.ops.object.transform_apply(rotation=True)
        ob.rotation_euler = (0, R(-90), 0)
        bpy.ops.object.transform_apply(rotation=True)
    elif up == 1:
        ob.rotation_euler = (R(90), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)

    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    ob.location -= (lo + hi) / 2.0
    bpy.ops.object.transform_apply(location=True)
    s = 2.0 / max(1e-9, (hi - lo).z)
    ob.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    if flip:
        ob.rotation_euler = (R(180), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
    bpy.ops.object.shade_smooth()
    ob.name = 'bear_master'
    return ob


# ---------------------------------------------------------------- 재질

def _bsdf(mat):
    return mat.node_tree.nodes['Principled BSDF']


def mat_resin(name, rgb):
    """파스텔 무광 레진. 광택 코트는 넣지 않는다 — 무광이 지시사항이다.

    래티스 셀 벽이 얇아서 빛이 조금 투과한다. 서브서피스를 살짝 넣어야
    3D 프린트 레진 특유의 '속이 비치는' 느낌이 나고, 안 넣으면 석고처럼 죽는다.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    b.inputs['Base Color'].default_value = lin(rgb)
    b.inputs['Roughness'].default_value = 0.62
    b.inputs['Metallic'].default_value = 0.0
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = 0.38
    if 'Subsurface Weight' in b.inputs:
        b.inputs['Subsurface Weight'].default_value = 0.18
        if 'Subsurface Scale' in b.inputs:
            b.inputs['Subsurface Scale'].default_value = 0.14
        if 'Subsurface Radius' in b.inputs:
            b.inputs['Subsurface Radius'].default_value = (1.0, 0.72, 0.68)
    return m


def mat_organza(name='organza'):
    """레퍼런스의 시스루 핑크 리본. EEVEE 라 투과 대신 알파 블렌드로 간다."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    if hasattr(m, 'blend_method'):
        m.blend_method = 'BLEND'
    if hasattr(m, 'show_transparent_back'):
        m.show_transparent_back = False
    if hasattr(m, 'use_backface_culling'):
        m.use_backface_culling = False
    b = _bsdf(m)
    b.inputs['Base Color'].default_value = lin((0xF2, 0xB6, 0xBE))
    b.inputs['Roughness'].default_value = 0.14
    b.inputs['Alpha'].default_value = 0.40
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = 0.6
    return m


def mat_pool():
    """5샷 진주빛 웅덩이. 물결은 지오메트리가 아니라 노멀로 만든다."""
    m = bpy.data.materials.new('pool')
    m.use_nodes = True
    nt = m.node_tree
    b = _bsdf(m)
    b.inputs['Base Color'].default_value = lin((0xDE, 0xD0, 0xDA))
    b.inputs['Roughness'].default_value = 0.30
    b.inputs['Metallic'].default_value = 0.0

    coord = nt.nodes.new('ShaderNodeTexCoord')
    coord.location = (-1000, -200)

    tex = nt.nodes.new('ShaderNodeTexWave')
    tex.wave_type = 'RINGS'
    tex.rings_direction = 'SPHERICAL'
    tex.inputs['Scale'].default_value = 0.65      # Object 좌표 = 월드 유닛
    tex.inputs['Distortion'].default_value = 2.6
    tex.inputs['Detail'].default_value = 2.0
    tex.location = (-700, -200)

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55
    bump.inputs['Distance'].default_value = 0.10
    bump.location = (-350, -200)

    nt.links.new(coord.outputs['Object'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m, tex


# ---------------------------------------------------------------- 배경 / 조명

def build_backdrop(cam, f0, f1):
    """레퍼런스 실측 그라디언트. 카메라에 물려서 어떤 무빙에도 화면을 채운다.

    크롬 곰이 반사하는 것도 이 판이다 — 그래서 월드 색이 아니라 발광 판이다.
    카메라마다 한 장씩 달리므로 자기 샷 밖에서는 반드시 꺼야 한다.
    안 그러면 다른 샷의 배경판이 화면 안에 판때기로 떠 있다.
    """
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    bd = bpy.context.object
    bd.name = 'backdrop_' + cam.name
    bd.parent = cam
    bd.location = (0, 0, -46.0)      # 카메라 로컬 -Z = 정면
    bd.rotation_euler = (0, 0, 0)
    bd.scale = (86, 150, 1)          # 9:16 보다 넉넉하게
    if hasattr(bd, 'visible_shadow'):
        bd.visible_shadow = False

    m = bpy.data.materials.new('bg')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]

    emis = nt.nodes.new('ShaderNodeEmission')
    emis.location = (-200, 0)
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-520, 0)
    coord = nt.nodes.new('ShaderNodeTexCoord')
    coord.location = (-1000, 0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-820, 0)

    e = ramp.color_ramp
    e.elements[0].position = 0.0
    e.elements[0].color = lin(BG_EDGE)
    e.elements[1].position = 1.0
    e.elements[1].color = lin(BG_EDGE)
    half = mix(BG_EDGE, BG_MID, 0.5)
    for pos, rgb in ((0.32, half), (0.50, BG_MID), (0.68, half)):
        el = e.elements.new(pos)
        el.color = lin(rgb)

    nt.links.new(coord.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Y'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], emis.inputs['Color'])
    nt.links.new(emis.outputs['Emission'], out.inputs['Surface'])
    bd.data.materials.append(m)

    # 자기 샷에서만 보이게. 불리언이라 보간은 CONSTANT 여야 한다.
    prev = bpy.context.preferences.edit.keyframe_new_interpolation_type
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
    try:
        for f, hidden in ((f0 - 1, True), (f0, False), (f1 + 1, True)):
            bd.hide_render = hidden
            bd.keyframe_insert('hide_render', frame=max(1, f))
    finally:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = prev
    return bd


def build_world():
    """크롬이 비출 환경. 이게 이 영상의 핵심이다.

    처음엔 단색 월드였는데 거울 곰이 균일한 흰 들판만 비춰서 무광 플라스틱처럼
    나왔다. 크롬의 '형태'는 조명이 아니라 반사되는 환경의 명암 단차가 만든다.
    그래서 실제 스튜디오처럼 아래는 어둡고, 눈높이에 밝은 소프트박스 띠를 두고,
    위는 부드럽게 떨어지는 세로 그라디언트를 넣는다.

    배경으로는 보이지 않는다 — 카메라에 물린 backdrop 판이 앞을 가리기 때문이다.
    이 월드는 오로지 반사와 앰비언트용이다.
    """
    w = bpy.data.worlds.new('w')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = 0.85

    coord = nt.nodes.new('ShaderNodeTexCoord')
    coord.location = (-900, 0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-700, 0)
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-480, 0)

    # 크롬일 때는 반사에 형태를 만들려고 어두운 바닥을 뒀지만, 무광 레진은
    # 반사가 아니라 확산광으로 읽힌다. 바닥이 어두우면 파스텔 아랫면이 탁해진다.
    # 그래서 전체적으로 밝게 올리고 위쪽에만 완만한 소프트박스를 남긴다.
    e = ramp.color_ramp
    e.elements[0].position = 0.0
    e.elements[0].color = lin((0xC4, 0xBA, 0xC6))     # 바닥 — 파스텔이 탁해지지 않게
    e.elements[1].position = 1.0
    e.elements[1].color = lin((0xE8, 0xE2, 0xE8))     # 천장
    for pos, rgb in ((0.40, (0xDA, 0xD2, 0xDC)),
                     (0.55, (0xFA, 0xF6, 0xFA)),
                     (0.66, (0xFF, 0xFA, 0xF6)),      # 살구빛이 살짝 도는 상단광
                     (0.82, (0xF0, 0xEA, 0xF0))):
        e.elements.new(pos).color = lin(rgb)

    nt.links.new(coord.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])


def area_light(name, loc, rot, size, energy, color=(1, 1, 1), specular=1.0):
    """specular 는 이 램프가 '거울에 비치는 정도'다.

    크롬 곰은 램프 판을 그대로 반사한다. 300W 짜리 6m 판이 거울에 찍히면
    그 자리가 통째로 순백으로 날아가고(2샷에서 화면의 24%), 몸통은 상대적으로
    건메탈처럼 어두워진다. 램프는 파스텔 곰을 밝히는 확산광만 담당하게 두고,
    크롬의 형태는 월드 그라디언트가 만들도록 스페큘러를 죽인다.
    """
    d = bpy.data.lights.new(name, type='AREA')
    d.size, d.energy, d.color = size, energy, color
    if hasattr(d, 'specular_factor'):
        d.specular_factor = specular
    o = bpy.data.objects.new(name, d)
    o.location, o.rotation_euler = loc, rot
    bpy.context.scene.collection.objects.link(o)
    return o


def build_lights():
    """정지컷의 밝은 배경용 정본 그대로다: key 380 / fill 240 / rim 190 / under 110.

    처음에 '영상이니까 세게'라고 키를 900 까지 올렸다가 전부 순백으로 날아갔다.
    배경이 #EAE5E7 로 이미 밝아서 여기서 더 올릴 여지가 없다.
    """
    # 크롬일 때는 램프가 거울에 찍혀 타는 걸 막으려고 스페큘러를 0.1 로 죽였다.
    # 무광 레진은 램프 판을 반사하지 않으므로 그 억제를 풀어도 된다.
    area_light('key', (-3.0, -4.2, 4.0), (R(48), 0, R(-36)), 5.0, 340)
    area_light('fill', (4.0, -3.0, 1.0), (R(80), 0, R(54)), 6.0, 210)
    # back — 래티스 구멍으로 빛이 새어 나오게 하는 램프. 이 영상의 주인공이다.
    # 좁고(size 2.6) 세게(720) 때려야 셀 벽 사이가 갈라져 보인다. 넓게 퍼뜨리면
    # 그냥 밝은 뒷면이 되고 구멍은 안 보인다.
    area_light('back', (0.0, 5.2, 1.4), (R(96), 0, 0), 2.6, 430,
               color=(1.0, 0.95, 0.97))
    area_light('rim', (1.6, 3.8, 3.4), (R(126), 0, R(22)), 4.0, 190,
               color=(1.0, 0.94, 0.96))
    area_light('under', (0.0, -2.0, -3.2), (R(-40), 0, 0), 5.0, 120,
               color=(1.0, 0.94, 0.97))
    area_light('kick', (-4.4, 1.2, 0.4), (R(90), 0, R(-104)), 5.0, 170,
               color=(1.0, 0.96, 0.99))


# ---------------------------------------------------------------- 유틸

def key(ob, path, pairs, index=-1):
    """[(frame, value), ...] 를 그대로 꽂는다."""
    for f, v in pairs:
        setattr(ob, path, v)
        ob.keyframe_insert(path, frame=f, index=index)


def add_bear(master, name, mat, loc, rot, scale):
    """메시는 공유하고 재질만 오브젝트에 붙인다 — 폴리를 복제하지 않기 위해서.

    OBJ 에 .mtl 이 없어서 임포트 결과에 머티리얼 슬롯이 아예 없다. 슬롯이 없으면
    오브젝트 링크 재질을 꽂을 자리가 없어서 전부 블렌더 기본 회색으로 렌더된다
    (크롬도 파스텔도 다 흰 플라스틱으로 나왔던 원인). 그래서 마스터 메시에
    빈 슬롯을 하나 만들어 두고, 인스턴스마다 그 슬롯을 OBJECT 로 바꿔 쓴다.
    """
    ob = bpy.data.objects.new(name, master.data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = (scale, scale, scale)
    if not ob.material_slots:
        raise RuntimeError('마스터 메시에 머티리얼 슬롯이 없다 — ensure_slot() 확인')
    ob.material_slots[0].link = 'OBJECT'
    ob.material_slots[0].material = mat
    return ob


def ensure_slot(master):
    """마스터 메시에 슬롯 한 칸을 보장한다. 인스턴스가 재질을 얹을 자리."""
    if not master.data.materials:
        master.data.materials.append(bpy.data.materials.new('slot_placeholder'))
    print('[reel] material slots on master: %d' % len(master.data.materials))


def add_flex(ob):
    """유연함 시연 — 3샷 스쿼시, 4샷 벤드.

    제품의 특징이 '휘어진다'는 것이라 사용자가 영상에 넣으라고 지시했다.
    정지 제품컷의 '형태 변형 금지'(균등 배율·회전만) 규칙에 대한 명시적 예외다.
    1-2샷에서는 중립을 키로 못 박아 둔다 — 제품의 원래 형태를 먼저 보여 준 뒤에
    휘어야 시연으로 읽히고, 아니면 그냥 모델이 이상한 걸로 보인다.

    스쿼시는 비균등 배율, 벤드는 SimpleDeform 이다. 둘 다 5M verts 를 프레임마다
    다시 계산하므로 렌더 시간에 그대로 얹힌다.
    """
    # 스쿼시 & 스트레치 (3샷). 부피 보존처럼 보이게 xy 와 z 를 반대로 준다.
    key(ob, 'scale', [
        (1,   (1.00, 1.00, 1.00)),
        (180, (1.00, 1.00, 1.00)),
        (205, (1.075, 1.075, 0.855)),   # 눌림
        (227, (0.965, 0.965, 1.070)),   # 되튀며 늘어남
        (248, (1.012, 1.012, 0.984)),
        (270, (1.00, 1.00, 1.00)),
        (380, (1.00, 1.00, 1.00)),
    ])

    # 벤드 (4샷)
    md = ob.modifiers.new('flex_bend', 'SIMPLE_DEFORM')
    md.deform_method = 'BEND'
    md.deform_axis = 'X'
    md.angle = 0.0
    for f, deg in ((1, 0), (271, 0), (302, 27), (332, -15), (360, 6), (380, 0)):
        md.angle = R(deg)
        md.keyframe_insert('angle', frame=f)
    return ob


def add_empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def add_camera(name, lens, fstop, focus_ob, target):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.dof.use_dof = True
    d.dof.focus_object = focus_ob
    d.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(cam)
    c = cam.constraints.new('TRACK_TO')
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    return cam


def bind(frame, cam):
    mk = bpy.context.scene.timeline_markers.new('cut%d' % frame, frame=frame)
    mk.camera = cam


def ribbon(name, points, width, mat, tilt_step=22.0):
    """베지어 곡선 + extrude = 납작한 띠. 컨트롤 포인트 tilt 로 비튼다."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = 16
    cu.extrude = width          # 곡선 로컬 Z 로 양쪽 extrude -> 폭 2*width
    cu.bevel_depth = 0.0
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = sp.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.tilt = R(tilt_step * i)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat)
    return ob


# ---------------------------------------------------------------- 무대

STAGE_B_X = 100.0   # 5샷(웅덩이)은 1-4샷과 애니메이션이 섞이지 않게 옆으로 떼어 놓는다


def build_stage_a(master, mats):
    """1-4샷: 히어로 크롬 곰 + 파스텔 위성 + 리본 두 장."""
    hero = add_bear(master, 'hero', mats['blush'], (0, 0, 0), (0, 0, R(-25)), 1.0)
    key(hero, 'rotation_euler', [
        (1,   (R(4), R(-6), R(-25))),
        (180, (R(-2), R(3), R(6))),
        (380, (R(3), R(-4), R(38))),
    ])
    add_flex(hero)

    # (이름, 색, 시작위치, 끝위치, 배율)  y 가 클수록 카메라에서 멀다 = 보케
    sats = [
        ('s1', 'rose',   (-2.10,  2.2,  1.75), (-2.45,  2.0,  1.40), 0.42),
        ('s2', 'lilac',  ( 2.35,  2.9,  1.15), ( 2.00,  3.1,  0.80), 0.38),
        ('s3', 'mint',   ( 1.75,  1.5, -1.70), ( 2.10,  1.7, -1.35), 0.32),
        ('s4', 'peach',  (-2.55,  3.6, -1.30), (-2.20,  3.5, -0.95), 0.46),
        ('s5', 'sky',    ( 2.95,  4.3,  2.35), ( 2.60,  4.1,  2.00), 0.52),
        ('s6', 'milk',   (-1.30,  4.9, -2.35), (-0.95,  5.1, -2.00), 0.50),
        ('s7', 'butter', ( 0.55,  5.8,  2.60), ( 0.20,  5.6,  2.30), 0.56),
    ]
    for i, (nm, color, a, b, sc) in enumerate(sats):
        ob = add_bear(master, nm, mats[color], a, (0, 0, 0), sc)
        key(ob, 'location', [(1, a), (380, b)])
        key(ob, 'rotation_euler', [
            (1,   (R(6 * i), R(-10 + 4 * i), R(-40 + 22 * i))),
            (380, (R(6 * i - 8), R(2 + 4 * i), R(20 + 22 * i))),
        ])

    # 리본 A — 1-2샷에서 곰 뒤를 훑고 지나간다
    ra = ribbon('ribbon_a', [
        (-7.0, 1.2, -2.4), (-2.6, 0.4, -0.6), (0.8, 1.8, 1.1),
        (4.2, 0.6, -0.4), (7.6, 1.6, 1.8),
    ], width=0.30, mat=mats['organza'], tilt_step=54.0)
    key(ra, 'location', [(1, (-3.4, 0.0, -0.9)), (380, (3.6, -0.4, 1.4))])
    key(ra, 'rotation_euler', [(1, (R(-14), R(4), R(8))), (380, (R(10), R(-8), R(-14)))])

    # 리본 B — 3샷 끝에서 화면을 덮었다가 4샷에서 걷힌다
    rb = ribbon('ribbon_b', [
        (-6.4, -2.0, 2.2), (-2.0, -2.6, -0.4), (1.6, -2.2, 1.6),
        (5.4, -2.8, -1.2), (8.8, -2.2, 1.0),
    ], width=0.46, mat=mats['organza'], tilt_step=68.0)
    key(rb, 'location', [
        (1,   (-9.5, -0.6, 0.4)),
        (181, (-6.6, -1.0, 0.2)),
        (270, (-1.2, -1.8, 0.3)),
        (300, ( 0.9, -2.0, 0.4)),
        (380, ( 6.8, -1.2, 0.9)),
    ])
    key(rb, 'rotation_euler', [
        (1,   (R(6), R(-2), R(4))),
        (270, (R(-10), R(6), R(-6))),
        (380, (R(-24), R(14), R(-18))),
    ])
    return hero


def build_stage_b(master, mats):
    """5샷: 진주빛 웅덩이 위에 뜬 곰 + 위쪽에 작은 곰 하나."""
    X = STAGE_B_X
    pool_mat, wave = mat_pool()
    bpy.ops.mesh.primitive_plane_add(size=60.0, location=(X, 6.0, -2.30))
    pool = bpy.context.object
    pool.name = 'pool'
    pool.data.materials.append(pool_mat)

    # 물결은 위상만 흐른다 — 지오메트리를 흔들면 곰 발밑이 어긋난다
    wave.inputs['Phase Offset'].default_value = 0.0
    wave.inputs['Phase Offset'].keyframe_insert('default_value', frame=381)
    wave.inputs['Phase Offset'].default_value = 5.4
    wave.inputs['Phase Offset'].keyframe_insert('default_value', frame=561)

    hero = add_bear(master, 'hero_b', mats['lilac'], (X, 0, -1.28), (0, 0, R(-8)), 1.0)
    key(hero, 'location', [
        (381, (X, 0.0, -1.34)),
        (470, (X, 0.0, -1.20)),
        (561, (X, 0.0, -1.30)),
    ])
    key(hero, 'rotation_euler', [
        (381, (R(2), R(-5), R(-14))),
        (561, (R(-1), R(4), R(16))),
    ])

    small = add_bear(master, 'small_b', mats['butter'],
                     (X + 1.35, 1.9, 1.75), (0, 0, R(30)), 0.42)
    key(small, 'location', [
        (381, (X + 1.45, 1.9, 1.62)),
        (561, (X + 1.18, 2.1, 1.92)),
    ])
    key(small, 'rotation_euler', [
        (381, (R(-6), R(8), R(24))),
        (561, (R(4), R(-6), R(-18))),
    ])

    rc = ribbon('ribbon_c', [
        (X - 6.2, -1.6, 0.4), (X - 2.2, -2.2, -0.9), (X + 1.4, -1.8, 0.8),
        (X + 5.2, -2.4, -0.6),
    ], width=0.34, mat=mats['organza'], tilt_step=58.0)
    key(rc, 'location', [(381, (-1.6, 0.2, 0.2)), (561, (1.4, -0.2, 0.7))])
    key(rc, 'rotation_euler', [(381, (R(8), R(-4), R(6))), (561, (R(-6), R(8), R(-10)))])

    # 5샷 전용 조명 (1-4샷 조명은 여기까지 안 닿는다)
    for nm, loc, rot, size, en, col in [
        ('bkey', (X - 3.2, -4.0, 4.2), (R(46), 0, R(-34)), 5.0, 340, (1, 1, 1)),
        ('bfill', (X + 4.2, -3.2, 1.2), (R(80), 0, R(52)), 6.0, 210, (1, 1, 1)),
        ('bback', (X, 5.2, 1.2), (R(96), 0, 0), 2.6, 260, (1.0, 0.95, 0.97)),
        ('bbnc', (X, -1.4, -1.9), (R(-90), 0, 0), 9.0, 100, (1.0, 0.95, 0.97)),
    ]:
        area_light(nm, loc, rot, size, en, color=col)
    return hero


# ---------------------------------------------------------------- 샷 / 카메라

def build_shots(hero_a, hero_b):
    X = STAGE_B_X
    cams = []

    # 컷마다 다른 카메라를 만들고 마커로 묶는다. 한 대를 순간이동시키면
    # 보간이 컷을 가로질러 번져서 컷 직후 몇 프레임이 흐른다.
    def shot(name, lens, fstop, focus, tgt_a, tgt_b, pos_a, pos_b, f0, f1, pad=26):
        tgt = add_empty(name + '_tgt', tgt_a)
        key(tgt, 'location', [(f0 - pad, tgt_a), (f1 + pad, tgt_b)])
        cam = add_camera(name, lens, fstop, focus, tgt)
        key(cam, 'location', [(f0 - pad, pos_a), (f1 + pad, pos_b)])
        bind(f0, cam)
        cams.append((cam, f0, f1))
        return cam

    # 1샷 (0.0-3.0s) 떠다니는 무리 사이로 밀고 들어간다
    shot('cam1', 50, 2.2, hero_a,
         (0.0, 0.0, 0.20), (0.0, 0.0, 0.02),
         (0.34, -9.20, 0.80), (0.12, -6.70, 0.22), 1, 90)

    # 2샷 (3.0-6.0s) 래티스 매크로. 셀 벽 사이로 역광이 새는 걸 보여 준다
    shot('cam2', 110, 3.4, hero_a,
         (0.0, 0.0, -0.05), (0.0, 0.0, 0.30),
         (0.55, -2.35, 0.10), (0.86, -2.88, 0.46), 91, 180)

    # 3샷 (6.0-9.0s) 3/4 각도, 리본이 앞을 가로질러 덮는다
    shot('cam3', 70, 2.6, hero_a,
         (-0.10, 0.0, 0.30), (0.05, 0.0, -0.05),
         (-1.95, -6.35, 1.15), (-2.62, -5.40, 0.10), 181, 270)

    # 4샷 (9.0-12.67s) 리본이 걷히며 정면이 드러나고 천천히 돈다
    shot('cam4', 65, 2.6, hero_a,
         (-0.05, 0.0, 0.20), (0.05, 0.0, 0.10),
         (-1.25, -5.15, 1.45), (0.42, -6.62, 0.22), 271, 380)

    # 5샷 (12.67-18.7s) 웅덩이 위. 가장 길고 가장 천천히 올라간다
    shot('cam5', 52, 3.2, hero_b,
         (X, 0.0, -1.35), (X, 0.0, -0.75),
         (X + 0.45, -7.6, -0.55), (X - 0.05, -6.6, 0.55), 381, 561, pad=40)

    bpy.context.scene.camera = cams[0][0]
    return cams


# ---------------------------------------------------------------- 렌더

def setup_render(out, res, samples, f0, f1, mblur=False):
    sc = bpy.context.scene
    avail = [i.identifier for i in
             bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = ('BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in avail
                        else ('BLENDER_EEVEE' if 'BLENDER_EEVEE' in avail else avail[0]))
    sc.render.resolution_x = res
    sc.render.resolution_y = int(round(res * 16.0 / 9.0))
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.fps = 30
    sc.frame_start = f0
    sc.frame_end = f1
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.compression = 15
    sc.render.use_motion_blur = mblur
    if mblur and hasattr(sc.render, 'motion_blur_shutter'):
        sc.render.motion_blur_shutter = 0.35
    sc.render.filepath = os.path.join(out, 'f')

    ee = getattr(sc, 'eevee', None)
    if ee is not None:
        for attr in ('taa_render_samples', 'samples'):
            if hasattr(ee, attr):
                setattr(ee, attr, samples)
        for attr, val in (('use_raytracing', True), ('use_bloom', False),
                          ('use_gtao', True), ('use_shadows', True),
                          ('use_volumetric_lights', False)):
            if hasattr(ee, attr):
                try:
                    setattr(ee, attr, val)
                    print('[reel]   eevee.%s = %s' % (attr, val))
                except Exception as e:
                    print('[reel]   eevee.%s 실패: %s' % (attr, e))
            else:
                print('[reel]   eevee.%s 없음' % attr)
    print('[reel] engine=%s  %dx%d  frames %d..%d  samples=%d  motion_blur=%s'
          % (sc.render.engine, sc.render.resolution_x, sc.render.resolution_y,
             f0, f1, samples, mblur))


def main():
    a = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
    except Exception as e:
        print('[reel] 기본 보간 설정 실패:', e)

    master = normalize(import_bear(a.obj), a.flip)
    ensure_slot(master)
    master.hide_render = True
    master.hide_viewport = True

    mats = {'organza': mat_organza()}
    for nm, rgb in PRODUCT.items():
        mats[nm] = mat_resin(nm, rgb)

    build_world()
    build_lights()
    hero_a = build_stage_a(master, mats)
    hero_b = build_stage_b(master, mats)
    cams = build_shots(hero_a, hero_b)
    for c, f0, f1 in cams:
        build_backdrop(c, f0, f1)

    out = a.out if os.path.isabs(a.out) else os.path.join(os.getcwd(), a.out)
    os.makedirs(out, exist_ok=True)
    setup_render(out, a.res, a.samples, a.start, a.end, a.mblur)
    if a.frames:
        sc = bpy.context.scene
        for f in [int(x) for x in a.frames.split(',') if x.strip()]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, 'f%04d.png' % f)
            bpy.ops.render.render(write_still=True)
            print('[reel] still', f)
    else:
        bpy.ops.render.render(animation=True)
    print('[reel] done ->', out)


if __name__ == '__main__':
    main()
