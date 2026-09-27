# 송구리 에셋 키트

## 구성
- `character_sheet.png` — 포즈·팔레트 한눈에 보기
- `sprites/` — 송구리 6포즈(idle, up, jump, kick, point, throw) + 친구 4색(green, pink, navy, gold)
  - `_1x.png` 원본 픽셀(24×21), `_12x.png` 확대본(선명한 픽셀 유지)
- `props/` — 송편 3색, 반달 (투명 배경 PNG)
- `code/` — 영상 전체를 만든 코드
  - `lib.py` 스타일 엔진: 팔레트, 손그림 떨림 선, 종이 질감, 얇은 명조 텍스트, 스프라이트, 송편·달
  - `scenes.py` 추석 영상 스토리보드와 장면
  - `audio.py` BGM·효과음 합성, `render.py` 렌더러, `stills.py` 초안 스틸 확인용
- `fonts/get_fonts.sh` — Noto Serif KR 내려받기

## 스타일 가이드
- 팔레트: 아이보리 #F0EEE6 · 클레이 오렌지 #D97757 · 다크 #141413 · 딥 네이비 #1A2032
- 송편: 흰색 #FAF6EC · 쑥 #96BE76 · 분홍 #F2A6B6
- 서체: 모든 글자 Noto Serif KR ExtraLight/Light (얇은 명조체)
- 선: 10fps로 떨리는 손그림 선, 종이 질감 오버레이, 비네팅
- 캐릭터: 픽셀 캐릭터는 확대 시 반드시 Nearest(최근접) 보간

## 실행
```
pip install skia-python numpy scipy pillow
cd fonts && ./get_fonts.sh && cd ..
cp code/*.py . && python3 audio.py
python3 render.py 0 1500   # 조각 렌더링 후 ffmpeg로 이어 붙이기
```
새 영상은 `lib.py`는 그대로 두고 `scenes.py`만 새로 쓰면 같은 스타일이 유지됩니다.
