from extract import *
def main():
    torch.set_num_threads(8);f=json.loads((OUT/'features_manifest.json').read_text());z=np.load(OUT/'features.npz');df=pd.read_csv(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    assert f['source_sha256']==sha(Path(__file__).with_name('extract.py')) and f['feature_sha256']==sha(OUT/'features.npz') and f['csv_sha256']==sha(ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv')
    assert f['labels_used'] is False and z['sample_ids'].tolist()==df.sample_id.tolist()
    snapshot=Path(snapshot_download('indobenchmark/indobert-base-p1',revision=f['model_snapshot'],local_files_only=True))
    for name,digest in f['model_hashes'].items():assert sha(snapshot/name)==digest
    old=np.load(ROOT/'03_data/fitur_clip_indobert_740.npz')['txt'];assert np.abs(old-z['cls']).max()<2e-5
    for name in ['cls','mean','last4']:assert z[name].shape==(740,768) and np.isfinite(z[name]).all() and np.allclose(np.linalg.norm(z[name],axis=1),1,atol=2e-5)
    tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);m=AutoModel.from_pretrained(snapshot,local_files_only=True).eval();checks=[]
    for i in [0,147,295,443,591,739]:
        row=df.iloc[i];enc=tok(f'{row.headline_verified} [SEP] {row.supporting_text_verified}'.strip(),return_tensors='pt',truncation=True,max_length=128,padding='max_length')
        ids=enc['input_ids'][0].tolist();selected=[j for j,t in enumerate(ids) if int(enc['attention_mask'][0,j]) and t not in tok.all_special_ids]
        with torch.inference_mode():
            out=m(**enc,output_hidden_states=True)
            mean=out.last_hidden_state[0,selected].mean(dim=0)
            last4=torch.stack([v[0,selected].mean(dim=0) for v in out.hidden_states[-4:]]).mean(dim=0)
            for name,v in [('mean',mean),('last4',last4)]:
                v=torch.nn.functional.normalize(v,p=2,dim=0).numpy();err=float(np.abs(v-z[name][i]).max());assert err<2e-5;checks.append(dict(index=i,view=name,max_abs=err))
    report=dict(status='passed',samples=740,cls_all740=True,model_source_data_hashes=True,norm_order=True,sampled_token_reproduction=checks)
    (OUT/'feature_verification.json').write_text(json.dumps(report,indent=2)+'\n');print('FEATURE AUDIT PASSED',flush=True)
if __name__=='__main__':main()
