"""Validate the complete retained threshold partitions before using scalars."""
import csv
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

from envelope_math import require


MODELS=('YOLO11n','YOLO26n')
FIELDS={'model','cell_id','threshold_left','threshold_right','left_closed','right_closed',
        'false_positives','misses','predictions','matching_rank','references','unit_loss'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text())


def put(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def parse(rows,models=MODELS,counts=(299,220),references=305):
    require(all(set(r)==FIELDS for r in rows),'Curve fields differ')
    require(set(r['model'] for r in rows)==set(models),'Model allocation differs')
    output=[]
    for model,count in zip(models,counts):
        records=[r for r in rows if r['model']==model];require(len(records)==count,'Curve cell count differs')
        previous=Q(1,4);last_counts=None;lines=[];domains=[]
        for i,row in enumerate(records):
            require(row['cell_id']=='cell-'+str(i).zfill(4),'Missing or repeated curve cell')
            left,right=Q(row['threshold_left']),Q(row['threshold_right'])
            require(left==previous and Q(1,4)<=left<=right<=1,'Threshold coverage gap or overlap')
            require(row['left_closed']=='True','Open left threshold boundary')
            if i+1==count:
                require(left==right==1 and row['right_closed']=='True','Final singleton missing')
            else:require(left<right and row['right_closed']=='False','Invalid open-right threshold interval')
            numbers={k:int(row[k]) for k in ('false_positives','misses','predictions','matching_rank','references','unit_loss')}
            require(all(str(v)==row[k] and v>=0 for k,v in numbers.items()),'Noncanonical or negative count')
            fp,fn,n,m,r,loss=[numbers[k] for k in ('false_positives','misses','predictions','matching_rank','references','unit_loss')]
            require(r==references and fp==n-m and fn==r-m and loss==fp+fn,'Curve matching identity differs')
            if last_counts is not None:
                require(fp<=last_counts[0] and fn>=last_counts[1] and n<=last_counts[2],
                        'Stricter-policy monotonicity differs')
            last_counts=(fp,fn,n);previous=right
            lines.append({'id':row['cell_id'],'fp':fp,'fn':fn})
            domains.append({k:row[k] for k in ('cell_id','threshold_left','threshold_right','left_closed','right_closed')})
        require(last_counts==(0,references,0),'Empty final output missing')
        output.append({'model':model,'lines':lines,'threshold_domains':domains})
    return output


def load_curve(path):
    with Path(path).open(newline='') as stream:return parse(list(csv.DictReader(stream)))


def check_bindings(frozen):
    require(frozen['models']==list(MODELS) and frozen['population']==64,'Frozen comparison scope differs')
    for row in frozen['bindings']:
        path=Path(row['path'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size==row['bytes']
                and sha(path)==row['sha256'],'Frozen envelope input changed')
