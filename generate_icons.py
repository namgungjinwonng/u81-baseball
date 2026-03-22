# -*- coding: utf-8 -*-
"""Generate PWA icons as PNG using basic bitmap drawing (no PIL needed)."""
import struct
import zlib
import os

def create_png(width, height, pixels):
    """Create a PNG file from raw RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter none
        for x in range(width):
            idx = (y * width + x) * 4
            raw += bytes(pixels[idx:idx+4])

    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend


def draw_icon(size):
    """Draw a baseball-themed icon."""
    pixels = [0] * (size * size * 4)
    cx, cy = size // 2, size // 2
    r = size // 2 - 2

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx, dy = x - cx, y - cy
            dist = (dx*dx + dy*dy) ** 0.5

            if dist <= r:
                # Circle background: dark navy gradient
                t = dist / r
                br = int(26 + (15 - 26) * t)
                bg = int(26 + (33 - 26) * t)
                bb = int(46 + (96 - 46) * t)
                pixels[idx] = br
                pixels[idx+1] = bg
                pixels[idx+2] = bb
                pixels[idx+3] = 255

                # Draw "U18" text area - white rectangle in center
                text_w = int(size * 0.6)
                text_h = int(size * 0.28)
                tx = cx - text_w // 2
                ty = cy - text_h // 2
                if tx <= x < tx + text_w and ty <= y < ty + text_h:
                    pixels[idx] = 233     # #e94560
                    pixels[idx+1] = 69
                    pixels[idx+2] = 96
                    pixels[idx+3] = 255

                # Top accent line
                line_y = int(size * 0.22)
                if abs(y - line_y) <= max(1, size // 80) and abs(dx) < r * 0.6:
                    pixels[idx] = 233
                    pixels[idx+1] = 69
                    pixels[idx+2] = 96
                    pixels[idx+3] = 255

                # Bottom accent line
                line_y2 = int(size * 0.78)
                if abs(y - line_y2) <= max(1, size // 80) and abs(dx) < r * 0.6:
                    pixels[idx] = 233
                    pixels[idx+1] = 69
                    pixels[idx+2] = 96
                    pixels[idx+3] = 255

                # Edge glow
                if dist > r - 3:
                    pixels[idx] = 233
                    pixels[idx+1] = 69
                    pixels[idx+2] = 96
                    pixels[idx+3] = 255
            else:
                pixels[idx+3] = 0  # transparent

    return pixels


base = os.path.dirname(os.path.abspath(__file__))
for size in [192, 512]:
    pixels = draw_icon(size)
    png_data = create_png(size, size, pixels)
    path = os.path.join(base, f'icon-{size}.png')
    with open(path, 'wb') as f:
        f.write(png_data)
    print(f"Generated {path} ({len(png_data)} bytes)")
