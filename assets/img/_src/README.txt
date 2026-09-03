여기에 원본 제품 사진을 넣으세요.

1) 7색 정렬컷 (왼쪽부터 red, orange, yellow, green, blue, purple, black)
   - 파일 이름은 아무거나 상관없습니다. 예: bears-row.png
   - 흰 배경 그대로 두세요. 배경 제거는 스크립트가 합니다.

2) 각도별 컷을 따로 주실 경우 (선택)
   - 한 장에 한 마리만 나오게 하고, 파일 이름을 색 이름으로 지으세요.
     예: black.png, black-side.png, black-back.png

넣은 뒤 아래 명령을 실행하면 assets/img/bear-<color>.png 로 저장됩니다.

    python tools/prepare_product_shots.py --pink-from red

--pink-from red 는 사진에 없는 핑크를 빨강 곰의 색상만 옮겨 만듭니다.
핑크 실물 사진이 따로 있으면 그 옵션 없이 실행하고 pink.png 를 같이 넣으세요.
