"""Plot declared radii and dependent case outcomes; no continuous interpolation."""
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(directory):
    directory = Path(directory); summary = json.loads((directory / 'summary.json').read_text())
    rows = summary['summaries']; radii = [row['radius'] for row in rows]
    low = [float(Fraction(row['primary']['lower'])) for row in rows]
    high = [float(Fraction(row['primary']['upper'])) for row in rows]
    nominal = float(Fraction(rows[0]['primary']['nominal_delta']))
    colors = {'supported': '#176b59', 'excluded': '#68758c', 'unresolved': '#ad631d'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={'width_ratios': [1.15, 1]})
    fig.subplots_adjust(top=.82, bottom=.24, left=.07, right=.98, wspace=.30)
    fig.suptitle('Reference translation can change the fixed replacement decision', x=.07, ha='left', y=.97,
                 fontsize=15, weight='bold')
    fig.text(.07, .90, 'One existing box per image, one axis, fixed shape. Exposed development data; declared stress radii.', fontsize=10)
    left.axhline(0, color='#2c3440', linewidth=1)
    left.axhline(nominal, color='#68758c', linestyle=':', linewidth=1, label='Unchanged reference: 37/64')
    left.vlines(radii, low, high, color='#204d76', linewidth=2, label='Exact family interval at the stated radius')
    left.scatter(radii, low, color='#204d76', marker='_', s=80, zorder=3)
    left.scatter(radii, high, color='#204d76', marker='_', s=80, zorder=3)
    left.set_xscale('symlog', base=2, linthresh=1, linscale=.8)
    left.set_xticks(radii, [str(r) for r in radii]); left.set_xlim(-.2, 80)
    left.set_xlabel('Maximum translation (pixels)'); left.set_ylabel('Mean matching-loss improvement')
    left.set_title('Primary 64-image case', loc='left', fontsize=11)
    left.grid(axis='y', alpha=.18); left.legend(loc='upper left', fontsize=8, frameon=False)
    left.text(.03, .03, 'Reversal-radius infimum ≈ 7.6792 px\nNot attained; a 7.7109 px world reverses with 19 images.',
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
    right.set_xlabel('Maximum translation (pixels)'); right.set_ylabel('Overlapping diagnostic cases')
    right.set_title('All 73 dependent cases', loc='left', fontsize=11)
    handles, labels = right.get_legend_handles_labels()
    fig.legend(handles, labels, loc='center', bbox_to_anchor=(.755, .13), ncol=3, frameon=False, fontsize=8)
    fig.text(.07, .07, 'Intervals describe admitted worlds, not confidence intervals or measured annotation-error rates. '
             '73 cases reuse the same 64 images.', fontsize=8, color='#404854')
    fig.text(.07, .035, 'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. '
             'No endorsement.', fontsize=8, color='#404854')
    for ax in (left, right):
        ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(directory / 'translation.png', dpi=180, metadata={'Software': 'Matplotlib'})
    fig.savefig(directory / 'translation.svg', metadata={'Date': None})
    svg = directory / 'translation.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)


if __name__ == '__main__':
    plot(Path(__file__).resolve().parent)
