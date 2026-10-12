"""Offline regression tests: no model or network calls."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import rerun


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.panel,cls.order,cls.config = rerun.inputs(),rerun.models(),rerun.schedule(),rerun.protocol()
        cls.model = next(iter(cls.panel))
        cls.row = next(rerun.read_rows(rerun.ROOT/'results/responses'/f'{cls.model}.jsonl.gz'))

    def test_prompt_and_sampling_match_recorded_request(self):
        row=self.row
        payload=rerun.request(self.data[(row['dataset'],row['query_id'])],row['condition_id'],row['seed'],self.panel[self.model],self.config)
        self.assertEqual(rerun.sha_text(payload['prompt']),row['prompt_sha256'])
        self.assertEqual(payload['options'],dict(temperature=0.1,seed=row['seed'],num_predict=80,num_ctx=4096))
        self.assertFalse(payload['think'])

    def test_dry_run_all_models_never_opens_network(self):
        with patch.object(sys,'argv',['rerun.py','--model','all','--limit','3']), \
             patch.object(rerun.urllib.request,'urlopen',side_effect=AssertionError('Network called')), \
             patch.object(rerun,'write_json') as write, contextlib.redirect_stdout(io.StringIO()):
            rerun.main()
            self.assertEqual(write.call_args.args[1]['total_requests'],24)
            self.assertEqual(write.call_args.args[1]['network_calls'],0)

    def test_resume_rejects_duplicate_changed_prompt_and_changed_response(self):
        valid=rerun.validate_resume([self.row],self.data,self.panel,self.order,self.config,self.model)
        self.assertEqual(len(valid),1)
        for rows in [[self.row,self.row],[dict(self.row,prompt_sha256='bad')],[dict(self.row,response='changed')],
                     [dict(self.row,model_digest='bad')],[dict(self.row,seed=999)]]:
            with self.assertRaises(ValueError):
                rerun.validate_resume(rows,self.data,self.panel,self.order,self.config,self.model)

    def test_invalid_limit_and_remote_endpoint_fail_before_network(self):
        for extra in [['--limit','0'],['--endpoint','https://example.com']]:
            with patch.object(sys,'argv',['rerun.py','--model',self.model]+extra), \
                 patch.object(rerun.urllib.request,'urlopen',side_effect=AssertionError('Network called')), \
                 contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                rerun.main()


if __name__=='__main__':
    unittest.main()
