const vm=require('vm'),assert=require('assert');
const nodes={};for(const id of ['hasil','jalan','spin','task','sample','modeData','dataHeadline','dataSupporting'])nodes[id]={style:{display:'block'},disabled:false,value:id==='task'?'task2_domain_sumber':'input',classList:{add(){},remove(){}}};
nodes.workspace={dataset:{state:'ready'}};for(const id of ['workspaceTag','workspaceTitle','workspaceDescription'])nodes[id]={textContent:''};
const pending=[],rendered=[];const context={document:{getElementById:id=>nodes[id]},AbortController,FormData,alert:m=>{throw Error(m)},fetch:()=>new Promise(resolve=>pending.push(resolve)),tampil:(data)=>{rendered.push(data);nodes.hasil.style.display='block';context.setWorkspaceState('results');}};
vm.createContext(context);
const html=require('fs').readFileSync(require('path').join(__dirname,'../02_web_demo/index.html'),'utf8');
vm.runInContext(html.slice(html.indexOf('let analysisSeq='),html.indexOf('function tampil(d, modeData)')),context);

(async()=>{
 const first=vm.runInContext('analisis()',context);
 assert.equal(nodes.workspace.dataset.state,'loading');
 vm.runInContext('invalidateAnalysis()',context);
 assert.equal(nodes.workspace.dataset.state,'ready');
 nodes.task.value='task1_issue';
 const second=vm.runInContext('analisis()',context);
 pending[0]({json:async()=>({task:'old'})});await first;
 assert.equal(rendered.length,0);assert.equal(nodes.jalan.disabled,true);assert.equal(nodes.workspace.dataset.state,'loading');
 pending[1]({json:async()=>({task:'new'})});await second;
 assert.equal(rendered.length,1);assert.equal(rendered[0].task,'new');assert.equal(nodes.jalan.disabled,false);
 assert.equal(nodes.workspace.dataset.state,'results');
 vm.runInContext('invalidateAnalysis()',context);
 assert.equal(nodes.workspace.dataset.state,'ready');
 console.log('Dashboard loading, invalidation and results states verified.');
 console.log('Late analysis response ignored; current response rendered; active button state preserved.');
})().catch(e=>{console.error(e);process.exitCode=1;});
