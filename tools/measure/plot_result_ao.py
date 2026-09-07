"""Render aggregate AO evidence; no source annotations or model execution."""
import argparse
import json
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=pathlib.Path)
    parser.add_argument('output', type=pathlib.Path)
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'reiyah-result-ao-0.1.0'})
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.4),
                                    gridspec_kw={'width_ratios': [1, 1.7]})
    refs = result['ghost_reference_population']
    percentages = [100 * refs[c]['fraction_of_original_ghost_flags_reclassified']
                   for c in ['camera', 'lidar']]
    left.barh(['Camera', 'Lidar'], percentages, color=['#275d83', '#7c536c'], height=.5)
    for i, value in enumerate(percentages):
        left.text(value + .5, i, f'{value:.1f}%', va='center')
    left.set_xlim(0, 31)
    left.set_xlabel('Percent of historical flags')
    left.set_title('Flags near excluded annotations', loc='left', fontweight='bold', pad=15)
    left.invert_yaxis()
    labels = []
    row = 0
    for reference, label in [('filtered_cache', 'Filtered reference'),
                             ('full_annotations', 'Complete annotations')]:
        entry = result['temporal_null_sensitivity'][reference]['fixed_heading_support']
        for null, name, color in [('ego_relative', 'ego-relative', '#275d83'),
                                  ('world_fixed', 'world-fixed', '#7c536c')]:
            value = entry[null + '_ratio']
            low, high = entry[null + '_scene_bootstrap_percentile_95']
            right.errorbar(value, row, xerr=np.array([[value-low], [high-value]]),
                           fmt='o', color=color, capsize=4, markersize=6)
            right.text(high + .2, row, f'{value:.2f}', va='center', color=color)
            labels.append(label + '\n' + name)
            row += 1
    right.set_yticks(range(row), labels)
    right.invert_yaxis()
    right.axvline(1, color='#9ca3af', linestyle=':', linewidth=1)
    right.set_xlim(0, 18)
    right.set_xlabel('Observed / temporal-null coincidence')
    right.set_title('Different nulls, different estimands', loc='left', fontweight='bold', pad=15)
    for ax in [left, right]:
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle('Reiyah AO: reference absence is not physical nonexistence',
                 fontsize=14, fontweight='bold', x=.04, ha='left')
    fig.text(.04, .025, 'Existing public predictions at score 0.30. Intervals: scene-bootstrap percentiles.\n'
             'Fixed heading-eligible donor support; no independent physical adjudication.', fontsize=9)
    fig.tight_layout(rect=[.02, .1, .99, .91], w_pad=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata = {'Date': None} if args.output.suffix == '.svg' else {}
    fig.savefig(args.output, dpi=160, metadata=metadata)
    if args.output.suffix == '.svg':
        args.output.write_text('\n'.join(line.rstrip() for line in
                                        args.output.read_text().splitlines()) + '\n')
    plt.close(fig)


if __name__ == '__main__':
    main()
