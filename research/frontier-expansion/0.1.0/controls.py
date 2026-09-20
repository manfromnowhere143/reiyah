"""Authored controls, finite exhaustive values, and forged-result rejection."""
import copy,itertools,json,tempfile
from pathlib import Path
from format import Invalid,load_json
from contract import evaluate
from checker import verify,reference

def rejects(fn,reason):
    try: fn()
    except (Invalid,AssertionError,ValueError) as exc:
        assert reason in str(exc), (reason,str(exc))
        return
    raise AssertionError("accepted forged input/result: "+reason)

def run():
    allocation=load_json(Path(__file__).with_name("allocation.json"))
    base=allocation["cases"][0]["case"]
    checks=[]
    for entry in allocation["cases"]:
        result=evaluate(entry["case"])
        assert result["status"]==entry["expected"],entry["case"]["case_id"]
        verify(entry["case"],result)
        checks.append(entry["case"]["case_id"])
    malformed=[]
    def bad(name,edit,reason):
        c=copy.deepcopy(base);edit(c)
        rejects(lambda:evaluate(c),reason)
        rejects(lambda:reference(c),reason)
        malformed.append(name)
    bad("unknown-property",lambda c:c.update(unchecked=True),"case:keys")
    bad("wrong-frame",lambda c:c["worlds"][0]["lead"].update(frame_id="other"),"frame_mismatch")
    bad("wrong-bumper",lambda c:c["worlds"][0]["lead"].update(point="front_bumper"),"reference_point")
    bad("float-coordinate",lambda c:c["worlds"][0]["lead"]["samples"][0].__setitem__(1,0.0),"rational")
    bad("noncanonical",lambda c:c["worlds"][0]["lead"]["samples"][0].__setitem__(1,"2/2"),"canonical_rational")
    bad("huge-rational",lambda c:c["worlds"][0]["lead"]["samples"][0].__setitem__(1,str(10**19)),"rational_size")
    bad("duplicate-time",lambda c:c["worlds"][0]["lead"]["samples"][1].__setitem__(0,"0"),"sample_time_order")
    bad("empty-trace",lambda c:c["worlds"][0]["lead"].update(samples=[]),"sample_limit")
    bad("world-cap",lambda c:c.update(worlds=c["worlds"]*129),"world_limit")
    bad("sample-cap",lambda c:c["worlds"][0]["ego"].update(samples=[["0","0"]]*257),"sample_limit")
    bad("duplicate-world",lambda c:c["worlds"].append(copy.deepcopy(c["worlds"][0])),"duplicate_world")
    bad("unbound-actor",lambda c:c["worlds"][0].update(actor_id=None),"unbound_actor")
    bad("unknown-interpolation",lambda c:c["model"].update(interpolation="guess"),"interpolation")
    bad("sampled-worlds-not-exhaustive",lambda c:c["model"].update(world_set="sampled"),"world_set")
    bad("wrong-units",lambda c:c["claim"].update(distance_unit="feet"),"units")
    bad("reversed-window",lambda c:c["claim"].update(window=["2","0"]),"window_or_gap")
    bad("negative-gap",lambda c:c["claim"].update(minimum_gap="-1"),"window_or_gap")
    bad("schema-version",lambda c:c.update(schema_version="9"),"version")
    forged=[]
    for field,value in (("status","contradicted"),("input_sha256","0"*64),("safety","safe"),("worlds",[]),("reasoning_grounding","grounded")):
        r=evaluate(base);r[field]=value
        rejects(lambda:verify(base,r),"result_mismatch");forged.append(field)
    r=evaluate(base);r["worlds"][0]["minimum_observed_gap"]="6"
    rejects(lambda:verify(base,r),"result_mismatch");forged.append("wrong-minimum")
    r=evaluate(base);r["worlds"][0]["minimum_at"]="1"
    rejects(lambda:verify(base,r),"result_mismatch");forged.append("wrong-time")
    c=copy.deepcopy(base);c["claim"]["minimum_gap"]="6"
    rejects(lambda:verify(c,evaluate(base)),"result_mismatch");forged.append("changed-threshold")
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/"bad.json";p.write_text('{"x":1,"x":2}')
        rejects(lambda:load_json(p),"duplicate_json_key")
        p.write_text('{"x":NaN}');rejects(lambda:load_json(p),"nonfinite_json")
    # Exhaust all 3^6 endpoint combinations, both interpolation modes and
    # three clock shifts on asymmetric grids. This tests 4,374 cases.
    count=0
    for values in itertools.product(("0","3","6"),repeat=6):
        for interp,shift in itertools.product(("piecewise_linear","unspecified"),("-1/2","0","1/2")):
            c=copy.deepcopy(base);c["model"]["interpolation"]=interp
            c["worlds"][0]["ego"]["samples"]=[[t,v] for t,v in zip(("0","1","2"),values[:3])]
            c["worlds"][0]["lead"]["samples"]=[[t,v] for t,v in zip(("0","1/2","2"),values[3:])]
            c["worlds"][0]["lead"]["clock_shift"]=shift
            verify(c,evaluate(c));count+=1
    return {"document_id":"reiyah.frontier-expansion.controls","version":"0.1.0",
            "authored_cases":len(checks),"input_rejections":malformed,"result_rejections":forged,
            "json_rejections":2,"finite_cross_checks":count,
            "all_pass":True,"independent_replication":False}
if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True);args=parser.parse_args()
    result=run();Path(args.output).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result))
