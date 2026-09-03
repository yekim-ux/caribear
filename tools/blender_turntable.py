# -*- coding: utf-8 -*-
"""
곰돌이 키링 3D 원본 -> 히어로용 턴테이블 루프 (배경 투명 WebM/VP9)

Blender 안에서만 돈다. 쉘에서:

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/blender_turntable.py -- \
        --obj "C:/.../곰돌이키링_테스트출력.obj" --out assets/video \
        --color blush --frames 120 --res 560 --samples 32

만드는 것:
    assets/video/bear-<color>-turntable.webm   (VP9 + 알파, 무한 루프용)

blender_render_bear.py 와 같은 스튜디오·같은 오소 카메라·같은 재질을 쓴다.
정지컷과 영상의 톤이 어긋나면 안 되기 때문에 조명 값은 그쪽을 그대로 가져온다.

원칙:
  - 형태는 손대지 않는다. Z축 회전(rotY)과 균등 배율만. LANDING_KIT.md §9 그대로다.
  - 배경 투명. 히어로의 그라디언트·글로우·바닥 그리드 위에 그대로 얹힌다.
    (투명 WebM 은 Chrome/Firefox/Edge 만 재생한다. Safari 는 <video poster> 의
     정지컷으로 떨어진다 — 지금 디자인이 원래 정지컷이므로 그게 곧 폴백이다.)
  - 첫 프레임 = 0도 = 정지컷 front 와 같은 각도. poster 로 bear-<color>.webp 를 쓰면
    영상이 로드되기 전/못 할 때 이음매가 안 보인다.
  - 마지막 프레임은 360도를 '포함하지 않는다'. 루프가 한 프레임 멈칫하는 걸 막는다.
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

# 정지컷과 같은 값이어야 한다 (tools/blender_render_bear.py PRODUCT)
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
    p.add_argument('--frames', type=int, default=120, help='한 바퀴 프레임 수')
    p.add_argument('--fps', type=int, default=24)
    p.add_argument('--res', type=int, default=560, help='가로 픽셀. 세로는 1.9배')
    p.add_argument('--samples', type=int, default=32)
    p.add_argument('--margin', type=float, default=1.16)
    p.add_argument('--flip', action='store_true', default=True)
    p.add_argument('--yaw0', type=float, default=0.0)
    p.add_argument('--png-frames', action='store_true',
                   help='WebM 대신 PNG 시퀀스로 뽑는다 (다른 방식으로 인코딩할 때)')
    return p.parse_args(argv)


def import_obj(path):
    print('[turntable] importing', path)
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
    """가장 긴 축을 +Z 로 세우고 원점 중심 · 높이 2.0. 균등 배율·직각 회전만 준다."""
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


def make_material(ob, rgb):
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


def area_light(name, loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, type='AREA')
    d.size, d.energy, d.color = size, energy, color
    o = bpy.data.objects.new(name, d)
    o.location, o.rotation_euler = loc, rot
    bpy.context.scene.collection.objects.link(o)


def build_studio():
    """정지컷과 같은 밝은 배경용 세팅 (key 380 / fill 240 / rim 190 / under 110)."""
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
    print('[turntable] ortho_scale %.3f' % cam_d.ortho_scale)


def spin(ob, frames, yaw0):
    """0 -> 360도를 frames 개로 쪼갠다. 360도 프레임은 넣지 않는다(루프 멈칫 방지)."""
    ob.rotation_mode = 'XYZ'
    # 등속 회전 — 기본 BEZIER 이징이 붙으면 루프 이음매에서 속도가 튄다.
    # Blender 5 에서 action.fcurves 가 사라져서, 키를 꽂기 전에 기본 보간을 바꾼다.
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    except Exception as e:
        print('[turntable] 기본 보간 설정 실패, BEZIER 로 간다:', e)
    for i in range(frames + 1):
        ob.rotation_euler = (0, 0, math.radians(yaw0 + 360.0 * i / frames))
        ob.keyframe_insert('rotation_euler', frame=i + 1)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames            # frames+1 은 0도와 겹치므로 뺀다


def setup_render(res, samples, fps, png_frames):
    sc = bpy.context.scene
    avail = [i.identifier for i in
             bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in avail else \
                       ('BLENDER_EEVEE' if 'BLENDER_EEVEE' in avail else avail[0])
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 1.9)
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.fps = fps
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.color_mode = 'RGBA'

    if png_frames:
        sc.render.image_settings.file_format = 'PNG'
        sc.render.image_settings.compression = 90
    else:
        sc.render.image_settings.file_format = 'FFMPEG'
        ff = sc.render.ffmpeg
        ff.format = 'WEBM'
        ff.codec = 'WEBM'            # VP9
        ff.constant_rate_factor = 'HIGH'
        ff.ffmpeg_preset = 'GOOD'
        ff.audio_codec = 'NONE'

    ee = getattr(sc, 'eevee', None)
    if ee is not None:
        for attr in ('taa_render_samples', 'samples'):
            if hasattr(ee, attr):
                setattr(ee, attr, samples)
        for attr in ('use_raytracing', 'use_gtao', 'use_shadows'):
            if hasattr(ee, attr):
                setattr(ee, attr, True)
    print('[turntable] engine', sc.render.engine, '| RGBA', sc.render.image_settings.color_mode)


def main():
    a = parse_args()
    if a.color not in PRODUCT:
        raise SystemExit('모르는 색: ' + a.color)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = normalize(import_obj(a.obj), a.flip)
    make_material(ob, PRODUCT[a.color])
    build_studio()
    build_camera(ob, a.margin)
    setup_render(a.res, a.samples, a.fps, a.png_frames)
    spin(ob, a.frames, a.yaw0)

    if a.png_frames:
        bpy.context.scene.render.filepath = os.path.join(out, 'f_')
    else:
        bpy.context.scene.render.filepath = os.path.join(
            out, 'bear-%s-turntable' % a.color)
    bpy.ops.render.render(animation=True)
    print('[turntable] done ->', bpy.context.scene.render.filepath)


if __name__ == '__main__':
    main()
