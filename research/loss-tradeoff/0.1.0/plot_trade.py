"""Plot exact primary decision regions, marking their equality outcomes."""
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def number(value):
    return float(Fraction(int(value['numerator']),int(value['denominator'])))


def label(family):
    direct={'exact_projection':'Exact supplied projection','one_edit_global':'One arbitrary edit globally',
            'one_edit_per_image':'One arbitrary edit per image'}
    if family in direct:return direct[family]
    prefix='One axis' if family.startswith('axis_') else 'Both coordinates'
    parts=family.split('_');radius=Fraction(int(parts[-2]),int(parts[-1]))
    return prefix+' ≤ '+str(float(radius) if radius.denominator!=1 else int(radius))+' px'


def plot(directory):
    directory=Path(directory);summary=json.loads((directory/'summary.json').read_text());rows=summary['primary']
    colors={'supported':'#176b59','excluded':'#68758c','unresolved':'#ad631d'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(12,8.6));fig.subplots_adjust(left=.29,right=.97,top=.77,bottom=.19)
    fig.suptitle('The replacement verdict depends on the miss penalty',x=.055,y=.96,ha='left',fontsize=16,weight='bold')
    fig.text(.055,.916,'Against the supplied projection: YOLO26n has 58 fewer false positives and 21 more misses than YOLO11n.',fontsize=10)
    fig.text(.055,.879,'Nominal strict improvement requires miss/false-positive penalty < 58/21 ≈ 2.7619. Equality excludes it.',fontsize=10)
    ax.axvline(.5,color='#293442',linestyle='--',linewidth=1,zorder=5)
    for index,row in enumerate(rows):
        for cell in row['continuum']:
            left,right=number(cell['left']),number(cell['right'])
            if not cell['point']:
                ax.broken_barh([(left,right-left)],(index-.31,.62),facecolors=colors[cell['decision']],edgecolors='none')
        for cell in row['continuum']:
            point=number(cell['left'])
            if cell['point'] and 0<point<1:
                ax.scatter([point],[index],s=23,color=colors[cell['decision']],edgecolors='white',linewidth=.7,zorder=6)
    ax.set_xlim(0,1);ax.set_ylim(len(rows)-.5,-.5)
    ax.set_yticks(range(len(rows)),[label(row['family']) for row in rows],fontsize=9)
    ax.set_xticks([0,.25,.5,.75,1]);ax.set_xlabel('Miss-penalty share p; false-positive share is 1 − p')
    ax.tick_params(axis='y',length=0,pad=9);ax.spines[['top','left','right']].set_visible(False)
    upper=ax.twiny();upper.set_xlim(ax.get_xlim());upper.set_xticks([0,1/3,.5,2/3,.8,1],['0','0.5','1','2','4','miss-only'])
    upper.set_xlabel('Miss / false-positive penalty ratio',labelpad=7);upper.spines[['left','right','bottom']].set_visible(False)
    legend=[Patch(facecolor=color,label=state) for state,color in colors.items()]
    fig.legend(handles=legend,loc='center',bbox_to_anchor=(.62,.125),ncol=3,frameon=False)
    fig.text(.055,.075,'Dashed line: equal penalties. Markers: exact boundary outcomes. Declared stress sets on the same 64 exposed images.',fontsize=9,color='#404854')
    fig.text(.055,.044,'These are conditional decision weights, not measured economic or safety costs. All 1,433 reserved images stay closed.',fontsize=9,color='#404854')
    fig.text(.055,.015,'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. No endorsement.',fontsize=8,color='#404854')
    fig.savefig(directory/'tradeoff.png',dpi=180,metadata={'Software':'Matplotlib'})
    fig.savefig(directory/'tradeoff.svg',metadata={'Date':None})
    path=directory/'tradeoff.svg';path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n');plt.close(fig)


if __name__=='__main__':plot(Path(__file__).resolve().parent)
