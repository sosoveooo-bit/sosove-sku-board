import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from sku_board import backend, image_cancellation as cancel


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=patch.object(cancel,'_path',Path(self.tmp.name)/'cancel.json');self.path.start()
        self.records=patch.object(cancel,'_records',None);self.records.start()
        self.jobs=patch.object(backend,'_AI_IMAGE_JOBS',{});self.jobs.start()
        self.persist=patch.object(backend,'save_ai_image_jobs_locked');self.persist.start()
        self.cleanup=patch.object(backend,'delete_ai_image_job_files');self.cleanup.start()
        self.actor={'username':'fixture','role':'designer'};self.op='a'*32

    def tearDown(self):
        self.cleanup.stop();self.persist.stop();self.jobs.stop();self.records.stop();self.path.stop();self.tmp.cleanup()

    def job(self,status='queued'):
        job={'id':'AIJ-'+'A'*14,'owner':'fixture','actor':self.actor,'mode':'text','status':status,
             'payload':{'operationId':self.op},'files':[]}
        backend._AI_IMAGE_JOBS[job['id']]=job;return job

    def test_cancel_before_delayed_submission_survives_reload(self):
        backend.cancel_ai_image_operation({'operationId':self.op},self.actor)
        cancel._records=None
        self.assertTrue(cancel.is_cancelled('fixture',self.op))
        self.assertFalse(cancel.is_cancelled('other-user',self.op))
        with patch.object(backend,'start_ai_image_job_worker') as start:
            response=backend.start_ai_image_job('text',{'operationId':self.op},self.actor)
        self.assertTrue(response['cancelled']);start.assert_not_called()

    def test_queued_job_never_reaches_provider(self):
        job=self.job();backend.cancel_ai_image_operation({'jobIds':[job['id']]},self.actor)
        with patch.object(backend,'generate_ad_launch_ai_image') as provider:
            backend.run_ai_image_job(job['id'])
        provider.assert_not_called();self.assertEqual(job['status'],'cancelled')

    def test_cancelled_job_remains_terminal_after_reload(self):
        import json
        job=self.job();job['status']='cancelled';job['cancelRequested']=True
        path=Path(self.tmp.name)/'jobs.json';path.write_text(json.dumps({'jobs':{job['id']:job}}),encoding='utf-8')
        with patch.object(backend,'AI_IMAGE_JOBS_FILE',path):loaded=backend.load_ai_image_jobs()
        self.assertEqual(loaded[job['id']]['status'],'cancelled')
        self.assertTrue(loaded[job['id']]['cancelRequested'])

    def test_inflight_result_is_saved_after_cancel_request(self):
        job=self.job('running')
        def provider(*args):
            backend.cancel_ai_image_operation({'operationId':self.op},self.actor)
            return {'materials':[{'id':'finished-image'}]}
        with patch.object(backend,'generate_ad_launch_ai_image',side_effect=provider):backend.run_ai_image_job(job['id'])
        self.assertEqual(job['status'],'success');self.assertTrue(job['cancelRequested'])
        self.assertEqual(job['result']['materials'][0]['id'],'finished-image')

    def test_other_owner_rejected_before_any_cancellation(self):
        job=self.job();job['owner']='other-user'
        with self.assertRaisesRegex(ValueError,'无权'):
            backend.cancel_ai_image_operation({'operationId':self.op,'jobIds':[job['id']]},self.actor)
        self.assertFalse(cancel.is_cancelled('fixture',self.op));self.assertEqual(job['status'],'queued')

    def test_thread_pool_inherits_cancellation_and_blocks_next_post(self):
        entered=threading.Event();release=threading.Event();client=Mock()
        def child():entered.set();release.wait(2);return cancel.post(client,'fixture-endpoint')
        token=cancel.enter('fixture',self.op)
        try:
            with cancel.OperationExecutor(max_workers=1) as executor:
                result=executor.submit(child);self.assertTrue(entered.wait(1));cancel.cancel('fixture',self.op);release.set()
                with self.assertRaises(cancel.OperationCancelled):result.result(timeout=2)
        finally:cancel.leave(token)
        client.post.assert_not_called()

    def test_planning_response_reports_cancelled_and_blocks_retry(self):
        def planning():cancel.cancel('fixture',self.op);return {'ok':True,'suitePages':[]}
        result=backend.run_ai_operation({'operationId':self.op},self.actor,planning)
        self.assertTrue(result['cancelled'])
        token=cancel.enter('fixture',self.op)
        try:
            with patch.object(backend,'invoke_ai_director_chat_once') as invoke:
                with self.assertRaises(cancel.OperationCancelled):backend.invoke_ai_director_chat({'model':'fixture'},[])
            invoke.assert_not_called()
        finally:cancel.leave(token)


if __name__=='__main__':unittest.main()
