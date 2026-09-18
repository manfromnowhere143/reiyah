"""Compare exact intervals at evaluated radii without continuous interpolation."""
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(directory):
    directory = Path(directory); summary = json.loads((directory / 'summary.json').read_text())
    previous = json.loads((directory.parents[1] / 'reference-translation/0.1.0/summary.json').read_text())
    rows = summary['summaries']; radii = [row['radius'] for row in rows]
    low = [float(Fraction(row['primary']['universal_bounds_lower'])) for row in rows]
    high = [float(Fraction(row['primary']['universal_bounds_upper'])) for row in rows]
    axis_low = [float(Fraction(row['primary']['lower'])) for row in previous['summaries']]
    axis_high = [float(Fraction(row['primary']['upper'])) for row in previous['summaries']]
    colors = {'supported': '#176b59', 'excluded': '#68758c', 'unresolved': '#ad631d'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={'width_ratios': [1.15, 1]})
    fig.subplots_adjust(top=.81, bottom=.25, left=.07, right=.98, wspace=.30)
    fig.suptitle('Moving both coordinates widens reference uncertainty', x=.07, ha='left', y=.97,
                 fontsize=15, weight='bold')
    fig.text(.07, .90, 'One existing box per image, fixed shape; each coordinate may move by the stated radius.', fontsize=10)
    left.axhline(0, color='#2c3440', linewidth=1)
    left.axhline(37 / 64, color='#68758c', linestyle=':', linewidth=1)
    left.vlines(radii, low, high, color='#204d76', linewidth=5, alpha=.5, label='Both coordinates: exact interval')
    left.vlines(radii, axis_low, axis_high, color='#ae6425', linewidth=1.8, label='One axis: exact interval')
    left.scatter(radii, low, color='#204d76', marker='_', s=80, zorder=3)
    left.scatter(radii, high, color='#204d76', marker='_', s=80, zorder=3)
    left.set_xscale('symlog', base=2, linthresh=1, linscale=.8)
    left.set_xticks(radii, [str(r) for r in radii]); left.set_xlim(-.2, 80)
    left.set_xlabel('Maximum coordinate displacement (pixels)'); left.set_ylabel('Mean matching-loss improvement')
    left.set_title('Same primary 64-image case', loc='left', fontsize=11)
    left.grid(axis='y', alpha=.18); left.legend(loc='upper left', fontsize=8, frameon=False)
    left.text(.03, .03, '2D: supported at 5 px; an excluding world at 5.03125 px.\nA verified bracket, not an exact critical radius.',
              transform=left.transAxes, fontsize=8, va='bottom')
    bottom = [0] * len(rows)
    for state in ('supported', 'excluded', 'unresolved'):
        count = [row['decisions'][state] for row in rows]
        right.bar(range(len(rows)), count, bottom=bottom, color=colors[state], width=.74, label=state)
        for index, value in enumerate(count):
            if value >= 4:
                right.text(index, bottom[index] + value / 2, str(value), ha='center', va='center', color='white', fontsize=8)
        bottom = [a + b for a, b in zip(bottom, count)]
    right.set_xticks(range(len(rows)), [str(r) for r in radii]); right.set_ylim(0, 78)
    right.set_xlabel('Maximum coordinate displacement (pixels)'); right.set_ylabel('Overlapping diagnostic cases')
    right.set_title('2D family: all 73 dependent cases', loc='left', fontsize=11)
    handles, labels = right.get_legend_handles_labels()
    fig.legend(handles, labels, loc='center', bbox_to_anchor=(.755, .14), ncol=3, frameon=False, fontsize=8)
    fig.text(.07, .075, 'Declared stress sets, not measured error rates or confidence intervals. All unresolved rows have opposite worlds.',
             fontsize=8, color='#404854')
    fig.text(.07, .035, 'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. No endorsement.',
             fontsize=8, color='#404854')
    for ax in (left, right): ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(directory / 'translation-2d.png', dpi=180, metadata={'Software': 'Matplotlib'})
    fig.savefig(directory / 'translation-2d.svg', metadata={'Date': None})
    svg = directory / 'translation-2d.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n'); plt.close(fig)


if __name__ == '__main__':
    plot(Path(__file__).resolve().parent)
