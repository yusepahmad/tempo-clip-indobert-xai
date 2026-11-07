"""Verifikasi HTTP model nyata: tiga task, input manual, batch + ekspor (5 Okt 2026).

PERINGATAN: folder keluaran relatif terhadap direktori kerja
(`DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3`). Bila dijalankan dari
folder induk paket, skrip ini MENIMPA bukti historis `task1_issue.json`,
`task2_domain_sumber.json`, `task3_primary_entity_type.json`,
`batch_export.{json,csv}` dan `http_verification.json`. Untuk verifikasi ulang,
jalankan dari folder staging terpisah seperti di docs/HANDOFF_SERVER.md
(`cd "$STAGE" && TEMPO_DEMO_URL=... venv/bin/python 01_notebook/verify_week3_http.py`).
Server dibaca dari TEMPO_DEMO_URL (default http://127.0.0.1:7861); juga
membuat satu job batch baru di `_jobs` server.
"""
import requests,json,time,os
from pathlib import Path
base=os.environ.get("TEMPO_DEMO_URL","http://127.0.0.1:7861")
out=Path("DEMO_XAI_745_FULL/04_hasil_eksperimen/revisi_week3");out.mkdir(exist_ok=True)
samples=requests.get(base+"/api/samples").json();sample=samples[0]
catalog=requests.get(base+"/api/catalog").json();assert [len(x["classes"]) for x in catalog]==[10,7,8]
results=[]
for task in ("task2_domain_sumber","task1_issue","task3_primary_entity_type"):
 data={"sample_id":sample["sample_id"],"task":task,"metode_atribusi":"occlusion"}
 if task=="task1_issue":data.update(headline="HEADLINE FINAL DIEDIT",supporting="TEKS MANUAL")
 response=requests.post(base+"/api/analisis",data=data,timeout=240);assert response.ok,response.text
 r=response.json();assert r["task_id"]==task and r["kesimpulan"]["task_id"]==task
 if task=="task1_issue":assert r["headline"]=="HEADLINE FINAL DIEDIT" and r["supporting"]=="TEKS MANUAL"
 assert all(x.get("task_id",task)==task for x in r["evidence"])
 results.append({"task":task,"analysis_id":r["analysis_id"],"headline":r["headline"],"strategy":r["kesimpulan"]["strategi"],"seconds":r["durasi_detik"]})
 (out/(task+".json")).write_text(json.dumps(r,ensure_ascii=False,indent=2));print(results[-1],flush=True)
# Dataset plus broken upload: one error must not stop the dataset result.
r=requests.post(base+"/api/batch",data={"sample_ids":json.dumps([sample["sample_id"]]),"task":"task2_domain_sumber"},files=[("gambar",("broken.png",b"not an image","image/png"))]);assert r.status_code==202,r.text
id=r.json()["id"]
for _ in range(120):
 j=requests.get(base+"/api/batch/"+id).json()
 if j["status"] not in ("running","queued"):break
 time.sleep(2)
assert [x["status"] for x in j["items"]]==["success","failed"],j
assert "in-sample" in j["items"][0]["result"]["mode"]
for kind in ("json","csv"):
 r=requests.get(base+"/api/batch/"+id+"/export/"+kind);assert r.ok;(out/("batch_export."+kind)).write_text(r.text)
for v in j["items"][0]["result"]["heatmap_per_task"].values():assert requests.get(base+v["url"]).ok
(out/"http_verification.json").write_text(json.dumps({"status":"success","catalog_sizes":[10,7,8],"single":results,"batch_id":id,"batch_statuses":[x["status"] for x in j["items"]]},indent=2));print("HTTP REAL MODEL VERIFIED",flush=True)
