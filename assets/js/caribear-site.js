/* CARIBEAR — 사이트 공통 스크립트 (컬러 정본 · 내비 · 유틸)
   페이지는 정적이다 — 곰은 3D 원본을 Blender 로 렌더한 제품컷(assets/img/bear-*.webp)을 쓴다. */
(function (global) {
  'use strict';

  /* 8셰이드 — MILK LAB 무드. tools/blender_render_bear.py 의 PRODUCT 와 같은 값이어야 한다.
     chip: UI 스와치 색 = bear: 렌더 베이스 색 (밝은 배경이라 둘을 어긋나게 둘 이유가 없다).
     finish: 셰이드 서브라벨(코스메틱 마감 표현).
     GREY(01) 는 파스텔 7색을 받쳐 주는 중립색이다. 배경(#FBF7F4)과 색이 가까우므로
     억지로 어둡게 내리지 말고 컨테이너 톤·드롭섀도로 분리한다. */
  var COLORS = [
    { key:'grey',   n:'01', label:'GREY',   mood:'MISTY', chip:'#CFCAC8', bear:'#CFCAC8' },
    { key:'blush',  n:'02', label:'BLUSH',  mood:'DEWY',  chip:'#FFC2CE', bear:'#FFC2CE' },
    { key:'peach',  n:'03', label:'PEACH',  mood:'GLOW',  chip:'#FFC49B', bear:'#FFC49B' },
    { key:'butter', n:'04', label:'BUTTER', mood:'SOFT',  chip:'#FFE49A', bear:'#FFE49A' },
    { key:'mint',   n:'05', label:'MINT',   mood:'FRESH', chip:'#A9E0C8', bear:'#A9E0C8' },
    { key:'sky',    n:'06', label:'SKY',    mood:'CLEAR', chip:'#A9D2F2', bear:'#A9D2F2' },
    { key:'lilac',  n:'07', label:'LILAC',  mood:'AIRY',  chip:'#CBBCF0', bear:'#CBBCF0' },
    { key:'rose',   n:'08', label:'ROSE',   mood:'TINT',  chip:'#F58BA5', bear:'#F58BA5' }
  ];

  /* 2사이즈 — 형태는 같고 배율만 다르다 (LANDING_KIT.md §9). 렌더도 같은 컷을 그대로 쓴다.
     무게는 베이직 실측(TPE 실리콘 밀도 기준 약 1.046e-4 g/mm³) 대비 부피비로 환산 + 하드웨어(링) 여분. */
  var SIZES = [
    { key:'basic', label:'BASIC', dims:'45×45×85MM', weight:'20G', price:29000, was:36000 },
    { key:'mini',  label:'MINI',  dims:'25×25×40MM', weight:'5G',  price:18000, was:0 }
  ];

  function sizeByKey(key) {
    for (var i = 0; i < SIZES.length; i++) if (SIZES[i].key === key) return SIZES[i];
    return SIZES[0];
  }

  function byKey(key) {
    for (var i = 0; i < COLORS.length; i++) if (COLORS[i].key === key) return COLORS[i];
    return COLORS[0];
  }

  function won(n) { return '₩' + n.toLocaleString('ko-KR'); }

  /* 제품컷 경로 — Blender 로 3D 원본에서 뽑은 렌더 (tools/blender_render_bear.py)
     angle: front(기본) | three | side | back,  small: 디스크·썸네일용 작은 파일 */
  function shot(key, angle, small) {
    var a = (angle && angle !== 'front') ? '-' + angle : '';
    return 'assets/img/' + (small ? 'sm/' : '') + 'bear-' + key + a + '.webp';
  }
  var SHOT_ANGLES = ['front', 'three', 'side', 'back'];

  /* 모바일 내비 토글 */
  function initNav() {
    var toggle = document.querySelector('.nav__toggle');
    var links = document.getElementById('nav-links');
    if (!toggle || !links) return;
    toggle.addEventListener('click', function () {
      var open = links.getAttribute('data-open') === 'true';
      links.setAttribute('data-open', String(!open));
      toggle.setAttribute('aria-expanded', String(!open));
    });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && global.matchMedia('(max-width:1023px)').matches) {
        links.setAttribute('data-open', 'false');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initNav();
  });

  global.CARIBEAR = { COLORS: COLORS, byKey: byKey, won: won, shot: shot, ANGLES: SHOT_ANGLES,
                      SIZES: SIZES, sizeByKey: sizeByKey };
})(window);
