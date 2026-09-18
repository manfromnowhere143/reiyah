"""Plot scalar development frontiers and exact threshold-step envelopes."""
import csv
from fractions import Fraction
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def draw(directory):
    directory = Path(directory)
    def rows(name):
        with (directory/name).open() as handle: return list(csv.DictReader(handle))
    budgets = rows('matched-fp-budgets.csv'); curves = rows('detector-curves.csv'); primary = rows('primary-thresholds.csv')
    summary = json.loads((directory/'summary.json').read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.1))
    fig.subplots_adjust(left=.075, right=.975, top=.765, bottom=.28, wspace=.29)
    fig.suptitle('The apparent winner depends on the operating policy', x=.055, y=.955, ha='left', fontsize=17, weight='bold')
    fig.text(.055, .895, 'Same 64 exposed development images, fixed outputs above score 0.25 and unit false-positive/miss penalties.', fontsize=10)
    fig.text(.055, .853, 'These are retrospective proxy comparisons. Thresholds are not calibrated probabilities or validated deployment choices.', fontsize=10)
    colors = ['#315f8b', '#b55c33']; ax = axes[0]
    ax.set_title('Nominal reference: fewest misses at each FP budget', loc='left', fontsize=11, pad=13)
    maximum = max(int(row['false_positives']) for row in curves)
    selected = [row for row in budgets if int(row['false_positive_budget']) <= maximum]
    xx = [int(row['false_positive_budget']) for row in selected]
    for model, prefix, color in zip(('YOLO11n', 'YOLO26n'), ('old', 'new'), colors):
        yy = [int(row[prefix+'_minimum_misses']) for row in selected]
        ax.step(xx, yy, where='post', color=color, linewidth=1.9, label=model)
        original = next(row for row in curves if row['model'] == model and row['cell_id'] == 'cell-0000')
        ax.scatter([int(original['false_positives'])], [int(original['misses'])], color=color, s=42, zorder=5)
    ax.axvline(69, color='#8b9299', linewidth=.8, linestyle=':')
    ax.annotate('At FP budget 69\nOld: 154 misses; new: 156', xy=(69, 154), xytext=(45, 241),
                fontsize=9, arrowprops={'arrowstyle': '-', 'color': '#7d858e', 'linewidth': .8})
    ax.set_xlim(0, maximum+5); ax.set_ylim(125, 305)
    ax.set_xlabel('Allowed total false positives on 64 images'); ax.set_ylabel('Fewest attained misses (lower is better)')
    ax.legend(frameon=False, loc='upper right', fontsize=9)
    ax.text(.04, .04, 'Dots: retained score > 0.25 settings', transform=ax.transAxes, fontsize=8, color='#4e5967')
    ax = axes[1]; ax.set_title('Common threshold: original-reference contracts', loc='left', fontsize=11, pad=13)
    for family, color, label in [('one_edit_per_image', '#bfc8d1', 'One arbitrary edit per image'),
                                 ('one_edit_global', '#7199bd', 'One arbitrary edit globally')]:
        selected = [row for row in primary if row['family'] == family]
        xx = [float(Fraction(row['threshold_left'])) for row in selected]
        low = [float(Fraction(row['mean_lower'])) for row in selected]
        high = [float(Fraction(row['mean_upper'])) for row in selected]
        ax.fill_between(xx, low, high, step='post', color=color, alpha=.60, linewidth=0, label=label)
    nominal = [row for row in primary if row['family'] == 'exact_projection']
    ax.step([float(Fraction(row['threshold_left'])) for row in nominal], [float(Fraction(row['mean_lower'])) for row in nominal],
            where='post', linewidth=1.25, color='#25394a', label='Exact supplied projection')
    ax.axhline(0, color='#8b9299', linestyle='--', linewidth=.9)
    ax.set_xlim(.25, 1); ax.set_ylim(-2.2, 3.1); ax.set_xticks([.25, .4, .55, .7, .85, 1])
    ax.set_xlabel('Strict retained-score threshold'); ax.set_ylabel('Mean loss difference (old − new)')
    ax.legend(frameon=False, loc='upper right', fontsize=8)
    ax.text(.04, .055, 'Positive: candidate improvement under that premise', transform=ax.transAxes, fontsize=8, color='#4e5967')
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color='#dfe3e8', linewidth=.6, alpha=.6); ax.set_axisbelow(True)
    fig.text(.055, .194, 'Retrospective minimum nominal loss: YOLO11n 207; YOLO26n 210. Every attained cell and tie is retained.', fontsize=10)
    fig.text(.055, .154, 'All 515 common-threshold cells with any remaining detections have opposing one-edit-per-image worlds.', fontsize=10)
    fig.text(.055, .108, 'The 517 cells and 7,707 case rows overlap. They are not independent trials. Camera-time contracts are retained in the tables.', fontsize=9, color='#48535f')
    fig.text(.055, .068, 'No reserved images, new inference, measured human savings or physical-safety claim. Empty outputs are not a quality recommendation.', fontsize=9, color='#48535f')
    fig.text(.055, .030, 'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. No endorsement.', fontsize=8, color='#48535f')
    if summary['common_threshold_cells'] != 517 or summary['primary_rows']+summary['anchor_rows'] != 7707:
        raise ValueError('Unexpected plotted allocation')
    fig.savefig(directory/'operating.png', dpi=180, metadata={'Software': 'Matplotlib'})
    fig.savefig(directory/'operating.svg', metadata={'Date': None})
    path = directory/'operating.svg'; original = path.read_text()
    normalized = '\n'.join(line.rstrip() for line in original.splitlines())+'\n'
    def semantics(node):
        attributes = tuple(sorted((key, ' '.join(value.split()) if key == 'd' else value) for key, value in node.attrib.items()))
        text = node.text if node.text and node.text.strip() else None
        tail = node.tail if node.tail and node.tail.strip() else None
        return node.tag, attributes, text, tail, tuple(semantics(child) for child in node)
    assert semantics(ET.fromstring(original)) == semantics(ET.fromstring(normalized))
    path.write_text(normalized); plt.close(fig)


if __name__ == '__main__':
    draw(Path(__file__).resolve().parent)
