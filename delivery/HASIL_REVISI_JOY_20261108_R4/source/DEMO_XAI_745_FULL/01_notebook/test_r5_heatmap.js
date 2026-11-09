const vm=require('vm'),assert=require('assert'),fs=require('fs'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'../02_web_demo/index.html'),'utf8');
const node=()=>({style:{display:'block'},textContent:'',src:'stale.png',removeAttribute(a){if(a==='src')this.src='';}});
const nodes={};for(const id of ['imgHeat','capHeat','imgHeatTask','capHeatTask','judulHeatTask'])nodes[id]=node();
const context={document:{getElementById:id=>nodes[id]}};vm.createContext(context);
vm.runInContext(html.slice(html.indexOf('function pilihPetaPanas('),html.indexOf('function tampil(d, modeData)')),context);
const render=d=>vm.runInContext('renderPetaPanas',context)(d);
const base={heatmap_padu_url:'/api/heatmap/cam_a_padu',heatmap_url:'/api/heatmap/cam_a',task_xai:'Domain sumber metafora',kelas_untuk_atribusi:'PERMAINAN_KONTES',kelas_untuk_atribusi_tampil:'Permainan & Kontes'};

// Peta utama = gabungan; bukti task pilihan terpisah dengan task/kelas yang benar.
render(base);
assert.equal(nodes.imgHeat.src,base.heatmap_padu_url);assert.equal(nodes.imgHeat.style.display,'block');
assert.match(nodes.capHeat.textContent,/gabungan tiga task/);assert.match(nodes.capHeat.textContent,/bukan dasar atribusi kata/);
assert.equal(nodes.imgHeatTask.src,base.heatmap_url);
assert.equal(nodes.judulHeatTask.textContent,'Bukti task pilihan: Domain sumber metafora — kelas Permainan & Kontes');
assert.doesNotMatch(nodes.capHeatTask.textContent,/gabungan/);

// Pergantian task: label task berganti, peta utama tetap gabungan.
const t1={...base,heatmap_padu_url:'/api/heatmap/cam_b_padu',heatmap_url:'/api/heatmap/cam_b',task_xai:'Isu utama',kelas_untuk_atribusi:'law_and_justice',kelas_untuk_atribusi_tampil:'Hukum & Peradilan'};
render(t1);
assert.equal(nodes.imgHeat.src,t1.heatmap_padu_url);assert.equal(nodes.imgHeatTask.src,t1.heatmap_url);
assert.match(nodes.judulHeatTask.textContent,/Isu utama — kelas Hukum & Peradilan/);

// Peta gabungan hilang: tidak boleh jatuh kembali ke peta task pilihan berlabel gabungan.
render({...base,heatmap_padu_url:null});
assert.equal(nodes.imgHeat.style.display,'none');assert.equal(nodes.imgHeat.src,'');
assert.notEqual(nodes.imgHeat.src,base.heatmap_url);
assert.match(nodes.capHeat.textContent,/tidak dapat dihitung/);
assert.equal(nodes.imgHeatTask.src,base.heatmap_url);

// Peta task pilihan hilang: gabungan tetap tampil, task diberi pesan.
render({...base,heatmap_url:null});
assert.equal(nodes.imgHeat.src,base.heatmap_padu_url);
assert.equal(nodes.imgHeatTask.style.display,'none');assert.match(nodes.capHeatTask.textContent,/tidak dapat dihitung/);

// Renderer lama tidak boleh kembali; tampil memakai renderer R5.
assert.ok(!html.includes('const utama = d.heatmap_url'));
const tampilSrc=html.slice(html.indexOf('function tampil(d, modeData)'));
assert.ok(tampilSrc.includes('renderPetaPanas(plain)'));
assert.equal((html.match(/id="imgHeatTask"/g)||[]).length,1);
console.log('R5 verified: main map = combined three-task map; selected-task map separate with task/class label; no fallback mislabel; task switch updates labels.');
