/* CARIBEAR — 키링 상세페이지 공통 동작 (keyring-basic.html · keyring-mini.html)
   caribear-site.js 다음에 로드한다.

   두 사이즈는 형태가 같고 가격·치수만 다르다. 그래서 페이지는 따로 두되(각자 URL·카피·
   스펙을 갖는다) 동작은 여기 한 곳에만 둔다 — 스와치 로직이 두 파일에서 갈라지는 걸 막는다.

     <script src="assets/js/caribear-site.js"></script>
     <script src="assets/js/caribear-pdp.js"></script>
     <script>CARIBEAR.initPDP({ size: 'basic' });</script>

   가격·치수는 각 HTML 에 이미 박혀 있다(JS 없이도 맞는 값이 보인다). 여기서는
   셰이드·각도·수량만 다룬다. 사이즈 칩은 상태 토글이 아니라 **다른 페이지로 가는 링크**다. */
(function (global) {
  'use strict';

  var PAGES = { basic: 'keyring-basic.html', mini: 'keyring-mini.html' };

  function initPDP(opts) {
    opts = opts || {};
    var size = CARIBEAR.sizeByKey(opts.size || 'basic');

    var params  = new URLSearchParams(location.search);
    var current = CARIBEAR.byKey(params.get('color') || 'grey');

    var main     = document.getElementById('pdp-main');
    var swWrap   = document.getElementById('pdp-swatches');
    var sizeWrap = document.getElementById('pdp-sizes');
    var crumb    = document.getElementById('crumb-color');
    var vLine    = document.getElementById('variant-line');
    var vMood    = document.getElementById('variant-mood');
    var ctaPrice = document.getElementById('cta-price');
    var qtyOut   = document.getElementById('qty');
    var cta      = document.getElementById('add-to-cart');
    var related  = document.getElementById('related');
    var qty = 1;

    /* initPDP 가 같은 DOM 에 두 번 불릴 수 있는 상황(SPA 라우터가 같은 페이지를 다시
       보여줄 때)을 대비해, 뭔가 채우기 시작하기 전에 컨테이너를 전부 비운다. 이 줄을
       각 컨테이너를 채우는 코드보다 뒤에 두면, 방금 이 실행에서 새로 넣은 것까지
       같이 지워버린다 — 그래서 반드시 맨 앞이어야 한다. */
    swWrap.innerHTML = '';
    sizeWrap.innerHTML = '';
    if (related) related.innerHTML = '';

    /* ---- 각도 썸네일 4컷 (front/three/side/back) ---- */
    var thumbWrap = document.getElementById('pdp-thumbs');
    thumbWrap.innerHTML = '';
    var angle = 'front';
    var thumbs = CARIBEAR.ANGLES.map(function (ang, i) {
      var b = document.createElement('button');
      b.className = 'thumb';
      b.type = 'button';
      b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
      b.setAttribute('aria-label', ang.toUpperCase() + ' 뷰');
      var img = document.createElement('img');
      img.className = 'bear';
      img.width = 237; img.height = 420;
      img.loading = 'lazy';
      img.alt = '';
      b.appendChild(img);
      b.addEventListener('click', function () { setAngle(ang); });
      thumbWrap.appendChild(b);
      return { el: b, img: img, ang: ang };
    });

    function setAngle(ang) {
      angle = ang;
      thumbs.forEach(function (t) {
        t.el.setAttribute('aria-pressed', t.ang === ang ? 'true' : 'false');
      });
      main.src = CARIBEAR.shot(current.key, ang);
    }

    /* ---- 사이즈 — 페이지 이동 링크. 고른 셰이드를 들고 넘어간다 ---- */
    var sizeLinks = CARIBEAR.SIZES.map(function (z) {
      var here = z.key === size.key;
      var a = document.createElement('a');
      a.className = 'size';
      a.textContent = z.label;
      a.href = PAGES[z.key] + '?color=' + current.key;
      a.setAttribute('aria-pressed', here ? 'true' : 'false');
      if (here) a.setAttribute('aria-current', 'page');
      a.title = z.label + ' · ' + z.dims + ' · ' + CARIBEAR.won(z.price);
      sizeWrap.appendChild(a);
      return { el: a, z: z };
    });

    function syncSizeLinks() {
      sizeLinks.forEach(function (s) {
        s.el.href = PAGES[s.z.key] + '?color=' + current.key;
      });
    }

    /* ---- 셰이드 스와치 ---- */
    var swatches = CARIBEAR.COLORS.map(function (c) {
      var b = document.createElement('button');
      b.className = 'swatch';
      b.type = 'button';
      b.style.setProperty('--sw', c.chip);
      b.setAttribute('aria-label', c.label + ' · FINISH ' + c.mood);
      b.setAttribute('aria-pressed', c.key === current.key ? 'true' : 'false');
      b.addEventListener('click', function () { select(c); });
      swWrap.appendChild(b);
      return { el: b, c: c };
    });

    function select(c) {
      current = c;
      swatches.forEach(function (s) {
        s.el.setAttribute('aria-pressed', s.c.key === c.key ? 'true' : 'false');
      });
      main.src = CARIBEAR.shot(c.key, angle);
      main.alt = '래티스 베어 참 — ' + c.label;
      thumbs.forEach(function (t) {
        t.img.src = CARIBEAR.shot(c.key, t.ang, true);
        t.img.alt = c.label + ' ' + t.ang.toUpperCase() + ' 뷰';
      });
      crumb.textContent = c.label;
      vLine.textContent = c.label + ' / ' + c.n;
      if (vMood) vMood.textContent = c.mood;
      document.title = 'Lattice Bear ' + size.label + ' · ' + c.label + ' — CARIBEAR®';
      syncSizeLinks();
      history.replaceState(null, '', '?color=' + c.key);
    }

    /* ---- 수량 ---- */
    function setQty(n) {
      qty = Math.min(10, Math.max(1, n));
      qtyOut.textContent = String(qty);
      ctaPrice.textContent = CARIBEAR.won(size.price * qty);
    }
    document.getElementById('qty-minus').addEventListener('click', function () { setQty(qty - 1); });
    document.getElementById('qty-plus').addEventListener('click', function () { setQty(qty + 1); });
    cta.addEventListener('click', function () {
      /* 데모 페이지 — 실제 장바구니 대신 선택값을 체크아웃으로 넘긴다 */
      cta.href = 'checkout.html?color=' + current.key + '&size=' + size.key + '&qty=' + qty;
    });

    /* ---- 연관 상품 ---- */
    if (related) {
      (opts.related || ['rose', 'sky', 'lilac', 'peach']).forEach(function (key) {
        var c = CARIBEAR.byKey(key);
        var a = document.createElement('a');
        a.className = 'card';
        a.href = PAGES[size.key] + '?color=' + c.key;
        a.innerHTML =
          '<div class="shot card__shot">' +
            '<img class="bear" src="' + CARIBEAR.shot(c.key, 'three', true) + '" ' +
                 'width="237" height="420" loading="lazy" decoding="async" ' +
                 'alt="' + c.label + ' 래티스 베어 참"></div>' +
          '<div class="card__body">' +
            '<h3>LATTICE BEAR ' + size.label + '</h3>' +
            '<small>' + c.label + ' / ' + c.n + ' · ' + c.mood + '</small>' +
            '<b>' + CARIBEAR.won(size.price) + '</b>' +
          '</div>';
        related.appendChild(a);
      });
    }

    select(current);
    setQty(1);
  }

  global.CARIBEAR.initPDP = initPDP;
  global.CARIBEAR.PDP_PAGES = PAGES;
})(window);
