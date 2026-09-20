"""Authored controls for provenance, binding, geometry and withheld physical claims."""
import argparse
import copy
from decimal import Decimal
from fractions import Fraction as F
import itertools
import tempfile
from pathlib import Path
from adapter import evaluate
from reference import evaluate_reference
from check import verify
from common import Invalid, VERSION, load, write_new

def fixture():
    seeds=[]
    for offset in range(25):
        for ident in range(1,9):
            seeds.append({"location":"us-101","vehicle_id":str(ident),"frame_id":str(offset+1),
                          "global_time":str(1000000+offset*100),"preceding":str(100+ident),"lane_id":"1"})
    rows=[]
    for offset in range(21):
        for ident in range(1,9):
            for lead in (False,True):
                rows.append({"location":"us-101","vehicle_id":str(ident+100 if lead else ident),
                    "frame_id":str(offset+1),"global_time":str(1000000+offset*100),
                    "local_y":str(offset+30 if lead else offset),"v_length":"10" if lead else "20",
                    "lane_id":"1","preceding":"0" if lead else str(100+ident),
                    "following":str(ident) if lead else "0","space_headway":"0" if lead else "30","v_class":"2"})
    return seeds,rows

def agree(seeds,rows):
    a=evaluate(seeds,rows)
    b=evaluate_reference(seeds,rows)
    assert a==b
    assert all(c["physical_continuous_clearance"]=="unresolved" for c in a)
    return a

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    names=[]
    seeds,rows=fixture()
    result=agree(seeds,rows)
    assert all(c["recorded_sample_obligation"]=="supported" and c["minimum_proxy_metres"]=="762/125" for c in result)
    names.append("subtract_lead_length_not_ego_length_or_front_headway")
    assert agree(seeds,list(reversed(rows)))==result
    names.append("trace_order_invariance")
    for y,status in (("26.40419947","contradicted"),("26.40419948","supported")):
        altered=copy.deepcopy(rows)
        for r in altered:
            if r["vehicle_id"]=="101":
                r["local_y"]=str(Decimal(y)+(int(r["frame_id"])-1))
        assert agree(seeds,altered)[0]["recorded_sample_obligation"]==status
        names.append("threshold_bracket_"+status)
    for name,field,value,reason in [
        ("lost_lead","preceding","0","lead_binding_changed"),
        ("different_lead","preceding","102","lead_binding_changed"),
        ("changed_lane","lane_id","2","lane_binding_changed"),
        ("unknown_lane","lane_id","0","lane_binding_changed"),
        ("frame_clock_disagreement","frame_id","100","clock_frame_mismatch"),
        ("dimension_disagreement","v_length","21","length_changes")]:
        changed=copy.deepcopy(rows)
        row=next(r for r in changed if r["vehicle_id"]=="1" and r["frame_id"]=="11")
        row[field]=value
        answer=agree(seeds,changed)[0]
        assert answer["recorded_sample_obligation"]=="not_evaluated" and reason in answer["reasons"]
        names.append(name)
    for name,time in (("missing_start","1000000"),("missing_interior","1001000"),("missing_end","1002000")):
        changed=[r for r in rows if not (r["vehicle_id"]=="1" and r["global_time"]==time)]
        answer=agree(seeds,changed)[0]
        assert "missing_expected_frame" in answer["reasons"] and answer["recorded_sample_obligation"]=="not_evaluated"
        names.append(name)
    changed=copy.deepcopy(rows)
    extra=copy.deepcopy(changed[0]);extra["global_time"]="1000050";changed.append(extra)
    assert "off_grid_frame" in agree(seeds,changed)[0]["reasons"]
    names.append("off_grid_sample")
    for label,mutator,reason in [
        ("duplicate_identity",lambda s,r:r.append(copy.deepcopy(r[0])),"duplicate_identity_time"),
        ("wrong_site",lambda s,r:r[0].update(location="i-80"),"source_location"),
        ("missing_time",lambda s,r:r[0].pop("global_time"),"source_fields"),
        ("unknown_field",lambda s,r:r[0].update(safety=True),"source_fields"),
        ("nonfinite_coordinate",lambda s,r:r[0].update(local_y="NaN"),"decimal_string"),
        ("numeric_coercion",lambda s,r:r[0].update(local_y=0),"decimal_string"),
        ("negative_length",lambda s,r:r[0].update(v_length="-1"),"nonpositive_length"),
        ("huge_coordinate",lambda s,r:r[0].update(local_y=str(10**16)),"number_size"),
        ("wrong_query_identity",lambda s,r:r[0].update(vehicle_id="999"),"query_membership"),
        ("wrong_query_clock",lambda s,r:r[0].update(global_time="999999"),"query_membership"),
        ("missing_seed",lambda s,r:s.pop(),"seed_population"),
        ("unordered_seeds",lambda s,r:s.reverse(),"seed_order"),
        ("response_cap",lambda s,r:r.extend(copy.deepcopy(r[0]) for _ in range(5001-len(r))),"trace_population_or_cap")]:
        s,r=copy.deepcopy((seeds,rows));mutator(s,r)
        for evaluator in (evaluate,evaluate_reference):
            try:evaluator(s,r)
            except Invalid as exc:assert str(exc)==reason,(label,str(exc))
            else:raise AssertionError("accepted "+label)
        names.append(label)
    # Exhaustive small input grid with separately written scalar expectations.
    finite=0
    for ego,lead,length in itertools.product((0,10,20),(20,30,40),(5,10,20)):
        changed=copy.deepcopy(rows)
        for r in changed:
            if r["vehicle_id"]=="1":r["local_y"]=str(ego)
            if r["vehicle_id"]=="101":r["local_y"]=str(lead);r["v_length"]=str(length)
        answer=agree(seeds,changed)[0]
        expected=F(lead-ego-length)*F(381,1250)
        assert answer["minimum_proxy_metres"]==str(expected)
        assert answer["recorded_sample_obligation"]==("supported" if expected>=5 else "contradicted")
        finite+=1
    envelope={"document_id":"reiyah.public-motion.results","version":VERSION,
              "freeze_sha256":"authored","scope":"recorded_longitudinal_proxy_only",
              "source_rows":len(rows),"cases":result}
    mutations=[
        ("promoted_physical_claim",lambda r:r["cases"][0].update(physical_continuous_clearance="supported")),
        ("wrong_gap",lambda r:r["cases"][0].update(minimum_proxy_metres="30")),
        ("wrong_decision",lambda r:r["cases"][0].update(recorded_sample_obligation="contradicted")),
        ("omitted_case",lambda r:r["cases"].pop()),
        ("case_order",lambda r:r["cases"].reverse()),
        ("wrong_freeze",lambda r:r.update(freeze_sha256="other")),
        ("wrong_scope",lambda r:r.update(scope="physical_clearance")),
        ("added_claim",lambda r:r.update(safe=True))]
    for label,mutation in mutations:
        altered=copy.deepcopy(envelope);mutation(altered)
        try:verify(seeds,rows,altered,"authored")
        except Invalid as exc:assert str(exc)=="result_mismatch"
        else:raise AssertionError("accepted "+label)
        names.append(label)
    with tempfile.TemporaryDirectory(prefix="reiyah-json-") as tmp:
        for label,content,error in (("duplicate_json",'{"x":1,"x":2}',"duplicate_json_key"),("nonfinite_json",'{"x":NaN}',"nonfinite_json")):
            path=Path(tmp)/label;path.write_text(content)
            try:load(path)
            except Invalid as exc:assert str(exc)==error
            else:raise AssertionError("accepted "+label)
            names.append(label)
    receipt={"document_id":"reiyah.public-motion.controls","version":VERSION,
             "authored_controls":names,"finite_scalar_cases":finite,"passed":True,
             "scope":"constructed development controls; not independent incidents or replication"}
    write_new(args.output,receipt)
    print({"authored_controls":len(names),"finite_scalar_cases":finite,"passed":True})
if __name__=="__main__":main()
