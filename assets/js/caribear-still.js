/* CARIBEAR — lattice bear 스틸 렌더러
   형태 정본은 assets/data/bear-form-shape.json (tools/build_bear_form.py 가 시안 이미지 기준으로 생성).
   페이지의 모든 곰 — 히어로·썸네일·상품컷·카트 이미지 — 을 이 파일이 한 번씩만 그린다.
   스트럿 망(kNN 그래프)은 모듈 레벨에서 딱 한 번 만들어 모든 캔버스가 공유한다. */
(function (global) {
  'use strict';

  var formPromise = null;

  function estimateSpacing(pts) {
    var n = Math.min(240, pts.length), d = [];
    for (var t = 0; t < n; t++) {
      var i = (t * 7919) % pts.length, a = pts[i].p, best = Infinity;
      for (var j = 0; j < pts.length; j += 3) {
        if (j === i) continue;
        var b = pts[j].p;
        var dd = (a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]) + (a[2]-b[2])*(a[2]-b[2]);
        if (dd < best) best = dd;
      }
      d.push(Math.sqrt(best));
    }
    d.sort(function (x, y) { return x - y; });
    return d[Math.floor(d.length / 2)];
  }

  function buildEdges(pts, k, maxLen) {
    var cell = maxLen, grid = Object.create(null);
    function key(a, b, c) { return a + '|' + b + '|' + c; }
    pts.forEach(function (pt, i) {
      var gk = key(Math.floor(pt.p[0]/cell), Math.floor(pt.p[1]/cell), Math.floor(pt.p[2]/cell));
      (grid[gk] || (grid[gk] = [])).push(i);
    });
    var seen = Object.create(null), edges = [];
    for (var i = 0; i < pts.length; i++) {
      var a = pts[i].p;
      var gx = Math.floor(a[0]/cell), gy = Math.floor(a[1]/cell), gz = Math.floor(a[2]/cell);
      var cand = [];
      for (var dx=-1; dx<=1; dx++) for (var dy=-1; dy<=1; dy++) for (var dz=-1; dz<=1; dz++) {
        var bucket = grid[key(gx+dx, gy+dy, gz+dz)];
        if (bucket) cand = cand.concat(bucket);
      }
      var scored = [];
      for (var m = 0; m < cand.length; m++) {
        var j = cand[m];
        if (j === i) continue;
        var b = pts[j].p;
        var d = Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
        if (d < maxLen) scored.push([d, j]);
      }
      scored.sort(function (x, y) { return x[0] - y[0]; });
      var lim = Math.min(k, scored.length);
      for (var s = 0; s < lim; s++) {
        var j2 = scored[s][1];
        var ek = i < j2 ? i + ':' + j2 : j2 + ':' + i;
        if (seen[ek]) continue;
        seen[ek] = 1;
        edges.push([i, j2]);
      }
    }
    return edges;
  }

  function loadForm(url) {
    if (formPromise) return formPromise;
    formPromise = fetch(url || 'assets/data/bear-form-shape.json').then(function (r) {
      if (!r.ok) throw new Error('bear-form-shape.json 로드 실패: ' + r.status);
      return r.json();
    }).then(function (d) {
      var P = d.p, N = d.n, pts = [];
      for (var i = 0; i < P.length; i += 3) {
        pts.push({ p: [P[i], P[i+1], P[i+2]], nrm: [N[i], N[i+1], N[i+2]] });
      }
      var spacing = estimateSpacing(pts);
      return {
        pts: pts,
        spacing: spacing,
        edges: buildEdges(pts, 3, spacing * 2.35),
        bounds: d.bounds || { minY: -0.68, maxY: 1.91 }
      };
    });
    return formPromise;
  }

  /* 곰 한 마리를 캔버스 좌표계에 그린다.
     b = color, rim, rimBoost, rotY, size, x, y — size/x/y 는 캔버스 대비 비율 */
  function drawBear(ctx, F, w, h, b) {
    var pts = F.pts, edges = F.edges;
    var span = F.bounds.maxY - F.bounds.minY;
    var size = b.size == null ? 0.78 : b.size;
    var scale = (h * size) / span;
    var cx = w * (b.x == null ? 0.5 : b.x);
    var cy = h * (b.y == null ? 0.5 : b.y) + (F.bounds.maxY + F.bounds.minY) / 2 * scale;
    var rotY = b.rotY == null ? -0.42 : b.rotY;
    var cos = Math.cos(rotY), sin = Math.sin(rotY);

    var lx = b.lightX == null ? -0.55 : b.lightX;
    var ly = b.lightY == null ? 0.55 : b.lightY;
    var ll = Math.hypot(lx, ly, 0.8) || 1; lx /= ll; ly /= ll;

    var n = pts.length, proj = new Float32Array(n * 3);
    for (var i = 0; i < n; i++) {
      var p = pts[i].p, i3 = i * 3;
      var rx = p[0] * cos + p[2] * sin;
      proj[i3] = cx + rx * scale;
      proj[i3+1] = cy - p[1] * scale;
      proj[i3+2] = -p[0] * sin + p[2] * cos;
    }

    var strut = Math.max(0.55, scale * F.spacing * 0.115);
    var rimBoost = b.rimBoost == null ? 0.85 : b.rimBoost;
    ctx.lineCap = 'round';

    for (var pass = 0; pass < 2; pass++) {
      var back = pass === 0;
      for (var e = 0; e < edges.length; e++) {
        var a = edges[e][0], c = edges[e][1];
        var mz = (proj[a*3+2] + proj[c*3+2]) * 0.5;
        if ((mz < 0) !== back) continue;

        var na = pts[a].nrm;
        var nx = na[0] * cos + na[2] * sin;
        var rim = Math.max(0, nx * lx + na[1] * ly);
        rim = Math.pow(rim, 2.2);

        ctx.globalAlpha = back ? 0.30 : 0.80;
        ctx.strokeStyle = b.color || '#4A434A';
        ctx.lineWidth = strut * (back ? 0.8 : 1);
        ctx.beginPath();
        ctx.moveTo(proj[a*3], proj[a*3+1]);
        ctx.lineTo(proj[c*3], proj[c*3+1]);
        ctx.stroke();

        if (!back && rim > 0.12) {
          ctx.globalAlpha = rim * rimBoost;
          ctx.strokeStyle = b.rim || '#FF2E88';
          ctx.lineWidth = strut * 1.15;
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
  }

  /* 캔버스 하나에 곰 여러 마리(그룹컷)까지 그린다 */
  function paint(canvas, F) {
    var bears = canvas.__bears;
    if (!bears || !bears.length) return;
    var r = canvas.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    var dpr = Math.min(global.devicePixelRatio || 1, 2);
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, r.width, r.height);
    /* 작은(뒤쪽) 곰부터 그려서 큰 곰이 앞에 오게 한다 */
    bears.slice().sort(function (a, b) {
      return (a.size == null ? 0.78 : a.size) - (b.size == null ? 0.78 : b.size);
    }).forEach(function (b) { drawBear(ctx, F, r.width, r.height, b); });
  }

  var registry = [];
  var resizeTimer = null;
  global.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      registry.forEach(function (item) { paint(item.canvas, item.F); });
    }, 150);
  });

  function find(canvas) {
    for (var i = 0; i < registry.length; i++) if (registry[i].canvas === canvas) return registry[i];
    return null;
  }

  /* .bear / data-bear / data-bears 가 붙은 캔버스를 전부 찾아 그린다 */
  function mountAll(root, url) {
    var nodes = (root || document).querySelectorAll('canvas.bear,canvas[data-bear],canvas[data-bears]');
    if (!nodes.length) return Promise.resolve(null);
    return loadForm(url).then(function (F) {
      Array.prototype.forEach.call(nodes, function (canvas) {
        var bears = null;
        if (canvas.dataset.bears) {
          try { bears = JSON.parse(canvas.dataset.bears); } catch (err) { bears = null; }
        }
        if (!bears) {
          bears = [{
            color: canvas.dataset.color || '#4A434A',
            rim: canvas.dataset.rim || '#FF2E88',
            rimBoost: canvas.dataset.rimboost ? parseFloat(canvas.dataset.rimboost) : 0.85,
            rotY: canvas.dataset.rot ? parseFloat(canvas.dataset.rot) : -0.42,
            size: canvas.dataset.size ? parseFloat(canvas.dataset.size) : 0.78
          }];
        }
        canvas.__bears = bears;
        registry.push({ canvas: canvas, F: F });
        paint(canvas, F);
      });
      return F;
    });
  }

  /* 색 교체 — PDP 스와치가 쓴다 */
  function retint(canvas, color, rim, rimBoost) {
    var item = find(canvas);
    if (!item) return;
    canvas.__bears.forEach(function (b) {
      b.color = color;
      if (rim) b.rim = rim;
      if (rimBoost != null) b.rimBoost = rimBoost;
    });
    paint(canvas, item.F);
  }

  function set(canvas, bears) {
    var item = find(canvas);
    if (!item) return;
    canvas.__bears = bears;
    paint(canvas, item.F);
  }

  global.CaribearStill = { load: loadForm, mountAll: mountAll, retint: retint, set: set };
})(window);
