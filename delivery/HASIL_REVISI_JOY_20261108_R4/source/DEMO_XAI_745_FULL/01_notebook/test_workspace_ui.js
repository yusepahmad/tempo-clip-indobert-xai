const assert=require('assert'),vm=require('vm'),fs=require('fs'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'../02_web_demo/index.html'),'utf8');
function node(id,dataset={}){return {id,dataset,hidden:false,attrs:{},handlers:{},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},getAttribute(k){return this.attrs[k]},focus(){this.focused=true},addEventListener(k,fn){this.handlers[k]=fn}}}
const views=['analisis','batch','panduan'].map(id=>node(id));
const links=views.map(v=>node('',{viewLink:v.id}));
const panels={},tabs=['ringkasan','visual','teks','sumber','verifikasi'].map(key=>{const tab=node('result-tab-'+key,{resultTab:key});tab.attrs['aria-controls']='result-panel-'+key;panels[tab.attrs['aria-controls']]=node(tab.attrs['aria-controls']);return tab});
const window={addEventListener(k,fn){this[k]=fn}},location={hash:'#analisis'};
const context={Array,document:{querySelectorAll(sel){return {'.app-view':views,'[data-view-link]':links,'[data-result-tab]':tabs}[sel]},getElementById(id){return panels[id]}},window,location};
vm.createContext(context);vm.runInContext(html.slice(html.indexOf('// Workspace tabs and views.'),html.lastIndexOf('</script>')),context);
function checkView(id){assert.deepEqual(views.filter(x=>!x.hidden).map(x=>x.id),[id]);assert.deepEqual(links.filter(x=>x.attrs['aria-current']==='page').map(x=>x.dataset.viewLink),[id])}
function checkTab(key){assert.deepEqual(tabs.filter(x=>x.attrs['aria-selected']==='true').map(x=>x.dataset.resultTab),[key]);assert.deepEqual(Object.values(panels).filter(x=>!x.hidden).map(x=>x.id),['result-panel-'+key]);assert.equal(tabs.filter(x=>x.tabIndex===0).length,1)}
checkView('analisis');location.hash='#batch';window.hashchange();checkView('batch');location.hash='#panduan';window.hashchange();checkView('panduan');location.hash='#unknown';window.hashchange();checkView('analisis');
tabs[1].handlers.click();checkTab('visual');let prevented=false;tabs[1].handlers.keydown({key:'ArrowRight',preventDefault(){prevented=true}});assert(prevented);checkTab('teks');assert(tabs[2].focused);tabs[0].handlers.keydown({key:'ArrowLeft',preventDefault(){}});checkTab('verifikasi');tabs[4].handlers.keydown({key:'Home',preventDefault(){}});checkTab('ringkasan');tabs[0].handlers.keydown({key:'End',preventDefault(){}});checkTab('verifikasi');
context.selectResultTab('invalid');checkTab('verifikasi');assert(!html.includes("scrollIntoView({behavior:'smooth'})"));
console.log('Views/hash navigation, active state, result tabs, keyboard and focus verified; no automatic page scroll.');

// Guided image follows dataset/upload mode; stale upload previews must not reappear.
for(const id of ['guidedPreview','guidedPlaceholder','previewData','previewUpload','modeData','gambar'])panels[id]=node(id);
panels.modeData.style={display:'block'};panels.gambar.files=[];panels.previewData.attrs.src='/api/gambar/sample';panels.previewUpload.attrs.src='blob:old';
context.updateGuidedPreview();assert.equal(panels.guidedPreview.attrs.src,'/api/gambar/sample');assert.equal(panels.guidedPreview.hidden,false);assert.equal(panels.guidedPlaceholder.hidden,true);
panels.modeData.style.display='none';context.updateGuidedPreview();assert.equal(panels.guidedPreview.hidden,true);assert.equal(panels.guidedPlaceholder.hidden,false);assert.equal(panels.guidedPreview.attrs.src,undefined);
panels.gambar.files=[{}];panels.previewUpload.attrs.src='blob:new';context.updateGuidedPreview();assert.equal(panels.guidedPreview.attrs.src,'blob:new');assert.equal(panels.guidedPreview.hidden,false);
panels.modeData.style.display='block';context.updateGuidedPreview();assert.equal(panels.guidedPreview.attrs.src,'/api/gambar/sample');
console.log('Guided preview: dataset, empty upload, new upload and return to dataset verified.');
