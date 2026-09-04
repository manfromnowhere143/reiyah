"""Generate the Gate B robustness synthesis figure as a dependency-free SVG.

The figure carries the three robustness axes in one view:
  - conditional coefficient c versus score threshold          (Result N, the x axis)
  - two detector pairs, each with a bootstrap CI band         (Result M, the two series)
  - the E-value at the 0.3 reference point, annotated         (Result O)
  - the independence line at c = 1.0 that every point clears

All numbers are the measured values in evidence/measurement/result_n.txt and result_o.txt.
The script hardcodes them and cites those files; it computes only pixel geometry, so the
figure is reproducible and regenerates byte-identically.

Usage:
  python3 tools/measure/make_synthesis_figure.py > docs/gate_b_robustness_figure.svg
"""

import sys

# conditional coefficient c (L5, five admissible confounders), from result_n.txt
THRESH = [0.1, 0.2, 0.3, 0.4, 0.5]
MEGVII = [(1.360, 1.325, 1.380), (1.238, 1.217, 1.250), (1.151, 1.138, 1.160),
          (1.089, 1.081, 1.095), (1.051, 1.046, 1.055)]
POINTP = [(1.249, 1.221, 1.268), (1.139, 1.126, 1.149), (1.096, 1.087, 1.103),
          (1.069, 1.062, 1.074), (1.043, 1.038, 1.047)]
# E-values at the 0.3 reference point, from result_o.txt
EVAL_MEGVII_030 = 3.03
EVAL_POINTP_030 = 2.13

W, H = 800, 566
ML, MR, MT, MB = 74, 188, 92, 112
PW = W - ML - MR
PH = H - MT - MB
XMIN, XMAX = 0.10, 0.50
YMIN, YMAX = 1.00, 1.40

INK = "#1a1c22"
MUTE = "#6b7280"
GRID = "#e7e8ec"
C_MEG = "#1f5fa8"        # deep blue
C_MEG_BAND = "#1f5fa8"
C_PP = "#c2582a"         # burnt orange
C_PP_BAND = "#c2582a"
INDEP = "#b02a37"        # independence line, muted red


def x(t):
    return ML + (t - XMIN) / (XMAX - XMIN) * PW


def y(c):
    return MT + (YMAX - c) / (YMAX - YMIN) * PH


def band(series, color):
    top = " ".join(f"{x(t):.1f},{y(hi):.1f}" for t, (_p, _lo, hi)
                    in zip(THRESH, series))
    bot = " ".join(f"{x(t):.1f},{y(lo):.1f}" for t, (_p, lo, _hi)
                   in reversed(list(zip(THRESH, series))))
    return (f'<polygon points="{top} {bot}" fill="{color}" '
            f'fill-opacity="0.13" stroke="none"/>')


def line(series, color):
    pts = " ".join(f"{x(t):.1f},{y(p):.1f}" for t, (p, _lo, _hi)
                   in zip(THRESH, series))
    dots = "".join(f'<circle cx="{x(t):.1f}" cy="{y(p):.1f}" r="3.4" '
                   f'fill="{color}"/>' for t, (p, _lo, _hi)
                   in zip(THRESH, series))
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="2.4" stroke-linejoin="round"/>{dots}')


def main():
    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
      f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">')
    a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

    # title + subtitle
    a(f'<text x="{ML}" y="34" font-size="19" font-weight="700" fill="{INK}">'
      f'Camera and lidar fail together after conditioning</text>')
    a(f'<text x="{ML}" y="56" font-size="13" fill="{MUTE}">'
      f'Conditional joint-failure coefficient on nuScenes val, after class, range, '
      f'visibility, weather and motion.</text>')
    a(f'<text x="{ML}" y="73" font-size="13" fill="{MUTE}">'
      f'Above 1.0 means the two channels miss the same objects more than independence '
      f'predicts. Higher is worse.</text>')

    # y gridlines + labels
    for c in [1.0, 1.1, 1.2, 1.3, 1.4]:
        yy = y(c)
        a(f'<line x1="{ML}" y1="{yy:.1f}" x2="{ML + PW}" y2="{yy:.1f}" '
          f'stroke="{GRID}" stroke-width="1"/>')
        a(f'<text x="{ML - 12}" y="{yy + 4:.1f}" font-size="12" fill="{MUTE}" '
          f'text-anchor="end">{c:.1f}</text>')

    # independence line at 1.0, emphasized
    a(f'<line x1="{ML}" y1="{y(1.0):.1f}" x2="{ML + PW}" y2="{y(1.0):.1f}" '
      f'stroke="{INDEP}" stroke-width="1.6" stroke-dasharray="6 4"/>')
    a(f'<text x="{ML + PW - 4}" y="{y(1.0) - 8:.1f}" font-size="12" '
      f'fill="{INDEP}" text-anchor="end" font-weight="600">'
      f'independence (c = 1.0)</text>')

    # x ticks + labels
    for t in THRESH:
        a(f'<text x="{x(t):.1f}" y="{MT + PH + 24:.1f}" font-size="12" '
          f'fill="{MUTE}" text-anchor="middle">{t:.1f}</text>')
    a(f'<text x="{ML + PW / 2:.1f}" y="{MT + PH + 48:.1f}" font-size="13" '
      f'fill="{INK}" text-anchor="middle">detector score threshold</text>')
    a(f'<text x="20" y="{MT + PH / 2:.1f}" font-size="13" fill="{INK}" '
      f'text-anchor="middle" transform="rotate(-90 20 {MT + PH / 2:.1f})">'
      f'conditional coefficient c</text>')

    # bands then lines (megvii on top of pointpillars for legibility)
    a(band(POINTP, C_PP_BAND))
    a(band(MEGVII, C_MEG_BAND))
    a(line(POINTP, C_PP))
    a(line(MEGVII, C_MEG))

    # legend (right gutter)
    lx = ML + PW + 22
    a(f'<text x="{lx}" y="{MT + 6}" font-size="12" font-weight="700" '
      f'fill="{INK}">detector pair</text>')
    a(f'<text x="{lx}" y="{MT + 24}" font-size="11.5" fill="{MUTE}">'
      f'camera: Mapillary</text>')
    a(f'<line x1="{lx}" y1="{MT + 44}" x2="{lx + 26}" y2="{MT + 44}" '
      f'stroke="{C_MEG}" stroke-width="2.6"/>'
      f'<circle cx="{lx + 13}" cy="{MT + 44}" r="3.2" fill="{C_MEG}"/>')
    a(f'<text x="{lx}" y="{MT + 62}" font-size="12" fill="{INK}">'
      f'x Megvii (lidar)</text>')
    a(f'<text x="{lx}" y="{MT + 78}" font-size="11" fill="{MUTE}">'
      f'E-value 3.03 at 0.3</text>')
    a(f'<line x1="{lx}" y1="{MT + 104}" x2="{lx + 26}" y2="{MT + 104}" '
      f'stroke="{C_PP}" stroke-width="2.6"/>'
      f'<circle cx="{lx + 13}" cy="{MT + 104}" r="3.2" fill="{C_PP}"/>')
    a(f'<text x="{lx}" y="{MT + 122}" font-size="12" fill="{INK}">'
      f'x PointPillars (lidar)</text>')
    a(f'<text x="{lx}" y="{MT + 138}" font-size="11" fill="{MUTE}">'
      f'E-value 2.13 at 0.3</text>')

    # E-value gloss
    a(f'<text x="{lx}" y="{MT + 176}" font-size="11.5" font-weight="700" '
      f'fill="{INK}">E-value</text>')
    for i, ln in enumerate([
            "strength a hidden", "common cause needs", "on both arms to",
            "reach independence.", "Larger = more robust."]):
        a(f'<text x="{lx}" y="{MT + 194 + i * 15}" font-size="10.5" '
          f'fill="{MUTE}">{ln}</text>')

    # honest footer
    a(f'<text x="{ML}" y="{H - 26}" font-size="11" fill="{MUTE}">'
      f'Every interval excludes 1.0. The coupling attenuates as the threshold tightens '
      f'and does not reach independence in the measured range.</text>')
    a(f'<text x="{ML}" y="{H - 11}" font-size="11" fill="{MUTE}">'
      f'Association after declared conditioning, not a causal effect. Two published '
      f'detection outputs on one public split. One camera model, not yet replicated.</text>')

    a('</svg>')
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
