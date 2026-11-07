// Regression for descending task scores; run with node (no model required).
const assert=require('assert'),fs=require('fs'),path=require('path'),vm=require('vm');
const html=fs.readFileSync(path.join(__dirname,'../02_web_demo/index.html'),'utf8');
const node={innerHTML:''},context={document:{getElementById:id=>{assert.equal(id,'tabelPred');return node;}}};
vm.createContext(context);
vm.runInContext(html.slice(html.indexOf('function skorPrediksi('),html.indexOf('function tampil(d, modeData)')),context);
const sort=vm.runInContext('urutkanPrediksi',context);
const keys=p=>Array.from(sort(p),([key])=>key);
const pred=(task,score)=>({nama_task:task,prediksi:'kelas-'+task,prediksi_tampil:'Label '+task,
  probabilitas:score,semua:[{kelas:'utama',prob:score},{kelas:'kedua-'+task,prob:0.15}]});
const fixture={task1:pred('Isu utama',0.177),task2:pred('Domain sumber',0.304),task3:pred('Sasaran kritik',0.27)};
const original=JSON.stringify(fixture);
Object.values(fixture).forEach(Object.freeze);Object.freeze(fixture);
assert.deepStrictEqual(keys(fixture),['task2','task3','task1']);
assert.deepStrictEqual(keys({a:pred('A','0.09'),b:pred('B','0.8'),c:pred('C','0.10')}),['b','c','a']);
assert.deepStrictEqual(keys({a:pred('A',0.4),b:pred('B',0.4),c:pred('C',0.9)}),['c','a','b']);
assert.deepStrictEqual(keys({bad:pred('Bad','nope'),missing:pred('Missing'),zero:pred('Zero',0),
  null:pred('Null',null),blank:pred('Blank',' '),infinite:pred('Infinite',Infinity),nan:pred('NaN',NaN)}),
  ['zero','bad','missing','null','blank','infinite','nan']);
assert.deepStrictEqual(keys({}),[]);assert.deepStrictEqual(keys(null),[]);
assert.equal(JSON.stringify(fixture),original);
assert.strictEqual(sort(fixture)[0][1],fixture.task2);

// Exercise the actual table-rendering block, not a second implementation.
const start=html.indexOf('  // tabel prediksi'),end=html.indexOf('  // gambar',start);
assert(start>0 && end>start);
vm.runInContext('function renderTable(prediksi){const d={prediksi};'+html.slice(start,end)+'}',context);
context.fixture=fixture;vm.runInContext('renderTable(fixture)',context);
const rendered=node.innerHTML;
assert(rendered.indexOf('Domain sumber')<rendered.indexOf('Sasaran kritik'));
assert(rendered.indexOf('Sasaran kritik')<rendered.indexOf('Isu utama'));
for(const [task,pct] of [['Domain sumber','30.4'],['Sasaran kritik','27.0'],['Isu utama','17.7']]){
  const row=rendered.match(new RegExp('<tr><td>'+task+'[\\s\\S]*?</tr>'))[0];
  assert(row.includes('kelas-'+task));assert(row.includes(pct+'%'));
  assert(row.includes('width:'+pct+'%'));assert(row.includes('kedua-'+task));
}
assert(rendered.includes('tertinggi ke terendah'));
assert(rendered.includes('belum dikalibrasi'));
context.fixture={invalid:pred('Invalid','bad')};vm.runInContext('renderTable(fixture)',context);
assert(!node.innerHTML.includes('NaN'));assert(node.innerHTML.includes('—'));
assert(node.innerHTML.includes('width:0%'));
assert.equal(JSON.stringify(fixture),original);
assert(html.includes('for (const [k,p] of urutkanPrediksi(d.prediksi))'));
console.log('PASS: numeric descending sort, stable ties, invalid scores last, immutable input, task/class/runner-up mapping, actual table percentages and bars.');
