# -*- coding: utf-8 -*-
"""
저널 02 "Inside the soft lattice" 용 구조 설명 컷.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/blender_detail_shots.py -- \
        --obj "C:/.../곰돌이키링_테스트출력.obj" --out assets/img --color blush --res 1200

만드는 것 (전부 배경 투명 PNG):
    journal-macro-<color>.png      래티스 살 굵기가 보이는 근접컷
    journal-section-<color>.png    앞쪽을 잘라내 속이 빈 걸 보여 주는 단면컷
    journal-structure-<color>.png  음영 없는 납작한 구조도 (셀 패턴만)

조명·재질·오소 카메라는 blender_render_bear.py 와 같은 값을 쓴다. 저널 컷만 톤이
달라지면 같은 제품으로 안 보인다.

## 단면컷을 만드는 법

메시를 자르지 않는다(5M 폴리곤에 Boolean 을 걸면 몇 분씩 걸리고 실패도 잦다).
대신 **카메라 clip_start 를 피사체 안쪽까지 밀어 넣는다** — 카메라와 클립면 사이가
통째로 안 그려지므로, 앞쪽 껍질이 사라지고 속이 드러난다. 형태는 손대지 않으니
LANDING_KIT.md §9 의 "형태 변형 금지"도 지킨다.
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

PRODUCT = {
    'grey':   (0xCF, 0xCA, 0xC8),
    'blush':  (0xFF, 0xC2, 0xCE),
    'peach':  (0xFF, 0xC4, 0x9B),
    'butter': (0xFF, 0xE4, 0x9A),
    'mint':   (0xA9, 0xE0, 0xC8),
    'sky':    (0xA9, 0xD2, 0xF2),
    'lilac':  (0xCB, 0xBC, 0xF0),
    'rose':   (0xF5, 0x8B, 0xA5),
}


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--obj', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--color', default='blush')
    p.add_argument('--res', type=int, default=1200)
    p.add_argument('--samples', type=int, default=96)
    p.add_argument('--margin', type=float, default=1.16)
    p.add_argument('--flip', action='store_true', default=True)
    return p.parse_args(argv)


def import_obj(path):
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
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    dims = list(ob.dimensions)
    up = dims.index(max(dims))
    if up == 0:
        ob.rotation_euler = (0, 0, math.radians(90))
        bpy.ops.object.transform_apply(rotation=True)
        ob.rotation_euler = (0, math.radians(-90), 0)
        bpy.ops.object.transform_apply(rotation=True)
    elif up == 1:
        ob.rotation_euler = (math.radians(90), 0, 0)
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
        ob.rotation_euler = (math.radians(180), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
    bpy.ops.object.shade_smooth()
    return ob


def studio_material(ob, rgb):
    mat = bpy.data.materials.new('caribear')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.50
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.42
    lin = [srgb_to_linear(c) for c in rgb]
    bsdf.inputs['Base Color'].default_value = (lin[0], lin[1], lin[2], 1.0)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return mat


def flat_material(ob, rgb):
    """음영 없는 납작한 색 — 구조도용. 셀 패턴(구멍)만 남는다."""
    mat = bpy.data.materials.new('caribear_flat')
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    em = nt.nodes.new('ShaderNodeEmission')
    lin = [srgb_to_linear(c) for c in rgb]
    em.inputs['Color'].default_value = (lin[0], lin[1], lin[2], 1.0)
    em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return mat


def area_light(name, loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, type='AREA')
    d.size, d.energy, d.color = size, energy, color
    o = bpy.data.objects.new(name, d)
    o.location, o.rotation_euler = loc, rot
    bpy.context.scene.collection.objects.link(o)
    return o


def build_studio():
    R = math.radians
    area_light('key',  (-2.6, -3.4, 3.2), (R(52), 0, R(-38)), 5.0, 380)
    area_light('fill', ( 3.4, -2.6, 0.8), (R(80), 0, R(52)),  5.0, 240)
    area_light('rim',  ( 0.0,  3.6, 2.6), (R(126), 0, 0),     5.0, 190,
               color=(1.0, 0.94, 0.96))
    area_light('under',( 0.0, -1.6, -2.6),(R(-40), 0, 0),     4.0, 110)


def build_camera(ob, margin):
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (0, -8.0, 0.0)
    cam.rotation_euler = (math.radians(90), 0, 0)
    bb = [Vector(c) for c in ob.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    r = max(math.hypot(v.x, v.y) for v in bb) * 2.0
    cam_d.ortho_scale = max(h, r) * margin
    return cam, cam_d


def setup_render(res_x, res_y, samples):
    sc = bpy.context.scene
    avail = [i.identifier for i in
             bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in avail else \
                       ('BLENDER_EEVEE' if 'BLENDER_EEVEE' in avail else avail[0])
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.compression = 90
    sc.view_settings.view_transform = 'Standard'
    ee = getattr(sc, 'eevee', None)
    if ee is not None:
        for attr in ('taa_render_samples', 'samples'):
            if hasattr(ee, attr):
                setattr(ee, attr, samples)
        for attr in ('use_raytracing', 'use_gtao', 'use_shadows'):
            if hasattr(ee, attr):
                setattr(ee, attr, True)


def shoot(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('[detail] wrote', os.path.basename(path))


def main():
    a = parse_args()
    if a.color not in PRODUCT:
        raise SystemExit('모르는 색: ' + a.color)
    rgb = PRODUCT[a.color]
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = normalize(import_obj(a.obj), a.flip)
    studio_material(ob, rgb)
    build_studio()
    cam, cam_d = build_camera(ob, a.margin)
    full_scale = cam_d.ortho_scale

    # ---- 1) 매크로: 몸통만 크게. 배율만 줄인다(형태는 그대로) ----
    setup_render(a.res, a.res, a.samples)
    cam_d.ortho_scale = full_scale * 0.34
    cam.location = (0, -8.0, -0.16)
    shoot(os.path.join(out, 'journal-macro-%s.png' % a.color))

    # ---- 2) 단면: 카메라 클립면을 피사체 안쪽까지 밀어 넣는다 ----
    cam_d.ortho_scale = full_scale
    cam.location = (0, -8.0, 0.0)
    setup_render(a.res, int(a.res * 1.9), a.samples)
    cam_d.clip_start = 8.0 - 0.22        # 카메라 y=-8, 피사체 중심 y=0
    shoot(os.path.join(out, 'journal-section-%s.png' % a.color))
    cam_d.clip_start = 0.1

    # ---- 3) 구조도: 음영 없는 납작한 색 ----
    flat_material(ob, rgb)
    shoot(os.path.join(out, 'journal-structure-%s.png' % a.color))

    print('[detail] done')


if __name__ == '__main__':
    main()
