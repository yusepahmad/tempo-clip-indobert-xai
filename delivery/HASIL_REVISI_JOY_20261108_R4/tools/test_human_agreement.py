import tempfile
from pathlib import Path
import json
import unittest
import numpy as np
import pandas as pd
from evaluate import TASKS
from human_agreement import annotation,icc_absolute,xai


class HumanAgreementTests(unittest.TestCase):
    def test_blank_templates_do_not_generate_kappa(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);data=pd.DataFrame({'sample_id':['one','two'],**{t:['',''] for t in TASKS}})
            data.to_csv(p/'a.csv',index=False);data.to_csv(p/'b.csv',index=False)
            (p/'protocol.json').write_text(json.dumps(dict(sample_ids=['one','two'],labels={t:['x','y'] for t in TASKS})))
            with self.assertRaises(ValueError):annotation(p/'a.csv',p/'b.csv',p/'protocol.json')

    def test_perfect_known_labels_and_mismatch_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);data=pd.DataFrame({'sample_id':['one','two'],**{t:['x','y'] for t in TASKS}})
            data.to_csv(p/'a.csv',index=False);data.iloc[::-1].to_csv(p/'b.csv',index=False)
            (p/'protocol.json').write_text(json.dumps(dict(sample_ids=['one','two'],labels={t:['x','y'] for t in TASKS})))
            result=annotation(p/'a.csv',p/'b.csv',p/'protocol.json')
            self.assertTrue(all(r['cohen_kappa']==1 for r in result['tasks']))
            data.assign(sample_id=['one','other']).to_csv(p/'b.csv',index=False)
            with self.assertRaises(ValueError):annotation(p/'a.csv',p/'b.csv',p/'protocol.json')

    def test_icc_perfect_raters_and_missing_rejection(self):
        matrix=np.repeat(np.array([[1.],[2.],[4.],[5.]]),5,axis=1)
        self.assertAlmostEqual(icc_absolute(matrix),1.)
        with self.assertRaises(ValueError):icc_absolute(matrix[:,:4])
        matrix[0,0]=np.nan
        with self.assertRaises(ValueError):icc_absolute(matrix)

    def test_xai_blank_or_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'ratings.csv'
            pd.DataFrame([dict(item_id='a',rater_id='r1',dimension='clarity',score='')]).to_csv(p,index=False)
            with self.assertRaises(ValueError):xai(p)

    def test_prespecified_xai_keys_and_integer_scores_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rows=[]
            for item,base in [('one',1),('two',3),('three',4)]:
                for rater in range(5):
                    rows.append(dict(item_id=item,rater_id=f'R{rater}',dimension='clarity',score=base))
            data=pd.DataFrame(rows);template=root/'template.csv';path=root/'ratings.csv'
            data.assign(score='').to_csv(template,index=False);data.to_csv(path,index=False)
            self.assertEqual(xai(path,template)['dimensions'][0]['raters'],5)
            data.iloc[:-1].to_csv(path,index=False)
            with self.assertRaises(ValueError):xai(path,template)
            data['score']=data['score'].astype(float);data.loc[0,'score']=1.5;data.to_csv(path,index=False)
            with self.assertRaises(ValueError):xai(path,template)


if __name__=='__main__':unittest.main()
