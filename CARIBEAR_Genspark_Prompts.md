# CARIBEAR — 젠스파크 이미지 생성 프롬프트 v2

> 시범/테스트용 웹사이트 시안용. 스펙 근거: `CARIBEAR_Web_Spec_v1.1.pdf`
> **v2 변경점** — 실제 3D 렌더를 기준으로 곰돌이 형태를 고정했고, 화면을 4개 카테고리로 묶었으며,
> 히어로를 영상·인터랙션 기준으로 다시 썼습니다.

---

## 형태 일관성을 잡는 방법 — 이게 제일 중요합니다

프롬프트만으로 캐릭터 형태를 반복 재현하는 건 **거의 불가능합니다.** 확실한 순서는 이렇습니다.

1. **가지고 계신 3D 렌더 1장을 젠스파크에 레퍼런스 이미지로 함께 업로드하세요.** 정면 컷(첫 번째 이미지)이 가장 좋습니다.
2. 프롬프트에 아래 **[BEAR]** 블록을 **글자 하나 바꾸지 말고** 매번 붙이세요.
3. 컬러 배리에이션은 새로 생성하지 말고, **원본 렌더를 색상만 바꿔서** 8컬러를 만드세요. 형태가 100% 동일해집니다.
4. 웹 화면 목업에 들어갈 제품 사진도 새로 생성하지 말고, **[CATEGORY 00]으로 뽑은 컷을 잘라 넣는다**는 전제로 목업에서는 제품을 단순 실루엣으로 요청하세요.

> 형태를 매번 새로 생성하면 귀 위치·고리 유무·셀 밀도가 컷마다 달라집니다.
> **제품 컷은 한 번만 뽑고 재사용**하는 게 정답입니다.

---

## [BEAR] — 캐릭터 락 블록 · 모든 프롬프트에 그대로 붙임

```
THE PRODUCT — always identical in every image, no variation allowed:

A small bear-shaped keyring built entirely from an open VORONOI LATTICE —
irregular polygonal cells with smooth rounded struts, like a 3D-printed
mesh shell. The bear is completely hollow and see-through; you can see the
inner back wall of the mesh through the front.

FORM, exactly:
- Sitting, symmetrical, facing straight forward
- A large round head, nearly as wide as the body
- Two round flat disc ears set wide apart on top of the head
- A small solid smooth ring loop rising from the very top of the head,
  centered between the two ears — this is the keyring attachment
- A rounded torso, short stubby arms hanging straight down against the sides
- Short stubby legs, feet pointing forward
- NO FACE AT ALL — no eyes, no nose, no mouth, no snout, no markings.
  The face is a blank lattice surface.

SURFACE: MATTE and OPAQUE. Soft diffuse finish like 3D-printed nylon
powder. NOT glossy, NOT wet, NOT translucent, NOT glass, NOT metallic,
no specular highlights, no reflections on the struts.

The mesh cells are medium-fine and even in density across the whole body.
```

---

## [BASE] — 웹 화면용 공통 스타일 블록

> 카테고리 01~03(웹 화면)에만 붙입니다. 카테고리 00(제품 컷)에는 붙이지 않습니다.

```
A high-fidelity website UI mockup, flat 2D screenshot, straight-on view.
No laptop, no phone frame, no hands, no desk, no perspective tilt,
no drop shadow around the page.

BRAND: CARIBEAR — a lattice bear keyring sold in 8 colors.
Y2K streetwear crossed with a technical spec sheet. Moody, never cute.

COLOR — use these exact hex values and no others:
- Page background #0A0A0A near-black, dominating about 70% of the image
- Primary text #F4F1F3 off-white
- Secondary text #A79FA4 warm grey
- Accent #FF2E88 neon hot pink, covering less than 10% of the image
- Hairline borders #2A252A, panel surfaces #131113
- Product colors, only inside product shots and color swatches:
  #FF3B30 red, #FF8A00 orange, #FFD60A yellow, #34C759 green,
  #0A84FF blue, #8B5CF6 purple, #FF2E88 pink, #0A0A0A black

TYPE:
- Headlines Space Grotesk Bold, ALL CAPS, very tight letter-spacing, huge
- Body Inter Regular
- Labels, prices, SKUs, meta in JetBrains Mono, UPPERCASE, wide spacing
- Every headline ends with a period rendered in hot pink #FF2E88

LAYOUT:
- 12-column grid, 1440px wide, wide margins, large areas of empty black
- EVERY element is a sharp rectangle with 90-degree corners.
  Zero border radius on buttons, cards, images, inputs, tags — everything.
- 1px hairline rules separating sections
- Tiny monospace meta text in the page corners like a technical document
```

---

# CATEGORY 00 — 제품 에셋 · 가장 먼저 뽑을 것

한 장으로 8컬러를 전부 확보합니다. 이 컷이 이후 모든 화면의 소스가 됩니다.

```
[BEAR]

COMPOSITION: A product lineup photograph, not a website.

Eight identical bear keyrings in one horizontal row, evenly spaced, all
shot from the exact same straight-on front angle, all the same size,
all perfectly aligned on the same baseline.

Left to right the eight colors are exactly:
1. black #0A0A0A
2. red #FF3B30
3. orange #FF8A00
4. yellow #FFD60A
5. green #34C759
6. blue #0A84FF
7. purple #8B5CF6
8. pink #FF2E88

Each bear is a single flat solid color across its entire lattice — the
struts are matte and uniformly colored, with no gradient and no shine.

LIGHTING: seamless near-black #0A0A0A studio background, soft key light
from the upper left at 45 degrees, plus a hot pink rim light from behind
so every silhouette separates cleanly from the dark ground — especially
the black one, which must stay clearly readable.

Sharp focus on the lattice structure. Wide 16:9 crop.
A tiny wide-spaced monospace caption along the bottom edge:
"FIG.01 — RAINBOW 8 LINEUP"

[NEGATIVE]
```

**추가로 뽑을 것 (같은 프롬프트에서 COMPOSITION만 교체):**

| 용도 | COMPOSITION 교체 문구 |
|---|---|
| PDP 메인 컷 | `A single black bear keyring centered on a pure WHITE seamless background, hard shadow beneath it, crisp edges.` ← 블랙 제품은 흰 배경 강제 |
| 무드 컷 | `A single black bear keyring hanging from a chain, on a near-black background, lit only by a strong hot pink rim light tracing the lattice edges.` |
| 디테일 컷 | `Extreme macro close-up of the lattice cells on the bear's torso, filling the frame, showing the rounded struts and hollow cells.` |

---

# CATEGORY 01 — 히어로 · 영상 / 인터랙션

## 01-A. 히어로 정지 프레임 (레이아웃 확정용)

```
[BASE]
[BEAR]

SCREEN: Homepage hero, full viewport, one single image.

Top: a slim navigation bar. Left, the wordmark "CARIBEAR." in Space
Grotesk Bold with a hot pink period. Right, small uppercase monospace
links "SHOP  DROPS  ABOUT" and "CART (2)".

Center of the screen, dominating the composition: one large black lattice
bear keyring floating against the near-black background, lit with a strong
hot pink rim light that traces every strut of the mesh so the silhouette
glows against the dark. Slight motion blur trailing behind it, as if it is
slowly rotating — this is a video still.

Overlaid on the left, an enormous headline stacked on three lines in
off-white Space Grotesk Bold ALL CAPS with extremely tight letter spacing:
"FLEX"
"YOUR"
"MOOD."
The final period is hot pink.

Under the headline, one line of small grey body text:
"Squishy lattice bear keyring, in 8 moods."
Below that, a sharp rectangular hot pink button with BLACK text reading
"SHOP DROP 001" — 90-degree corners, no rounding.

Bottom left, a small monospace scroll cue: "SCROLL ↓".
Bottom right, a small monospace video timecode: "00:03 / 00:08".
Bottom edge, a thin horizontal row of 8 small color squares in the 8
product colors, each with a thin light border, one of them outlined in
hot pink to show it is active.

A faint 45-degree diagonal pink line pattern in the background at very
low opacity, only behind the hero.

[NEGATIVE]
```

## 01-B. 히어로 영상 프롬프트 (영상 생성 도구용)

젠스파크의 영상 생성이나 다른 영상 툴에 넣으세요. **8초 루프, 무음, 9:16과 16:9 두 버전.**

```
[BEAR]

An 8-second seamless looping product video on a seamless near-black
#0A0A0A studio background.

MOTION: one black lattice bear keyring floats in the center and rotates
slowly and continuously around its vertical axis, a full 360 degrees over
the 8 seconds, at a constant speed. It drifts up and down by a few
millimeters as it turns. The keyring loop on top of its head stays
upright throughout.

LIGHT: a soft key light from the upper left stays fixed. A hot pink
#FF2E88 rim light sweeps slowly around the bear from behind, so different
parts of the lattice catch the pink edge glow as it rotates. The mesh
cells create shifting moire patterns as the front and back walls of the
lattice pass over each other during the turn.

CAMERA: locked off, no camera movement, no zoom, no shake.
The bear stays centered and the same size for the whole loop.
The first and last frame are identical so the loop is seamless.

Matte surface, no glossy highlights. No text, no captions, no logo,
no people, no hands. Shallow depth of field, the background stays pure
black and empty.
```

## 01-C. 히어로 인터랙션 명세 — 코딩 단계용 (이미지 생성 아님)

| 인터랙션 | 동작 | 근거 |
|---|---|---|
| **스퀴시 커서** | 커서가 곰 위를 지나면 그 지점의 래티스 셀이 안쪽으로 눌렸다가 되돌아옴. 반응 반경 120px, 복원 320ms `cubic-bezier(.2,.8,.2,1)` | SQUISHY가 1번 브랜드 필러인데 정지 이미지로는 증명되지 않음 |
| **드래그 회전** | 히어로 곰을 좌우로 드래그해 360° 직접 돌림. 손을 떼면 관성으로 감속 | 래티스 구조는 돌려봐야 이해됨 |
| **스크롤 컬러 전환** | 스크롤에 따라 곰 컬러가 8컬러를 순차 통과. 동시에 하단 스와치 로우의 활성 표시가 따라 이동 | "8가지 무드" 컨셉을 스크롤 자체로 설명 |
| **핑크 림 라이트 추적** | 커서 위치에 따라 림 라이트 각도가 따라옴 | 브랜드 시그니처 조명을 인터랙션으로 |

**필수 대응:**
- `prefers-reduced-motion: reduce` → 회전·스퀴시 전부 정지, **정지 프레임 1장으로 대체**
- 모바일·터치 → 커서 인터랙션 제거, **자동 회전 루프 영상만** 재생
- 영상은 `muted autoplay loop playsinline`, 첫 프레임을 포스터 이미지로 지정
- 3D 모델을 실시간 렌더할지 영상으로 대체할지는 **테스트용이므로 영상 권장** — 로딩·구현 비용이 훨씬 낮습니다

---

# CATEGORY 02 — 쇼핑 · 컬렉션 + 상세 (한 장에 2화면)

```
[BASE]
[BEAR]

Produce ONE single image containing TWO complete website screens stacked
vertically, separated by a thin hot pink hairline rule. A tiny monospace
label sits above each screen.

═══ TOP SCREEN — labeled "02 / COLLECTION" ═══

A page title in Space Grotesk Bold ALL CAPS reading "ALL BEARS." with a
hot pink period, and to its right a small monospace counter "8 ITEMS".
A 1px hairline rule beneath.

On the left, a narrow filter column with small uppercase monospace labels
"COLOR", "MOOD", "AVAILABILITY", each followed by tiny perfectly square
checkboxes.

The main area is a 4-column grid of 8 product cards. Each card shows one
lattice bear keyring in one of the 8 product colors, photographed
straight-on on pure black, and beneath the photo a monospace SKU code such
as "CB-RED-001", a product name in Space Grotesk SemiBold such as
"RED / SPICY", and a price in monospace tabular figures "38,000".

Two cards are sold out: their photos are desaturated to grey and dimmed to
40% opacity, with a small solid black rectangular tag in the top-left
corner reading "SOLD OUT" in tiny wide-spaced monospace. One card carries
a solid hot pink tag reading "NEW" in black text.

═══ BOTTOM SCREEN — labeled "03 / PRODUCT DETAIL" ═══

Split 7 columns left, 5 columns right.

Left: one large photograph of a single BLACK lattice bear keyring on a
pure WHITE background with a hard shadow beneath — a black product is
never shot on black. Below it, a row of 4 small square thumbnails with
thin borders.

Right, on the near-black background, stacked with generous spacing:
- tiny monospace breadcrumb "SHOP / RAINBOW 8 / BLACK"
- title in Space Grotesk Bold ALL CAPS "LATTICE BEAR — BLACK." with a
  hot pink period
- monospace meta line "CB-BLK-001 · MOOD CHILL · 58MM"
- a price block: "38,000" large in Space Grotesk Bold, beside a smaller
  struck-through grey "45,000", beside a hot pink monospace "-16%"
- a color selector of 8 small perfect squares in the 8 product colors,
  each with a thin light 1px border so the black one stays visible; the
  black square is selected and wrapped in a 2px hot pink outline with a
  clear gap between the square and the outline
- a quantity stepper: a thin rectangular outline containing a minus sign,
  the number 2 in monospace, and a plus sign
- a wide hot pink #FF2E88 rectangular button with BLACK text reading
  "ADD TO CART"
- below it a transparent button with a thin grey outline and off-white
  text reading "SIZE GUIDE"
- three collapsed rows separated by hairline rules, each with a small
  monospace label and a plus sign on the right:
  "MATERIAL", "SHIPPING", "RETURNS"

[NEGATIVE]
```

---

# CATEGORY 03 — 구매 흐름 + 모바일 (한 장에 4화면)

```
[BASE]
[BEAR]

Produce ONE single image laid out as a 2x2 grid of four separate website
screens on a neutral dark grey backdrop, each screen a flat rectangle with
a tiny monospace label above it. No phone frames, no hands, no perspective.

═══ TOP LEFT — "04 / CART" · desktop, wide ═══
Split 8 columns left, 4 columns right. A title "YOUR BAG." in Space
Grotesk Bold ALL CAPS with a hot pink period. Two line items separated by
hairline rules, each with a small square product thumbnail, a product
name, a monospace SKU, a compact quantity stepper, a monospace price, and
a small grey "REMOVE" text link.
On the right, a sticky order summary panel on a slightly lighter #131113
background with a thin border, containing monospace rows aligned left and
right with tabular figures: "SUBTOTAL 76,000", "SHIPPING 3,000",
"TOTAL 79,000". The total row sits below a hairline rule and is larger.
A full-width hot pink rectangular button with BLACK text reads "CHECKOUT".

═══ TOP RIGHT — "05 / CHECKOUT FORM" · desktop, wide ═══
A single centered column of form fields. Each field is a thin rectangle
with 90-degree corners and a small uppercase monospace label above it:
"EMAIL", "NAME", "ADDRESS", "CARD NUMBER". One field shows a 2px hot pink
focus outline. Beneath another field, a short error message in soft red
#FF6B6B reading "Enter the domain after the @ sign." At the bottom, a
full-width hot pink button with BLACK text reading "PAY 79,000".

═══ BOTTOM LEFT — "06 / MOBILE HOME" · narrow vertical, 375px wide ═══
The huge stacked headline "FLEX / YOUR / MOOD." filling most of the
screen, a black lattice bear keyring with a pink rim light behind the
type, a hot pink "SHOP DROP 001" button with black text, and a horizontal
row of the 8 colored bears along the bottom.

═══ BOTTOM RIGHT — "07 / MOBILE PDP" · narrow vertical, 375px wide ═══
A large product photo of the black lattice bear on white filling the top
half, then the title, the price, a horizontal row of 8 color squares with
the selected one outlined in hot pink, and a full-width hot pink
"ADD TO CART" button with black text pinned to the bottom edge.

All four screens share the same near-black background, the same tight
uppercase Space Grotesk headlines, and the same monospace meta text.
Every corner is sharp. Nothing is rounded.

[NEGATIVE]
```

---

## [NEGATIVE] — 모든 프롬프트 끝에 붙임

```
DO NOT INCLUDE: rounded corners, border radius, pill-shaped buttons,
glossy or wet or translucent surfaces, specular highlights, glass, metal,
chrome, drop shadows, glassmorphism, blurry gradients, purple-to-blue
gradients, neon glow bloom, pastel colors, beige, brown, cream, teal, gold.

On the bear specifically: no face, no eyes, no nose, no mouth, no snout,
no fur, no plush or fabric texture, no solid filled body, no closed
surface — the lattice must stay open and see-through. Do not change the
ear position, do not remove the ring loop on top of the head, do not add
a collar, bow, clothing, or accessories.

No cute cartoon mascots, no kawaii illustration, no emoji, no sparkles,
no hearts, no stars, no hand-drawn doodles, no script or serif fonts.
No stock-photo lifestyle scenes, no models, no hands holding the product,
no laptop or phone device frames, no desk photography, no perspective tilt.
No lorem ipsum, no garbled or misspelled text, no watermark.
No Korean or Chinese characters anywhere — all on-screen text in English.
```

---

## 뽑는 순서

**00 → 01-A → 01-B → 02 → 03**

00에서 8컬러 라인업이 확정돼야 나머지 화면의 제품 컷 톤이 어긋나지 않습니다.
01-A로 히어로 레이아웃을 잡고, 그 구도 그대로 01-B 영상을 뽑으면 정지↔영상이 이어집니다.
02·03은 각각 한 번에 여러 화면이 나오므로, 전체 시안이 **총 5회 생성**으로 끝납니다.

## 결과가 어긋날 때

| 증상 | 대응 |
|---|---|
| 곰 형태가 컷마다 다름 | **레퍼런스 이미지 업로드가 유일한 해법.** 프롬프트만으론 안 잡힙니다 |
| 곰에 눈·코가 생김 | `[NEGATIVE]`의 `no face, no eyes` 를 맨 앞으로 올리고 `[BEAR]`의 `NO FACE AT ALL` 을 한 번 더 반복 |
| 표면이 반질반질하게 나옴 | `matte`, `powder finish`, `no specular` 를 `[BEAR]` 안에서 3회 반복 |
| 머리 위 고리가 사라짐 | `a small solid ring loop on top of the head` 를 문장 맨 앞으로 이동 |
| 속이 꽉 찬 덩어리로 나옴 | `hollow`, `see-through`, `you can see the inner back wall through the front` 를 강조 |
| 버튼이 둥글게 나옴 | `[SCREEN]`에 `sharp 90-degree corners` 를 한 번 더 반복 |
| 2화면·4화면이 안 나오고 1장만 나옴 | 카테고리를 쪼개서 개별 생성. 모델이 복합 레이아웃을 못 따라가는 경우가 있습니다 |
| 핑크가 화면을 덮음 | `pink covers less than 10% of the image, black dominates` 추가 |
