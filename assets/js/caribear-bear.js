/* CARIBEAR — lattice bear renderer
   형태 정본: 곰돌이키링_테스트출력.obj → assets/data/bear-form.json
   실측 표면 포인트 → kNN 스트럿 망 → 앞/뒷벽 2패스 렌더로 보로노이 래티스를 근사 */

(function (global) {
  'use strict';

  /* ---------- 1·2. 형태 — 실측 3D 파일에서 추출한 포인트 클라우드 ----------
     assets/data/bear-form.json 은 곰돌이키링_테스트출력.obj 에서 뽑은 것이다.
     (굵은 복셀로 래티스를 솔리드로 합침 → 외곽 표면 → 균등 샘플)
     형태를 바꾸려면 그 OBJ 를 다시 추출한다. 여기 좌표를 손대지 않는다. */

  var BOUNDS = { minY: -0.68, maxY: 1.91 };

  function loadForm(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error('bear-form.json 로드 실패: ' + r.status);
      return r.json();
    }).then(function (d) {
      var P = d.p, N = d.n, out = [];
      for (var i = 0; i < P.length; i += 3) {
        out.push({
          p: [P[i], P[i + 1], P[i + 2]],
          nrm: [N[i], N[i + 1], N[i + 2]]
        });
      }
      if (d.bounds) BOUNDS = d.bounds;
      return out;
    });
  }

  /* ---------- 3. 스트럿 망 — kNN 그래프 ----------------------------------- */
  /* 최근접 이웃 거리의 중앙값 → 스트럿 최대 길이. 포인트 수가 바뀌어도 셀 크기가 유지된다 */
  function estimateSpacing(pts) {
    var n = Math.min(300, pts.length), d = [];
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
    var cell = maxLen, grid = {};
    function key(a, b, c) { return a + '|' + b + '|' + c; }
    pts.forEach(function (pt, i) {
      var gk = key(Math.floor(pt.p[0] / cell), Math.floor(pt.p[1] / cell), Math.floor(pt.p[2] / cell));
      (grid[gk] || (grid[gk] = [])).push(i);
    });

    var seen = Object.create(null), edges = [];
    for (var i = 0; i < pts.length; i++) {
      var a = pts[i].p;
      var gx = Math.floor(a[0] / cell), gy = Math.floor(a[1] / cell), gz = Math.floor(a[2] / cell);
      var cand = [];
      for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) for (var dz = -1; dz <= 1; dz++) {
        var bucket = grid[key(gx + dx, gy + dy, gz + dz)];
        if (bucket) cand = cand.concat(bucket);
      }
      var scored = [];
      for (var m = 0; m < cand.length; m++) {
        var j = cand[m];
        if (j === i) continue;
        var b = pts[j].p;
        var d = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
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

  /* ---------- 4. 렌더러 --------------------------------------------------- */
  function CaribearHero(canvas, opts) {
    opts = opts || {};
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.color = opts.color || '#0A84FF';
    this.rim = opts.rim || '#FF2E88';
    this.rimBoost = opts.rimBoost == null ? 0.85 : opts.rimBoost;
    this.reduced = !!opts.reduced;
    this.touch = !!opts.touch;

    this.pts = opts.form;
    this.spacing = estimateSpacing(this.pts);
    this.edges = buildEdges(this.pts, 3, this.spacing * 2.35);

    this.disp = new Float32Array(this.pts.length * 3);
    this.vel = new Float32Array(this.pts.length * 3);
    this.proj = new Float32Array(this.pts.length * 3);

    this.rotY = -0.42;   /* 살짝 3/4 각 — 래티스 깊이가 가장 잘 읽히는 각도 */
    this.spin = this.reduced ? 0 : (Math.PI * 2) / 14;  /* 14초 1회전 */
    this.dragVel = 0;
    this.dragging = false;
    this.lastX = 0;
    this.pointer = { x: -9999, y: -9999, active: false };
    this.light = { x: -0.5, y: 0.6 };
    this.raf = null;

    this._resize = this.resize.bind(this);
    window.addEventListener('resize', this._resize);
    this.resize();
    this._bind();
  }

  CaribearHero.prototype.resize = function () {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var r = this.canvas.getBoundingClientRect();
    this.w = r.width; this.h = r.height;
    this.canvas.width = Math.round(r.width * dpr);
    this.canvas.height = Math.round(r.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.scale = (this.h * 0.70) / (BOUNDS.maxY - BOUNDS.minY);
    this.cx = this.w / 2;
    this.cy = this.h / 2 + (BOUNDS.maxY + BOUNDS.minY) / 2 * this.scale;
  };

  CaribearHero.prototype._bind = function () {
    var self = this, c = this.canvas;
    if (this.touch || this.reduced) return;  /* 터치·저모션에서는 커서 인터랙션 제거 */

    c.addEventListener('pointermove', function (e) {
      var r = c.getBoundingClientRect();
      self.pointer.x = e.clientX - r.left;
      self.pointer.y = e.clientY - r.top;
      self.pointer.active = true;
      /* 핑크 림 라이트가 커서를 추적 */
      self.light.x = (self.pointer.x / self.w - 0.5) * 2;
      self.light.y = (0.5 - self.pointer.y / self.h) * 2;
      if (self.dragging) {
        var dx = e.clientX - self.lastX;
        self.lastX = e.clientX;
        self.dragVel = dx * 0.010;
        self.rotY += self.dragVel;
      }
    });
    c.addEventListener('pointerleave', function () { self.pointer.active = false; });
    c.addEventListener('pointerdown', function (e) {
      self.dragging = true;
      self.lastX = e.clientX;
      c.setPointerCapture(e.pointerId);
      c.style.cursor = 'grabbing';
    });
    window.addEventListener('pointerup', function () {
      self.dragging = false;
      c.style.cursor = 'grab';
    });
  };

  CaribearHero.prototype.setColor = function (hex, rimBoost) {
    this.color = hex;
    if (rimBoost != null) this.rimBoost = rimBoost;
  };

  CaribearHero.prototype.start = function () {
    var self = this, prev = performance.now();
    (function loop(now) {
      var dt = Math.min((now - prev) / 1000, 0.05);
      prev = now;
      self.step(dt);
      self.draw();
      self.raf = requestAnimationFrame(loop);
    })(prev);
  };

  CaribearHero.prototype.step = function (dt) {
    if (!this.dragging) {
      this.rotY += (this.spin + this.dragVel * 60) * dt;
      this.dragVel *= Math.pow(0.02, dt);   /* 관성 감속 */
    }

    var s = this.scale, cx = this.cx, cy = this.cy;
    var cos = Math.cos(this.rotY), sin = Math.sin(this.rotY);
    var pts = this.pts, d = this.disp, v = this.vel, proj = this.proj;
    var px = this.pointer.x, py = this.pointer.y;
    var on = this.pointer.active && !this.reduced;
    var RAD = 120, RAD2 = RAD * RAD;   /* 명세: 반응 반경 120px */
    var K = 130, DAMP = 11;            /* 복원 ≈ 320ms cubic-bezier(.2,.8,.2,1) */

    for (var i = 0; i < pts.length; i++) {
      var i3 = i * 3, p = pts[i].p;
      var x = p[0] + d[i3], y = p[1] + d[i3 + 1], z = p[2] + d[i3 + 2];
      var rx = x * cos + z * sin;
      var rz = -x * sin + z * cos;
      var sx = cx + rx * s, sy = cy - y * s;
      proj[i3] = sx; proj[i3 + 1] = sy; proj[i3 + 2] = rz;

      /* 스퀴시 — 커서 아래 셀이 안쪽으로 눌렸다가 되돌아온다 */
      var fx = 0, fy = 0, fz = 0;
      if (on) {
        var ddx = sx - px, ddy = sy - py, dd2 = ddx * ddx + ddy * ddy;
        if (dd2 < RAD2) {
          var dl = Math.sqrt(dd2) || 1;
          var f = (1 - dl / RAD);
          f = f * f * 0.26;
          fx += (ddx / dl) * f * 0.22;   /* 살짝 옆으로 밀리고 */
          fy += (-ddy / dl) * f * 0.22;
          fz -= f * 1.35;                /* 주로 안쪽으로 눌린다 */
        }
      }
      v[i3]     += (fx * K - d[i3]     * K) * dt - v[i3]     * DAMP * dt;
      v[i3 + 1] += (fy * K - d[i3 + 1] * K) * dt - v[i3 + 1] * DAMP * dt;
      v[i3 + 2] += (fz * K - d[i3 + 2] * K) * dt - v[i3 + 2] * DAMP * dt;
      d[i3]     += v[i3]     * dt;
      d[i3 + 1] += v[i3 + 1] * dt;
      d[i3 + 2] += v[i3 + 2] * dt;
    }
  };

  CaribearHero.prototype.draw = function () {
    var ctx = this.ctx, proj = this.proj, edges = this.edges, pts = this.pts;
    ctx.clearRect(0, 0, this.w, this.h);

    var lx = this.light.x, ly = this.light.y;
    var ll = Math.hypot(lx, ly, 0.8) || 1;
    lx /= ll; ly /= ll;
    var cos = Math.cos(this.rotY), sin = Math.sin(this.rotY);
    var strut = Math.max(0.8, this.scale * this.spacing * 0.115);
    ctx.lineCap = 'round';

    /* 뒷벽 → 앞벽 2패스. 두 벽이 겹치며 무아레가 생긴다 */
    for (var pass = 0; pass < 2; pass++) {
      var back = pass === 0;
      for (var e = 0; e < edges.length; e++) {
        var a = edges[e][0], b = edges[e][1];
        var mz = (proj[a * 3 + 2] + proj[b * 3 + 2]) * 0.5;
        if ((mz < 0) !== back) continue;

        var na = pts[a].nrm;
        var nx = na[0] * cos + na[2] * sin;
        var rim = Math.max(0, nx * lx + na[1] * ly);
        rim = Math.pow(rim, 2.2);

        ctx.globalAlpha = back ? 0.30 : 0.80;
        ctx.strokeStyle = this.color;
        ctx.lineWidth = strut * (back ? 0.8 : 1);
        ctx.beginPath();
        ctx.moveTo(proj[a * 3], proj[a * 3 + 1]);
        ctx.lineTo(proj[b * 3], proj[b * 3 + 1]);
        ctx.stroke();

        if (!back && rim > 0.12) {
          ctx.globalAlpha = rim * this.rimBoost;
          ctx.strokeStyle = this.rim;
          ctx.lineWidth = strut * 1.15;
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
  };

  CaribearHero.load = function (canvas, url, opts) {
    return loadForm(url).then(function (form) {
      opts = opts || {};
      opts.form = form;
      return new CaribearHero(canvas, opts);
    });
  };

  global.CaribearHero = CaribearHero;
})(window);
