"""Display verified piecewise-affine scalars; plotting does not choose policies."""
import csv
from fractions import Fraction as Q
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def draw(directory):
    directory=Path(directory)
    with (directory/'penalty-partition.csv').open() as stream:rows=list(csv.DictReader(stream))
    intervals=[r for r in rows if r['kind']=='open_interval'];xx=[];yy=[]
    for row in intervals:
        lo,hi=Q(row['left']),Q(row['right']);b,a=map(Q,row['delta_mean_coefficients'].split())
        xx.extend([float(lo),float(hi)]);yy.extend([float(b+a*lo),float(b+a*hi)])
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(13.5,7.0))
    fig.subplots_adjust(left=.075,right=.975,top=.765,bottom=.29,wspace=.29)
    fig.suptitle('Separate operating policies change the penalty conclusion',x=.055,y=.955,
                 ha='left',fontsize=17,weight='bold')
    fig.text(.055,.896,'Same 64 exposed images, 305 projected car references and fixed retained detector outputs.',fontsize=10)
    fig.text(.055,.852,'Each detector gets its own retrospective minimum. No deployment threshold or calibrated score policy is selected.',fontsize=10)
    old_color='#315f8b';new_color='#b55c33'
    ax=axes[0];ax.set_title('Complete nominal penalty domain',loc='left',fontsize=11,pad=13)
    ax.plot([0,1],[58/64,-21/64],color='#8c949c',linewidth=1.6,linestyle='--',label='Both original score > 0.25 policies')
    ax.plot(xx,yy,color=old_color,linewidth=2,label='Separate best retained policies')
    ax.set_xlim(0,1);ax.set_ylim(-.37,.95)
    ax.set_xlabel('Miss penalty share p');ax.set_ylabel('Mean weighted loss difference (old − new)')
    ax.legend(frameon=False,loc='upper right',fontsize=8)
    ax.annotate('At p = 1/2: old unit loss 207; new 210',xy=(.5,-3/128),xytext=(.07,.18),fontsize=8,
                arrowprops={'arrowstyle':'-','color':'#7d858e','linewidth':.8})
    ax.text(.035,.06,'Positive: new lower nominal loss\nNegative: old lower nominal loss',
            transform=ax.transAxes,fontsize=8,color='#48535f')
    ax=axes[1];ax.set_title('Detail: the only interval where new is lower',loc='left',fontsize=11,pad=13)
    ax.axvspan(0,1/17,color='#efd8ca',alpha=.7)
    ax.plot(xx,yy,color=old_color,linewidth=2)
    ax.scatter([0,1/17],[0,0],s=30,facecolor='white',edgecolor=old_color,zorder=5)
    ax.scatter([1/18],[1/1152],s=27,color=new_color,zorder=5)
    ax.axvline(1/17,color='#8c949c',linewidth=.8,linestyle=':')
    ax.set_xlim(0,.082);ax.set_ylim(-.0065,.002)
    ax.set_xticks([0,.02,.04,1/17,.08],['0','0.02','0.04','1/17','0.08'])
    ax.set_xlabel('Miss penalty share p (expanded scale)');ax.set_ylabel('Mean weighted loss difference (old − new)')
    ax.annotate('Tie at p = 1/17\nMiss / FP penalty = 1/16',xy=(1/17,0),xytext=(.011,-.0031),
                fontsize=9,arrowprops={'arrowstyle':'-','color':'#7d858e','linewidth':.8})
    ax.text(.04,.055,'For 0 < p < 1/18: 0 FP each;\nold misses 285 cars, new misses 284 of 305.',
            transform=ax.transAxes,fontsize=8,color='#48535f')
    for ax in axes:
        ax.axhline(0,color='#818a93',linewidth=.8);ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',color='#dfe3e8',linewidth=.6,alpha=.6);ax.set_axisbelow(True)
    fig.text(.055,.204,'New is lower only for 0 < miss/FP penalty < 1/16. The endpoints are ties; old is lower above 1/16.',fontsize=10)
    fig.text(.055,.161,'All 519 original threshold cells, 51 exact penalty cells and optimizer ties are retained. These are overlapping descriptions.',fontsize=9)
    fig.text(.055,.114,'Conditional on the supplied projection. Earlier reference ambiguity, conventional query parity and unproven savings remain.',fontsize=9,color='#48535f')
    fig.text(.055,.072,'No new inference, reserved outcomes, policy training or held-out gain. High miss counts are not an operating recommendation.',fontsize=9,color='#48535f')
    fig.text(.055,.030,'Derived from nuScenes (Motional). CC BY-NC-SA 4.0 and retained Dataset Terms; see DISTRIBUTION.md. No endorsement.',fontsize=8,color='#48535f')
    fig.savefig(directory/'envelope.png',dpi=180,metadata={'Software':'Matplotlib'})
    fig.savefig(directory/'envelope.svg',metadata={'Date':None})
    path=directory/'envelope.svg';raw=path.read_text();normalized='\n'.join(line.rstrip() for line in raw.splitlines())+'\n'
    def semantics(node):
        attrs=tuple(sorted((k,' '.join(v.split()) if k=='d' else v) for k,v in node.attrib.items()))
        return node.tag,attrs,node.text if node.text and node.text.strip() else None,\
            node.tail if node.tail and node.tail.strip() else None,tuple(semantics(c) for c in node)
    assert semantics(ET.fromstring(raw))==semantics(ET.fromstring(normalized))
    path.write_text(normalized);plt.close(fig)


if __name__=='__main__':draw(Path(__file__).resolve().parent)
