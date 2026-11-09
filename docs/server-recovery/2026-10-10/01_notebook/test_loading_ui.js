const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(path.join(__dirname,'../02_web_demo/index.html'),'utf8');
const nodes={};
for(const id of ['workspace','processingOverlay','processingTitle','processingDescription','workspaceTag','workspaceTitle','workspaceDescription','jalan','spin','hasil','modeData','dataHeadline','dataSupporting','task','sample','gambar','previewUpload','statusOcr','headline','supporting','ocrCandidates'])nodes[id]={style:{display:'block'},dataset:{},value:'input',files:[],hidden:true,textContent:'',innerHTML:'',disabled:false,attrs:{},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},replaceChildren(){},add(){},classList:{add(){},remove(){}}};
nodes.headline.value='';nodes.supporting.value='';nodes.task.value='task2_domain_sumber';const pending=[],alerts=[];
const context={document:{getElementById:id=>nodes[id]},AbortController,FormData,URL:{createObjectURL:()=> 'blob:preview',revokeObjectURL(){}},Option:function(){},alert:m=>alerts.push(m),fetch:()=>new Promise((resolve,reject)=>pending.push({resolve,reject})),tampil:()=>{nodes.hasil.style.display='block';context.setWorkspaceState('results');}};
vm.createContext(context);
vm.runInContext("let _ocrKe=0;let _ocrTerakhir={headline:'',pendukung:''};let textEditRev={headline:0,supporting:0};",context);
vm.runInContext(html.slice(html.indexOf('function _disuntingPengguna'),html.indexOf('let analysisSeq=')),context);
vm.runInContext(html.slice(html.indexOf('let analysisSeq='),html.indexOf('function tampil(d, modeData)')),context);
function jsonResponse(data){return {json:async()=>data}}
(async()=>{
 nodes.gambar.files=[new Blob(['first'])];const first=context.bacaOtomatis();assert.equal(nodes.workspace.dataset.state,'ocr');assert.equal(nodes.processingOverlay.hidden,false);assert.equal(nodes.jalan.disabled,true);assert(nodes.processingTitle.textContent.includes('teks'));
 await context.analisis();assert.equal(pending.length,1,'analysis blocked during OCR');
 nodes.gambar.files=[new Blob(['second'])];const second=context.bacaOtomatis();pending[0].resolve(jsonResponse({headline:'OLD'}));await first;assert.equal(nodes.processingOverlay.hidden,false);assert.equal(nodes.jalan.disabled,true);
 pending[1].resolve(jsonResponse({headline:'NEW',kandidat_headline:['NEW']}));await second;assert.equal(nodes.headline.value,'NEW');assert.equal(nodes.processingOverlay.hidden,true);assert.equal(nodes.jalan.disabled,false);assert.equal(nodes.workspace.attrs['aria-busy'],'false');
 const failed=context.bacaOtomatis();pending[2].reject(new Error('offline'));await failed;assert.equal(nodes.processingOverlay.hidden,true);assert.equal(nodes.jalan.disabled,false);assert(nodes.statusOcr.innerHTML.includes('manual'));
 const analysis=context.analisis();assert.equal(nodes.processingOverlay.hidden,false);assert(nodes.processingTitle.textContent.includes('menganalisis'));assert.equal(nodes.workspace.attrs['aria-busy'],'true');pending[3].resolve(jsonResponse({}));await analysis;assert.equal(nodes.processingOverlay.hidden,true);assert.equal(nodes.workspace.dataset.state,'results');
 const invalid=context.analisis();pending[4].resolve(jsonResponse({error:'failure'}));await invalid;assert.equal(nodes.processingOverlay.hidden,true);assert.equal(nodes.jalan.disabled,false);assert.equal(nodes.workspace.dataset.state,'ready');assert.equal(alerts.length,1);
 console.log('OCR/analysis spinner lifecycle, blocking, stale upload response, network failure and server failure verified.');
})().catch(e=>{console.error(e);process.exitCode=1});
