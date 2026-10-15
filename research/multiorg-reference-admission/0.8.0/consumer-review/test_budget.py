"""Exercise exact boundary admission without launching a worker."""
from pathlib import Path
import importlib.util,json,tempfile
from unittest.mock import patch
P=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('launch',P/'run_remaining_cohort.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=[]
for index in (2,3):
    required=(4-index)*1100+1800
    for remaining in (required,required-0.001):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'PLAN.json').write_text(json.dumps({'monotonic_start':0,'owner_wall_budget_seconds':7200,'prelaunch_reserve_seconds':1800}))
            with patch.object(m,'P',root),patch.object(m.time,'monotonic',return_value=7200-remaining):
                try:m.budget_admission(index);accepted=True
                except ValueError:accepted=False
            assert accepted==(remaining>=required)
            rows.append({'image':index,'remaining':remaining,'required':required,'accepted':accepted})
print(json.dumps({'status':'passed','cases':rows,'passed':len(rows),'model_forwards':0}))
