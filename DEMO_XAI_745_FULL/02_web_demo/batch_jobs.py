"""Persistent serial batch jobs with review/retry and independent item errors."""
import csv, io, json, queue, re, threading, traceback, uuid
from pathlib import Path

_PATH = re.compile(r"(?<![\w.])(?:[A-Za-z]:\\|/)[^\s'\"]+")
_ID_JOB = re.compile(r"[0-9a-f]{32}")


def saring_path(teks):
    """Ganti path absolut server di dalam teks dengan nama berkasnya saja."""
    return _PATH.sub(lambda m: re.split(r"[\\/]", m.group(0))[-1], str(teks))


def pesan_gagal(e):
    """Pesan gagal item untuk pengguna/ekspor: tanpa path absolut server."""
    if type(e).__name__ == "UnidentifiedImageError":
        return "Gambar tidak terbaca: format berkas tidak dikenali"
    if type(e).__name__ == "InputTidakSah":
        # Penolakan masukan dari app.py: pesannya sudah ramah pengguna.
        return saring_path(e)
    return f"{type(e).__name__}: {saring_path(e)}"


class JobTidakDitemukan(LookupError):
    """Id job tidak sah atau manifest-nya tidak ada."""


class AntreanPenuh(RuntimeError):
    """Jumlah job yang berjalan/antre sudah mencapai batas."""


# Awalan sel yang ditafsirkan sebagai rumus oleh Excel/LibreOffice/Sheets.
# Dicek setelah spasi di depan dibuang; tab/CR di depan juga dianggap berbahaya.
_AWALAN_RUMUS = ("=", "+", "-", "@", "＝", "＋", "－", "＠")


def sel_csv_aman(v):
    if isinstance(v, str) and (v.startswith(("\t", "\r")) or v.lstrip().startswith(_AWALAN_RUMUS)):
        return "'" + v
    return v


class _Antrean:
    """Satu worker serial di thread daemon.

    Pengganti ThreadPoolExecutor: worker executor di-join saat interpreter
    keluar, sehingga Ctrl+C pada server menunggu seluruh job batch selesai.
    Thread daemon ikut berhenti; manifest selalu ditulis atomik, dan item
    yang tertinggal berstatus "running" ditandai "interrupted" saat start.
    """

    def __init__(self, fungsi):
        self._q = queue.Queue()
        self._fungsi = fungsi
        self._thread = threading.Thread(target=self._loop, name="batch-worker", daemon=True)
        self._thread.start()

    def submit(self, *args):
        self._q.put(args)

    def _loop(self):
        while True:
            args = self._q.get()
            if args is None:
                return
            try:
                self._fungsi(*args)
            except Exception:
                traceback.print_exc()

    def shutdown(self, wait=True):
        self._q.put(None)
        if wait:
            self._thread.join()


class BatchJobs:
    def __init__(self, root, runner, max_aktif=None):
        self.root=Path(root);self.root.mkdir(exist_ok=True)
        self.runner=runner;self.lock=threading.RLock();self.pool=_Antrean(self.run)
        self.active=set();self.max_aktif=max_aktif
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
        if not isinstance(id,str) or not _ID_JOB.fullmatch(id):raise JobTidakDitemukan("job tidak ditemukan")
        try:return json.loads((self.root/id/"manifest.json").read_text(encoding='utf-8'))
        except FileNotFoundError:raise JobTidakDitemukan("job tidak ditemukan") from None
    def create(self,items,task,method):
        id=uuid.uuid4().hex;(self.root/id).mkdir()
        j={"id":id,"status":"queued","task":task,"method":method,"items":items}
        self.save(j);return j
    def cek_kapasitas(self,id=None):
        """Lempar AntreanPenuh bila job baru/lanjutan akan melebihi batas."""
        with self.lock:
            if self.max_aktif is not None and id not in self.active and len(self.active)>=self.max_aktif:
                raise AntreanPenuh(f"Sudah ada {len(self.active)} job batch yang berjalan/antre "
                                   f"(maksimal {self.max_aktif}). Tunggu salah satunya selesai.")
    def start(self,id):
        with self.lock:
            if id in self.active:return
            self.active.add(id);self.pool.submit(id)
    @staticmethod
    def _status_akhir(items):
        if any(x["status"]=="needs_review" for x in items):return "needs_review"
        if items and all(x["status"]=="failed" for x in items):return "failed"
        return "complete"
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
                except Exception as e:
                    print(f"[batch {id}] item {index} gagal:\n{traceback.format_exc()}", flush=True)
                    item.update(status="failed",error=pesan_gagal(e))
                with self.lock:
                    j=self.get(id);j["items"][index]=item;self.save(j)
            with self.lock:
                j=self.get(id);j["status"]=self._status_akhir(j["items"]);self.save(j)
        finally:
            with self.lock:self.active.discard(id)
    @staticmethod
    def _antre_ulang(x):
        # Hasil/galat percobaan sebelumnya tidak boleh ikut terbawa ke percobaan baru.
        x.pop("error",None);x.pop("result",None);x["status"]="queued"
    def review(self,id,index,headline,supporting):
        with self.lock:
            j=self.get(id)
            if id in self.active:raise ValueError("Tunggu job selesai sebelum koreksi/retry")
            x=j["items"][index]
            boleh=x["status"]=="needs_review" or (x["status"]=="failed" and x.get("input_file"))
            if not boleh:
                raise ValueError("Item ini tidak perlu ditinjau: koreksi teks hanya untuk item unggahan "
                                 "yang menunggu pemeriksaan atau yang gagal")
            if not headline.strip():raise ValueError("Headline wajib diisi")
            self.cek_kapasitas(id)
            self._antre_ulang(x);x.update(headline=headline.strip(),supporting=supporting,reviewed=True)
            j["status"]="queued";self.save(j)
            self.start(id)
    def resume(self,id):
        with self.lock:
            j=self.get(id)
            if id in self.active:return
            self.cek_kapasitas(id)
            for x in j["items"]:
                if x["status"] in ("failed","running"):self._antre_ulang(x)
            j["status"]="queued";self.save(j)
            self.start(id)
    def export_csv(self,j):
        out=io.StringIO();w=csv.writer(out)
        w.writerow(["item","status","headline","task","class","score","protocol","method","error","model_version","score_kind","task_evaluation_mode"])
        for x in j["items"]:
            r=x.get("result",{});p=r.get("prediksi",{}).get(j["task"],{})
            row=[x["name"],x["status"],r.get("headline",x.get("headline","")),j["task"],p.get("prediksi",""),p.get("probabilitas",""),r.get("mode",""),r.get("metode_atribusi",""),x.get("error",""),p.get("model_version","baseline-mtl-v1"),p.get("score_kind","softmax_uncalibrated"),p.get("evaluation_mode",r.get("mode",""))]
            w.writerow([sel_csv_aman(v) for v in row])
        return out.getvalue()
