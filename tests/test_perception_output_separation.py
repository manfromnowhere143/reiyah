"""Filesystem aliases must not cross the staged evidence/output boundary."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_binding as binding, perception_admission as admission
from tools import perception_assistance as assistance, perception_rehearsal as rehearsal
from tools import perception_operands as operands, perception_reviewed_operands as reviewed
from tools.perception_decision.contract import Invalid
from tools.perception_observation import package
from tests.test_perception_observation import fixture, tree
from tests.test_perception_reviewed_operands import prepared_inputs


class OutputSeparationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)

    def prepared(self,name):
        root=self.root/name;root.mkdir();inputs=prepared_inputs(root)
        request=json.loads(inputs['binding_request'].read_bytes())
        return root,inputs,Path(request['package']['path']),request['package']['seal_sha256']

    def case_alias(self,path):
        alias=path.with_name(path.name.upper())
        if not alias.exists() or not alias.samefile(path):
            self.skipTest('Filesystem does not resolve this case alias')
        return alias

    def workflows(self,inputs):
        req,sha=inputs['binding_request'],inputs['binding_request_sha256']
        return {
            'binding':(binding,'build','BINDING_PRIVATE_OUTPUT',lambda out:binding.run(req,sha,out)),
            'admission':(admission,'build','ADMISSION_PRIVATE_OUTPUT',lambda out:admission.run(inputs['admission_request'],inputs['admission_request_sha256'],out)),
            'rehearsal':(rehearsal,'materialize','REHEARSAL_OUTPUT',lambda out:rehearsal.run(req,sha,'c'*32,out)),
            'assistance':(assistance,'materialize','ASSISTANCE_OUTPUT',lambda out:assistance.run(req,sha,'configuration-2',out)),
            'operands':(operands,'materialize','OPERANDS_OUTPUT',lambda out:operands.run(req,sha,inputs['assistance'],inputs['preparation_sha256'],out)),
            'reviewed':(reviewed,'materialize','REVIEWED_OUTPUT',lambda out:reviewed.run(out,**inputs))}

    def reject(self,code,fn):
        with self.assertRaises(Invalid) as caught:fn()
        self.assertEqual(caught.exception.code,code)

    def test_case_alias_does_not_add_private_material_to_observations(self):
        for name in ('binding','admission','rehearsal','assistance','operands','reviewed'):
            with self.subTest(workflow=name):
                root,inputs,evidence,seal=self.prepared(name)
                output=self.case_alias(evidence)/'private-output'
                _,_,code,run=self.workflows(inputs)[name]
                before=tree(evidence);package.verify(evidence,seal)
                self.reject(code,lambda:run(output))
                self.assertFalse(output.exists());self.assertEqual(tree(evidence),before)
                package.verify(evidence,seal)

    def test_case_alias_does_not_add_outputs_to_assistance_inputs(self):
        for name in ('operands','reviewed'):
            with self.subTest(workflow=name):
                root,inputs,evidence,seal=self.prepared(name)
                target=inputs['assistance'];before=tree(target)
                output=self.case_alias(target)/'private-output'
                _,_,code,run=self.workflows(inputs)[name]
                self.reject(code,lambda:run(output))
                self.assertFalse(output.exists());self.assertEqual(tree(target),before)
                operands.load_assistance(target,inputs['preparation_sha256'],inputs['binding_request_sha256'])
                package.verify(evidence,seal)

    def test_code_directory_alias_is_rejected_before_materialization(self):
        root,inputs,evidence,seal=self.prepared('code-guard')
        for name in ('rehearsal','assistance','operands','reviewed'):
            with self.subTest(workflow=name):
                module,method,code,run=self.workflows(inputs)[name]
                output=self.case_alias(module.ROOT)/('private-output-control-'+name)
                self.assertFalse(output.exists())
                with patch.object(module,method,side_effect=AssertionError('Guard allowed materialization')):
                    self.reject(code,lambda:run(output))
                self.assertFalse(output.exists())
        package.verify(evidence,seal)

    def test_parent_symlink_retargeting_keeps_writes_at_the_selected_private_destination(self):
        for name in ('binding','admission','rehearsal','assistance','operands','reviewed'):
            with self.subTest(workflow=name):
                root,inputs,evidence,seal=self.prepared(name)
                private=root/'package-private';private.mkdir()
                alias=root/'output-parent';alias.symlink_to(private,target_is_directory=True)
                module,method,_,run=self.workflows(inputs)[name];original=getattr(module,method)
                def retarget(*args,**kwargs):
                    result=original(*args,**kwargs)
                    alias.unlink();alias.symlink_to(evidence,target_is_directory=True)
                    return result
                before=tree(evidence)
                with patch.object(module,method,side_effect=retarget):run(alias/'private-output')
                self.assertTrue((private/'private-output').exists())
                self.assertFalse((evidence/'private-output').exists())
                self.assertEqual(tree(evidence),before);package.verify(evidence,seal)

    def test_new_package_never_seals_private_custody_through_a_case_alias(self):
        probe=self.root/'probe';probe.mkdir();self.case_alias(probe)
        for parent in ('root','assets'):
            with self.subTest(parent=parent):
                root=self.root/parent;root.mkdir();request=fixture(root);output=root/'observations'
                destination=output.with_name('OBSERVATIONS')
                if parent=='assets':destination=destination/'ASSETS'
                private=destination/'private-custody.json'
                self.reject('OBS_CUSTODY',lambda:package.build(request,output,private))
                self.assertFalse(private.exists());self.assertFalse((output/'SEAL.json').exists())
                self.assertEqual(tree(output),{})
                # A failed new preparation may retain empty partial directories;
                # it must contain neither disclosed payloads nor private custody.


if __name__=='__main__':unittest.main()
