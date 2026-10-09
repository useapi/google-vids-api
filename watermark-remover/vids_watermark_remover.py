#!/usr/bin/env python3
"""
Remove the visible Gemini sparkle (✦) from Google Vids videos.

Google Vids stamps a semi-transparent white four-pointed star in the bottom-right corner of every clip. This script
reverses that blend pixel by pixel (reverse alpha blending): clean = (frame - alpha * white) / (1 - alpha), using the
star's exact position, shape and opacity, measured from Vids clips in every format. Then it lightly smooths the star's
thin outline from its neighbours so no edge is left. No AI inpainting: the pixels under the star are recovered.

Works for every Vids format: 1280x720, 720x1280, 1920x1080, 1080x1920 (the star scales with the frame's short side).
Only the small area around the star is changed; the audio is copied untouched.

The invisible SynthID watermark Google also embeds is not affected.

Works on clips as generated and on upscales of them, not on extended or edited clips: those give the marked clip back
to the model, which repaints the star into the picture, so a faint diamond remains.

Requirements: Python 3.8+, numpy (pip install numpy), ffmpeg and ffprobe on PATH.

Usage:
    python3 vids_watermark_remover.py input.mp4 [output.mp4] [--crf 18]

Measured on Google Vids clips, October 2026 (Gemini Omni 1.1 Flash). If Google changes the mark, the numbers below need
measuring again.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

# The star at 720p (short side 720): centre 120 px from the right and bottom edges, radius 28.4 px, curve exponent 0.61
# (|dx/r|^p + |dy/r|^p <= 1). Everything scales with the short side / 720.
MARGIN, RADIUS, CURVE = 120.0, 28.4, 0.61
# Opacity and colour of the star: 0.300 at 720p, 0.283 at 1080p (Google draws it per resolution); colour is white
# (measured slightly above 255 per channel because of video encoding).
OPACITY = {720: 0.300, 1080: 0.283}
WHITE = np.array([265.6, 260.9, 257.9], dtype=np.float32)
# Edge softness in pixels: the 720p star is a little softer after encoding than the 1080p one.
SOFTNESS = {720: 0.5, 1080: 0.0}


VIDS_SIZES = {(1280, 720), (720, 1280), (1920, 1080), (1080, 1920)}
# exact colour conversion both ways, so frames away from the star come back unchanged
SWS = ['-sws_flags', 'accurate_rnd+full_chroma_int+bitexact']


def probe(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height,r_frame_rate,color_space,color_primaries,color_transfer,color_range',
         '-of', 'json', path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)['streams'][0]


def color_args(s):
    """Carry the input's colour tags over, so players show the clean file with the same colours."""
    tags = {'-colorspace': s.get('color_space'), '-color_primaries': s.get('color_primaries'),
            '-color_trc': s.get('color_transfer'), '-color_range': s.get('color_range')}
    return [x for k, v in tags.items() if v and v != 'unknown' for x in (k, v)]


def blur(m, sigma):
    """Gaussian blur of a 2-D map (edge softness of the star)."""
    if sigma <= 0:
        return m
    k = np.arange(-3, 4)
    g = np.exp(-k ** 2 / (2 * sigma * sigma))
    g /= g.sum()
    m = np.apply_along_axis(lambda v: np.convolve(v, g, 'same'), 0, m)
    return np.apply_along_axis(lambda v: np.convolve(v, g, 'same'), 1, m)


def box_blur(img, r):
    """Mean over a (2r+1)x(2r+1) square, per channel (used to smooth the star's outline)."""
    k = 2 * r + 1
    pad = np.pad(img, ((r, r), (r, r), (0, 0)), mode='edge')
    c = np.pad(pad.cumsum(0).cumsum(1), ((1, 0), (1, 0), (0, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def star(width, height):
    """The star's box (x, y, size) and its per-pixel opacity map for this frame size."""
    short = min(width, height)
    scale = short / 720
    native = 1080 if short >= 1000 else 720
    r = RADIUS * scale
    n = int(np.ceil(2 * r)) + 10
    cx, cy = width - MARGIN * scale, height - MARGIN * scale
    x0, y0 = int(round(cx - n / 2)), int(round(cy - n / 2))
    ss = 8  # supersampling for smooth edges
    o = (np.arange(ss) + 0.5) / ss
    yy = np.arange(n)[:, None, None, None] + o[None, None, :, None]
    xx = np.arange(n)[None, :, None, None] + o[None, None, None, :]
    inside = (np.abs((xx - (cx - x0)) / r) ** CURVE + np.abs((yy - (cy - y0)) / r) ** CURVE) <= 1
    alpha = blur(inside.mean((2, 3)), SOFTNESS[native] * scale) * OPACITY[native]
    return x0, y0, n, alpha.astype(np.float32), scale


def make_cleaner(width, height):
    x0, y0, n, alpha, scale = star(width, height)
    a = alpha[..., None]
    # the star's outline (partial coverage), widened about a pixel: smoothed after the reverse blend
    band = ((alpha > 0.005) & (alpha < alpha.max() * 0.97))[..., None].astype(np.float32)
    wide = box_blur(band, max(1, round(scale))) > 0.01
    keep = (~wide).astype(np.float32)
    weight = np.clip(box_blur(wide.astype(np.float32), 1), 0, 1)
    r = max(2, round(2 * scale))
    d1, d2 = box_blur(keep, r), box_blur(keep, 3 * r)

    def clean(frame):
        box = frame[y0:y0 + n, x0:x0 + n].astype(np.float32)
        out = (box - a * WHITE) / (1 - a)
        avg1 = box_blur(out * keep, r) / np.maximum(d1, 1e-3)
        avg2 = box_blur(out * keep, 3 * r) / np.maximum(d2, 1e-3)
        avg = np.where(d1 > 0.15, avg1, np.where(d2 > 0.03, avg2, out))
        out = out * (1 - weight) + avg * weight
        frame[y0:y0 + n, x0:x0 + n] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
        return frame

    return clean


def main():
    ap = argparse.ArgumentParser(description='Remove the visible Gemini sparkle from a Google Vids video.')
    ap.add_argument('input')
    ap.add_argument('output', nargs='?')
    ap.add_argument('--crf', type=int, default=18, help='x264 quality, lower is better (default 18)')
    ap.add_argument('--preset', default='medium', help='x264 preset (default medium)')
    ap.add_argument('--force', action='store_true', help='process a video that is not one of the Vids sizes')
    args = ap.parse_args()
    output = args.output or args.input.rsplit('.', 1)[0] + '_clean.mp4'
    if os.path.abspath(output) == os.path.abspath(args.input):
        sys.exit('Output must be a different file than the input')

    info = probe(args.input)
    width, height, rate = info['width'], info['height'], info['r_frame_rate']
    if (width, height) not in VIDS_SIZES and not args.force:
        sys.exit(f'{width}x{height} is not a Google Vids size (1280x720, 720x1280, 1920x1080, 1080x1920). '
                 'A cropped or resized video has the star somewhere else. Use --force to process it anyway')
    clean = make_cleaner(width, height)
    frame_bytes = width * height * 3

    decoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-noautorotate', '-i', args.input, *SWS, '-f', 'rawvideo',
                                '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    encoder = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{height}', '-r', rate,
         '-i', '-', '-i', args.input, '-map', '0:v', '-map', '1:a?', *SWS, '-c:v', 'libx264', '-crf', str(args.crf),
         '-preset', args.preset, '-pix_fmt', 'yuv420p', *color_args(info), '-c:a', 'copy', '-movflags', '+faststart',
         output], stdin=subprocess.PIPE)
    frames = 0
    try:
        while True:
            raw = decoder.stdout.read(frame_bytes)
            if len(raw) < frame_bytes:
                break
            frame = np.frombuffer(raw, np.uint8).reshape(height, width, 3).copy()
            encoder.stdin.write(clean(frame).tobytes())
            frames += 1
        encoder.stdin.close()
    except BrokenPipeError:
        decoder.kill()
        sys.exit('ffmpeg (encoder) failed')
    if decoder.wait() != 0:
        sys.exit('ffmpeg could not read the whole input')
    if encoder.wait() != 0 or frames == 0:
        sys.exit('ffmpeg (encoder) failed')
    print(f'{output}: {frames} frames, {width}x{height}')


if __name__ == '__main__':
    main()
