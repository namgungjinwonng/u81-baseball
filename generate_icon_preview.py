"""야구장 아이콘 생성 (미리보기용)"""
from PIL import Image, ImageDraw, ImageFont
import math

def create_baseball_field_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r = size // 2

    # 배경 원 (다크 네이비 - 앱 테마 색상)
    draw.ellipse([0, 0, size-1, size-1], fill='#1a1a2e')

    # 외야 잔디 (초록 원)
    grass_r = int(r * 0.82)
    grass_cy = cy + int(r * 0.15)
    draw.ellipse([cx - grass_r, grass_cy - grass_r, cx + grass_r, grass_cy + grass_r], fill='#2d7a3a')

    # 내야 다이아몬드
    diamond_r = int(r * 0.38)
    diamond_cy = grass_cy + int(r * 0.10)
    diamond_points = [
        (cx, diamond_cy - diamond_r),          # 2루 (위)
        (cx + diamond_r, diamond_cy),           # 1루 (오른쪽)
        (cx, diamond_cy + diamond_r),           # 홈 (아래)
        (cx - diamond_r, diamond_cy),           # 3루 (왼쪽)
    ]
    draw.polygon(diamond_points, fill='#c4956a')

    # 내야 잔디 (다이아몬드 안쪽 작은 초록)
    inner_r = int(r * 0.22)
    draw.ellipse([cx - inner_r, diamond_cy - inner_r, cx + inner_r, diamond_cy + inner_r], fill='#358a45')

    # 파울 라인 (홈에서 좌우로 뻗는 흰 선)
    home = diamond_points[2]
    line_w = max(2, size // 128)

    # 좌측 파울라인
    lf_end_x = cx - int(r * 0.78)
    lf_end_y = grass_cy - int(r * 0.55)
    draw.line([home, (lf_end_x, lf_end_y)], fill='white', width=line_w)

    # 우측 파울라인
    rf_end_x = cx + int(r * 0.78)
    rf_end_y = grass_cy - int(r * 0.55)
    draw.line([home, (rf_end_x, rf_end_y)], fill='white', width=line_w)

    # 베이스 (흰 사각형)
    base_size = max(3, size // 40)
    for bx, by in diamond_points[:3]:  # 2루, 1루, 홈 제외(홈은 오각형)
        draw.rectangle([bx - base_size, by - base_size, bx + base_size, by + base_size], fill='white')
    # 3루
    bx, by = diamond_points[3]
    draw.rectangle([bx - base_size, by - base_size, bx + base_size, by + base_size], fill='white')

    # 홈플레이트 (약간 큰 오각형)
    hp = diamond_points[2]
    hs = max(4, size // 32)
    home_plate = [
        (hp[0] - hs, hp[1] - hs//2),
        (hp[0] + hs, hp[1] - hs//2),
        (hp[0] + hs, hp[1] + hs//3),
        (hp[0], hp[1] + hs),
        (hp[0] - hs, hp[1] + hs//3),
    ]
    draw.polygon(home_plate, fill='white')

    # 마운드 (중앙 작은 원)
    mound_r = max(3, size // 40)
    draw.ellipse([cx - mound_r, diamond_cy - mound_r, cx + mound_r, diamond_cy + mound_r], fill='#c4956a')

    # 투수판 (흰색 작은 직사각형)
    pr_w = max(2, size // 50)
    pr_h = max(1, size // 120)
    draw.rectangle([cx - pr_w, diamond_cy - pr_h, cx + pr_w, diamond_cy + pr_h], fill='white')

    # 외야 경계 호 (흰색)
    arc_r = int(r * 0.78)
    arc_bbox = [cx - arc_r, grass_cy - arc_r, cx + arc_r, grass_cy + arc_r]
    draw.arc(arc_bbox, 200, 340, fill='#ffff88', width=max(2, size // 100))

    # "U18" 텍스트
    font_size = int(size * 0.13)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text = "U18"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    text_y = int(r * 0.18)

    # 텍스트 배경
    pad = size // 40
    draw.rounded_rectangle(
        [cx - tw//2 - pad, text_y - pad, cx + tw//2 + pad, text_y + th + pad],
        radius=size//30, fill='#e63946'
    )
    draw.text((cx - tw//2, text_y), text, fill='white', font=font)

    return img

# 512 미리보기 생성
img512 = create_baseball_field_icon(512)
img512.save('icon_preview_512.png')

# 192도 생성
img192 = create_baseball_field_icon(192)
img192.save('icon_preview_192.png')

print("미리보기 생성 완료: icon_preview_512.png, icon_preview_192.png")
