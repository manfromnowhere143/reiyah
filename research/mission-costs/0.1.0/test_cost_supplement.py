from copy import deepcopy
from decimal import Decimal
import hashlib,io,json
from pathlib import Path
import tarfile,tempfile
import unittest

from cost_supplement import archive_json,check,contained,number,put,reconcile,sha,timers


def timed(seconds='0.2'):
    return {'seconds':seconds,'started_utc':'2026-09-18T10:00:00.100000+00:00',
            'finished_utc':'2026-09-18T10:00:00.300000+00:00'}


class SupplementalControls(unittest.TestCase):
    def test_exact_tokens_nonfinite_and_unknowns(self):
        self.assertEqual(number('0.1')+number('0.2'),Decimal('0.3'))
        for value in (True,.1,'NaN','Infinity','-1','bad'):
            with self.assertRaises(ValueError):number(value)
        self.assertEqual(timers({'human_seconds':None,'child':[{'seconds':'0.1'}],'pixels':15}),
                         [{'field':'/child/0/seconds','seconds':'0.1'}])

    def test_temporal_nesting_requires_utc_and_order(self):
        outer={'started_utc':'2026-09-18T10:00:00Z','finished_utc':'2026-09-18T10:00:01+00:00'}
        self.assertTrue(contained(timed(),outer))
        inner=timed();inner['finished_utc']='2026-09-18T10:00:02+00:00'
        self.assertFalse(contained(inner,outer))
        inner=timed();inner['started_utc']='2026-09-18T10:00:00.100000+01:00'
        with self.assertRaises(ValueError):contained(inner,outer)

    def archive(self,root):
        archive=root/'archive.tar.gz';member='private/cached-synthetic-01/analysis/RESULTS.json'
        raw=json.dumps(timed()).encode()
        with tarfile.open(archive,'w:gz') as handle:
            info=tarfile.TarInfo(member);info.size=len(raw);handle.addfile(info,io.BytesIO(raw))
        manifest={'files':[{'path':member,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}],
                  'archive_sha256':sha(archive)}
        return archive,manifest,member

    def test_archive_identity_and_member_type_are_obligations(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive,manifest,member=self.archive(Path(temporary))
            self.assertEqual(archive_json(archive,manifest,member)['seconds'],'0.2')
            wrong=deepcopy(manifest);wrong['files'][0]['sha256']='0'*64
            with self.assertRaises(ValueError):archive_json(archive,wrong,member)
            with self.assertRaises(ValueError):archive_json(archive,manifest,'../outside')

    def test_whole_supplement_keeps_duration_classes_nonadditive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'inputs';source.mkdir();bindings=[]
            def add(name,role,value):
                path=source/name;path.parent.mkdir(parents=True,exist_ok=True);put(path,value)
                bindings.append({'path':name,'role':role,'bytes':path.stat().st_size,'sha256':sha(path)})
            add('probes.json','unwrapped_reader_attempts',{'attempts':[{'seconds':v,'state':'failed'} for v in ('0.1','0.2','0.3')]})
            add('view.json','unwrapped_physical_view',{'seconds':'0.4','state':'read'})
            add('public.json','published_snapshot_and_failed_launch',{'startup_failure':{
                'tool_wall_seconds':'0.4','secondary_result_view_tool_wall_seconds':'0.2'},'outer_seconds':'99'})
            owner={'stage':'cached-synthetic-01','started_utc':'2026-09-18T10:00:00Z',
                   'finished_utc':'2026-09-18T10:00:01Z','seconds':'1'}
            add('owner.json','owner_phase',owner)
            add('storage-owner.json','owner_phase',{**owner,'stage':'storage-recovery-01'})
            archive,manifest,member=self.archive(root)
            target=source/'private/storage-recovery-01/SYNTHETIC_OUTPUTS.tar.gz';target.parent.mkdir(parents=True)
            target.write_bytes(archive.read_bytes());bindings.append({'path':str(target.relative_to(source)),
                'role':'synthetic_archive','bytes':target.stat().st_size,'sha256':sha(target)})
            manifest.update(timed('0.05'))
            add('private/storage-recovery-01/COMPLETED.json','storage_recovery',manifest)
            frozen={'inputs':bindings,'implementation':[],'cutoff_utc':'2026-09-18T11:00:00Z'}
            put(root/'FREEZE.json',frozen);check(root,frozen);result=reconcile(root,frozen)
            self.assertEqual(result['additional_reader_duration_token_sum_seconds'],'1.0')
            self.assertEqual(result['failed_tool_duration_token_sum_seconds'],'0.6')
            self.assertEqual(result['new_outer_intervals'],[])
            self.assertTrue(all(r['added_to_outer_union'] is False for r in result['timers']))
            self.assertTrue(any(r['seconds']=='99' and r['accounting']=='published_snapshot_reference' for r in result['timers']))
            (source/'probes.json').write_text('{}')
            with self.assertRaises(ValueError):check(root,frozen)


if __name__=='__main__':unittest.main()
