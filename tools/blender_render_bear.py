# -*- coding: utf-8 -*-
"""
곰돌이 키링 3D 원본 -> 웹용 제품컷 PNG (배경 투명)

Blender 안에서만 돈다. 쉘에서:

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/blender_render_bear.py -- \
        --obj "C:/.../곰돌이키링_테스트출력.obj" --out assets/img \
        --colors black,red,orange,yellow,green,blue,purple,pink \
        --angles front,side,back,three --res 1600

만드는 것:
    assets/img/bear-<color>.png          (front)
    assets/img/bear-<color>-<angle>.png  (front 외)

원칙:
  - 형태는 손대지 않는다. 회전(카메라 각도)과 재질 색만 바꾼다.
  - 배경 투명(film_transparent). 다크 사이트 위에 그대로 얹는다.
  - 모든 컷이 같은 카메라·같은 조명이라 색끼리 흔들리지 않는다.
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

# 사이트 컬러 정본 (assets/js/caribear-site.js 와 같은 값)
PRODUCT = {
    'black':  (0x0A, 0x0A, 0x0A),
    'red':    (0xFF, 0x3B, 0x30),
    'orange': (0xFF, 0x8A, 0x00),
    'yellow': (0xFF, 0xD6, 0x0A),
    'green':  (0x34, 0xC7, 0x59),
    'blue':   (0x0A, 0x84, 0xFF),
    'purple': (0x8B, 0x5C, 0xF6),
    'pink':   (0xFF, 0x2E, 0x88),
}

# 카메라가 도는 각도 (오브젝트를 Z축으로 돌린다)
ANGLES = {'front': 0.0, 'three': -32.0, 'side': -90.0, 'back': 180.0}


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--obj', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--colors', default='black')
    p.add_argument('--angles', default='front')
    p.add_argument('--res', type=int, default=1600)
    p.add_argument('--samples', type=int, default=64)
    p.add_argument('--margin', type=float, default=1.14, help='피사체 대비 프레임 여유')
    p.add_argument('--flip', action='store_true',
                   help='모델이 거꾸로 들어올 때 X축 180도. 원본 파일마다 다르다')
    p.add_argument('--yaw0', type=float, default=0.0,
                   help='정면이 카메라를 보도록 돌리는 기준 각도(도)')
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_obj(path):
    print('[bear] importing', path)
    bpy.ops.wm.obj_import(filepath=path, forward_axis='NEGATIVE_Z', up_axis='Y')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        raise SystemExit('메시를 못 읽었다: ' + path)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    print('[bear] verts', len(ob.data.vertices), 'polys', len(ob.data.polygons))
    return ob


def normalize(ob, flip):
    """가장 긴 축을 +Z(위)로 세우고, 원점 중심 · 높이 2.0 으로 맞춘다.
       형태를 바꾸는 게 아니라 균등 배율·직각 회전만 준다."""
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    dims = list(ob.dimensions)
    up = dims.index(max(dims))
    if up == 0:                        # X 가 위 -> Y축으로 90도
        ob.rotation_euler = (0, 0, math.radians(90))
        bpy.ops.object.transform_apply(rotation=True)
        ob.rotation_euler = (0, math.radians(-90), 0)
        bpy.ops.object.transform_apply(rotation=True)
    elif up == 1:                      # Y 가 위 -> X축으로 90도
        ob.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)

    # 원점 중심으로
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    ob.location -= (lo + hi) / 2.0
    bpy.ops.object.transform_apply(location=True)

    s = 2.0 / max(1e-9, (hi - lo).z)
    ob.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)

    if flip:                            # 파일이 거꾸로 저장된 경우
        ob.rotation_euler = (math.radians(180), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)

    bpy.ops.object.shade_smooth()
    print('[bear] normalized dims', tuple(round(v, 3) for v in ob.dimensions))
    return ob


def make_material(ob):
    mat = bpy.data.materials.new('caribear')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.50      # 매트한 실리콘 (사진의 결)
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.42
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return bsdf


def set_color(bsdf, rgb):
    """베이스 컬러는 정본 값 그대로 쓴다.
       검정을 회색으로 띄우면 실버처럼 보인다 - 다크 배경에서의 가독성은
       베이스가 아니라 스튜디오의 림 라이트(스페큘러)가 만든다."""
    lin = [srgb_to_linear(c) for c in rgb]
    bsdf.inputs['Base Color'].default_value = (lin[0], lin[1], lin[2], 1.0)


def area_light(name, loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, type='AREA')
    d.size = size
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o)
    return o


def build_studio():
    """제품 사진과 같은 결: 정면 위 키라이트 + 옆 필 + 뒤 림"""
    R = math.radians
    area_light('key',  (-2.6, -3.4, 3.2), (R(52), 0, R(-38)), 5.0, 900)
    area_light('fill', ( 3.4, -2.6, 0.8), (R(80), 0, R(52)),  5.0, 300)
    area_light('rim',  ( 0.0,  3.6, 2.6), (R(126), 0, 0),     5.0, 700,
               color=(1.0, 0.78, 0.90))          # 사이트 핑크 쪽으로 살짝
    area_light('under',( 0.0, -1.6, -2.6),(R(-40), 0, 0),     4.0, 120)


def build_camera(ob, margin):
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'                          # 원근 왜곡 없이 = 형태가 정직하게 나온다
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    cam.location = (0, -8.0, 0.0)
    cam.rotation_euler = (math.radians(90), 0, 0)

    # 어느 각도로 돌려도 잘리지 않게, 세워 놓은 높이와 가로 반경으로 프레임을 잡는다
    bb = [Vector(c) for c in ob.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    r = max(math.hypot(v.x, v.y) for v in bb) * 2.0
    cam_d.ortho_scale = max(h, r) * margin
    print('[bear] ortho_scale %.3f' % cam_d.ortho_scale)
    return cam


def setup_render(res, samples):
    sc = bpy.context.scene
    engines = sc.bl_rna.properties['render'].fixed_type  # noqa
    avail = [i.identifier for i in
             bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in avail else \
                       ('BLENDER_EEVEE' if 'BLENDER_EEVEE' in avail else avail[0])
    print('[bear] engine', sc.render.engine)

    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 1.9)       # 곰이 세로로 길다
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.compression = 90
    sc.view_settings.view_transform = 'Standard'  # 제품 색을 정본 그대로 낸다

    ee = getattr(sc, 'eevee', None)
    if ee is not None:
        for attr in ('taa_render_samples', 'samples'):
            if hasattr(ee, attr):
                setattr(ee, attr, samples)
        for attr in ('use_raytracing', 'use_gtao', 'use_shadows'):
            if hasattr(ee, attr):
                setattr(ee, attr, True)


def main():
    a = parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    clear_scene()
    ob = normalize(import_obj(a.obj), a.flip)
    bsdf = make_material(ob)
    build_studio()
    build_camera(ob, a.margin)
    setup_render(a.res, a.samples)

    colors = [c.strip() for c in a.colors.split(',') if c.strip()]
    angles = [x.strip() for x in a.angles.split(',') if x.strip()]

    for name in colors:
        if name not in PRODUCT:
            print('[bear] 모르는 색, 건너뛴다:', name)
            continue
        set_color(bsdf, PRODUCT[name])
        for ang in angles:
            if ang not in ANGLES:
                print('[bear] 모르는 각도, 건너뛴다:', ang)
                continue
            ob.rotation_euler = (0, 0, math.radians(a.yaw0 + ANGLES[ang]))
            suffix = '' if ang == 'front' else '-' + ang
            path = os.path.join(out, 'bear-%s%s.png' % (name, suffix))
            bpy.context.scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            print('[bear] wrote', os.path.basename(path))

    print('[bear] done')


if __name__ == '__main__':
    main()
