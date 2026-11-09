"""CPU checks: frozen derivation, exact prompts, truthful readiness, no fallback."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
sys.path.insert(0, str(APP/'02_web_demo'))
from micro_e14_engine import MicroE14Engine, build_prompt, E14Unavailable, PACKAGE, TASKS


class DeploymentTests(unittest.TestCase):
    def test_prompts_match_all_2220_historical_audits(self):
        engine = MicroE14Engine()
        frame = engine.df.set_index('sample_id')
        path = APP/'04_hasil_eksperimen/next_research_20261017/06_micro_f1/MICRO_E14_joint_qlora_oof/fold5/input_audit.jsonl'
        audits = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(audits), 2220)
        for row in audits:
            sample = frame.loc[row['sample_id']]
            prompt = build_prompt(engine.contract, row['task'], sample.headline_verified,
                                  sample.supporting_text_verified, engine.contexts[row['sample_id']])
            self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), row['prompt_sha256'])

    def test_refit_loop_identical_to_cv(self):
        def loop(path):
            tree = ast.parse(path.read_text())
            main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
            return next(ast.dump(n, include_attributes=False) for n in main.body if isinstance(n, ast.For)
                        and isinstance(n.target, ast.Name) and n.target.id == 'epoch'
                        and any(isinstance(m, ast.Name) and m.id == 'refit_history' for m in ast.walk(n)))
        self.assertEqual(loop(HERE/'deployment_worker.py'), loop(HERE.parent/'kaggle_micro_e14/worker.py'))

    def test_no_fake_eval_or_inner_train(self):
        source = (HERE/'deployment_worker.py').read_text()
        self.assertNotIn('f1_score(truth', source)
        self.assertNotIn('train_test_split(train', source)
        self.assertIn('train = np.arange(len(frame))', source)
        self.assertIn('PeftModel.from_pretrained', source)
        protocol = json.loads((HERE/'deployment_protocol.json').read_text())
        self.assertEqual(protocol['inner_selected_epochs'], [3,1,3,2,3])
        self.assertEqual(protocol['epochs'], 3)

    def test_no_checkpoint_never_ready(self):
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            for name in ('contract.json','visual_context.json'):
                shutil.copyfile(PACKAGE/name, Path(folder)/name)
            engine = MicroE14Engine(folder)
            self.assertFalse(engine.description()['ready'])
            self.assertFalse(engine.description()['capabilities']['visual_xai'])
            with self.assertRaises(E14Unavailable):
                engine.predict_image(None, 'test', '', None)

    def test_no_upload_or_prediction_cache(self):
        engine = MicroE14Engine()
        engine.ready = True  # Proves rejection before any GPU access.
        with self.assertRaisesRegex(E14Unavailable, 'Unggahan baru'):
            engine.predict_image(None, 'test', '', None)
        source = (APP/'02_web_demo/micro_e14_engine.py').read_text()
        self.assertNotIn('predictions.csv', source)
        self.assertNotIn('MTLDeliveryEngine', source)


if __name__ == '__main__':
    unittest.main()
