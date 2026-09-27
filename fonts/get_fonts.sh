#!/bin/sh
# Noto Serif KR (SIL Open Font License) — 얇은 명조체
for w in ExtraLight Light Regular; do
  curl -sSL -o NotoSerifKR-$w.otf "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Serif/OTF/Korean/NotoSerifCJKkr-$w.otf"
done
