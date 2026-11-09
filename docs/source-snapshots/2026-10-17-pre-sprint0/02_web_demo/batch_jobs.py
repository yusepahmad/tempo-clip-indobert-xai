"""Persistent serial batch jobs with review/retry and independent item errors."""
import csv, io, json, threading, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

class BatchJobs:
    def __init__(self, root, runner):
        self.root=Path(root);self.root.mkdir(exist_ok=True)
        self.runner=runner;self.lock=threading.RLock();self.pool=ThreadPoolExecutor(max_workers=1)
        self.active=set()
        for p in self.root.glob("*/manifest.json"):
            j=json.loads(p.read_text(encoding='utf-8'))
            if j["status"] in ("queued","running"):
                j["status"]="interrupted"
                for x in j["items"]:
                    if x["status"]=="running":x["status"]="queued"
                self.save(j)
    def save(self,j):
        p=self.root/j["id"]/"manifest.json";tmp=p.with_suffix(".tmp")
        tmp.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
    def get(self,id):
        if not id.isalnum():raise ValueError("job id tidak sah")
        return json.loads((self.root/id/"manifest.json").read_text(encoding='utf-8'))
    def create(self,items,task,method):
        id=uuid.uuid4().hex;(self.root/id).mkdir()
        j={"id":id,"status":"queued","task":task,"method":method,"items":items}
        self.save(j);return j
    def start(self,id):
        with self.lock:
            if id in self.active:return
            self.active.add(id);self.pool.submit(self.run,id)
    def run(self,id):
        try:
            with self.lock:j=self.get(id);j["status"]="running";self.save(j)
            for index in range(len(j["items"])):
                with self.lock:
                    j=self.get(id);item=j["items"][index]
                    if item["status"]!="queued":continue
                    item["status"]="running";self.save(j)
                try:
                    result=self.runner(j,item,self.root/id)
                    item.update(result)
                except Exception as e:item.update(status="failed",error=f"{type(e).__name__}: {e}")
                with self.lock:
                    j=self.get(id);j["items"][index]=item;self.save(j)
            with self.lock:
                j=self.get(id);j["status"]="needs_review" if any(x["status"]=="needs_review" for x in j["items"]) else "complete";self.save(j)
        finally:
            with self.lock:self.active.discard(id)
    def review(self,id,index,headline,supporting):
        with self.lock:
            j=self.get(id)
            if id in self.active:raise ValueError("Tunggu job selesai sebelum koreksi/retry")
            x=j["items"][index]
            if not headline.strip():raise ValueError("Headline wajib diisi")
            x.update(headline=headline.strip(),supporting=supporting,status="queued",reviewed=True)
            x.pop("error",None);self.save(j)
        self.start(id)
    def resume(self,id):
        with self.lock:
            j=self.get(id)
            if id in self.active:return
            for x in j["items"]:
                if x["status"] in ("failed","running"):x["status"]="queued"
            self.save(j)
        self.start(id)
    def export_csv(self,j):
        out=io.StringIO();w=csv.writer(out)
        w.writerow(["item","status","headline","task","class","score","protocol","method","error"])
        for x in j["items"]:
            r=x.get("result",{});p=r.get("prediksi",{}).get(j["task"],{})
            row=[x["name"],x["status"],r.get("headline",x.get("headline","")),j["task"],p.get("prediksi",""),p.get("probabilitas",""),r.get("mode",""),r.get("metode_atribusi",""),x.get("error","")]
            w.writerow([("'"+v if isinstance(v,str) and v.startswith(("=","+","-","@")) else v) for v in row])
        return out.getvalue()
