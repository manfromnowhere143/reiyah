"""Bind the already acquired three-file audit before full logical inspection."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

from packet_core import require
from packet_run import put
from packet_view import sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--area',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    area=args.area.resolve();output=args.output.resolve();here=Path(__file__).resolve().parent
    require(not output.exists(),'Freeze destination already exists');output.mkdir(parents=True)
    copies=output/'implementation';copies.mkdir()
    paths={}
    def add(path,role):
        path=path.resolve();require(path.is_file() and not path.is_symlink(),'Missing regular input')
        paths[str(path)]={'path':str(path),'role':role,'bytes':path.stat().st_size,'sha256':sha(path)}
    for path in sorted(here.iterdir()):
        if path.suffix=='.py' or path.name=='PLAN.md':
            add(path,'frozen_implementation');shutil.copyfile(path,copies/path.name)
    for session in ('e89','e93','e9c'):
        require((area/'sources'/('edgefirst-v-'+session+'-predictions.parquet')).is_file(),'Prediction file absent')
        require((area/'sources'/('edgefirst-'+session+'-t_inline_timings.json')).is_file(),'Timing chart absent')
    for path in sorted((area/'sources').iterdir()):
        if path.name.startswith(('edgefirst-','apache-','arrow-25-','polars-','polars_runtime_32-','pyarrow-')):
            add(path,'retained_private_source_or_reader_wheel')
    add(area/'sources/coco-instances_val2017.json','membership_and_category_index_only')
    for path in sorted((area/'private/reader-deps').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and (
                path.suffix in ('.py','.so','.dylib') or path.name in ('METADATA','WHEEL','RECORD')):
            add(path,'installed_reader_runtime')
    add(Path(sys.executable),'python_executable')
    add(area/'private/run_phase.py','network_denied_phase_launcher')
    ledger=output/'ACQUISITION_LEDGER.jsonl';shutil.copyfile(area/'logs/downloads.jsonl',ledger)
    add(ledger,'immutable_acquisition_receipts')
    for path in sorted((area/'logs').glob('cached-*')):
        if path.is_file() and not path.name.startswith('cached-freeze-'):
            add(path,'retained_preparation_and_first_failures')
    for path in sorted((area/'private/source-followup-01').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            add(path,'retained_followup_preparation')
    frozen={'artifact_id':'reiyah.cached-packet-audit.freeze','version':'0.1.0','status':'exploratory',
            'frozen_utc':datetime.now(timezone.utc).isoformat(),'python_version':sys.version,
            'sessions':['e89','e93','e9c'],'maximum_rows_per_file':1000000,
            'maximum_phase_seconds':1200,'expected_images_per_file':5000,
            'readers':{'polars':'1.44.2','pyarrow':'25.0.1'},
            'new_inference_allowed':False,'image_pixel_access_allowed':False,
            'reference_accuracy_scoring_allowed':False,'reserved_outcome_access_allowed':False,
            'source_payload_redistribution_allowed':False,'bindings':list(paths.values())}
    put(output/'FREEZE.json',frozen)
    print(json.dumps({'freeze':str(output/'FREEZE.json'),'bindings':len(paths),
                      'sha256':sha(output/'FREEZE.json'),'frozen_utc':frozen['frozen_utc']}))


if __name__=='__main__':main()
