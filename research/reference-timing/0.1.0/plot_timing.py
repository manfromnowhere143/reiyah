"""Plot conditional timing outcomes without images or object geometry."""
from fractions import Fraction
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


LABELS = {'current_strict': 'Current census / strict', 'current_partial': 'Current census / partial',
          'union_strict': 'Adjacent census union / strict', 'union_partial': 'Adjacent census union / partial'}


def plot(directory):
    directory = Path(directory); value = json.loads((directory/'summary.json').read_text())
    colors = ['#176b59', '#68758c', '#bd742f', '#d8b97f', '#dce1e6']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 9.2), gridspec_kw={'height_ratios': [1.15, 1]})
    fig.subplots_adjust(left=.27, right=.95, top=.80, bottom=.23, hspace=.65)
    fig.suptitle('A timing model leaves the replacement unresolved', x=.045, y=.965, ha='left', fontsize=16, weight='bold')
    fig.text(.045, .925, 'Same 64 development images. A declared interpolation model is usable for 973 current car annotations; 62 remain unknown.', fontsize=10)
    fig.text(.045, .891, 'Partial contracts retain optional unknown boxes. Strict contracts require complete motion. The union adds preceding-only cars.', fontsize=10)
    ax = axes[0]; ax.set_title('Primary comparison: all 64 images', loc='left', fontsize=11, pad=13)
    nominal = float(Fraction(value['primary'][0]['original_nominal_mean']))
    ax.scatter([nominal], [0], color='#176b59', s=48, zorder=4)
    labels = ['Inherited supplied projection'] + [LABELS[row['contract']] for row in value['primary']]
    for index, row in enumerate(value['primary'], 1):
        if row['decision'] == 'input_blocked':
            reason = 'Preceding census unavailable' if row['contract'] == 'union_partial' else 'Motion information incomplete'
            ax.text(-1.04, index, reason, va='center', color='#68758c', fontsize=9)
            continue
        lower, upper = [float(Fraction(row[key])) for key in ('mean_lower', 'mean_upper')]
        ax.plot([lower, upper], [index, index], color='#4777a3', linewidth=5, alpha=.55, solid_capstyle='butt')
        ax.scatter([lower, upper], [index, index], marker='o', s=32, facecolor='white', edgecolor='#4777a3', zorder=4)
        lo, hi = [float(Fraction(row[key])) for key in ('attained_lower', 'attained_upper')]
        ax.scatter([lo, hi], [index, index], marker='D', color='#1b2838', s=32, zorder=5)
        ax.annotate('−21/64', (lo, index), xytext=(0, 13), textcoords='offset points', ha='center', fontsize=9)
        ax.annotate('61/64', (hi, index), xytext=(0, 13), textcoords='offset points', ha='center', fontsize=9)
    ax.axvline(0, color='#8c9299', linewidth=1, linestyle='--', zorder=1)
    ax.set_xlim(-1.1, 1.8); ax.set_ylim(4.55, -.65); ax.set_yticks(range(5), labels)
    ax.set_xticks([-1, -.5, 0, .5, 1, 1.5]); ax.set_xlabel('Mean matching-loss difference (old − new); strict improvement requires > 0')
    ax.spines[['top', 'left', 'right']].set_visible(False); ax.tick_params(axis='y', length=0, pad=10)
    ax.legend(handles=[Line2D([0], [0], color='#4777a3', linewidth=5, alpha=.55, label='Universal enclosure'),
                       Line2D([0], [0], marker='D', color='#1b2838', linestyle='none', label='Checked attained worlds')],
              loc='lower right', bbox_to_anchor=(1, 1.015), ncol=2, frameon=False, fontsize=8)
    ax = axes[1]; ax.set_title('All assigned cases: 73 overlapping cases per contract', loc='left', fontsize=11, pad=13)
    for index, row in enumerate(value['by_contract']):
        sizes = [row['supported'], row['excluded'], row['opposite_worlds'], row['bound_gaps'], row['input_blocked']]
        left = 0
        for size, color in zip(sizes, colors):
            if size:
                ax.barh(index, size, left=left, color=color, height=.60)
                ax.text(left+size/2, index, str(size), ha='center', va='center', fontsize=9,
                        color='white' if color in colors[:3] else '#263341')
                left += size
    ax.set_xlim(0, 73); ax.set_ylim(3.6, -.6); ax.set_yticks(range(4), [LABELS[row['contract']] for row in value['by_contract']])
    ax.set_xticks([0, 20, 40, 60, 73]); ax.set_xlabel('Assigned case count'); ax.tick_params(axis='y', length=0, pad=10)
    ax.spines[['top', 'left', 'right']].set_visible(False)
    names = ['Supported', 'Excluded', 'Unresolved: opposite worlds', 'Unresolved: bound gap', 'Input blocked']
    fig.legend(handles=[Patch(facecolor=color, label=name) for color, name in zip(colors, names)],
               loc='center', bbox_to_anchor=(.52, .163), ncol=3, frameon=False, fontsize=9)
    fig.text(.045, .096, 'All 292 rows and 115 native matching proofs are retained. Seven unresolved rows still have a bound gap.', fontsize=10)
    fig.text(.045, .064, 'This conditional projection study measures neither annotation error nor human savings or physical safety.', fontsize=9, color='#404854')
    fig.text(.045, .033, 'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. No endorsement.', fontsize=8, color='#404854')
    fig.savefig(directory/'timing.png', dpi=180, metadata={'Software': 'Matplotlib'})
    fig.savefig(directory/'timing.svg', metadata={'Date': None})
    path = directory/'timing.svg'; original = path.read_text()
    normalized = '\n'.join(line.rstrip() for line in original.splitlines())+'\n'
    def semantics(node):
        # XML canonicalization preserves redundant whitespace in SVG path
        # data. Removing line-end spaces changes that serialization while
        # preserving every path command and numeric token. Other attributes
        # and non-whitespace text must remain exact.
        attributes = tuple(sorted((key, ' '.join(value.split()) if key == 'd' else value)
                                  for key, value in node.attrib.items()))
        text = node.text if node.text and node.text.strip() else None
        tail = node.tail if node.tail and node.tail.strip() else None
        return node.tag, attributes, text, tail, tuple(semantics(child) for child in node)
    assert semantics(ET.fromstring(original)) == semantics(ET.fromstring(normalized))
    path.write_text(normalized); plt.close(fig)


if __name__ == '__main__':
    plot(Path(__file__).resolve().parent)
