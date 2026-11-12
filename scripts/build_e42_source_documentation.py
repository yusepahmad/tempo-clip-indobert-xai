"""Render verified source excerpts, PNG screenshots and a local HTML reference.

Run with DEMO_XAI_745_FULL/venv/bin/python. Git is used only to read the audited
commit; local excerpt identity is checked before publishing any screenshot.
"""
from pathlib import Path
import hashlib
import html
import io
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer, HtmlLexer, JsonLexer

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'work/e42-production'
if not (AUDIT / '.git').is_dir():
    AUDIT = ROOT
SHA = 'e0a977ece2f77ae95325fd164ca0d58a148ec5d8'
ASSETS = ROOT / 'docs/e42_source_assets'
PREFIX = 'DEMO_XAI_745_FULL/'

# Every interval refers to the immutable GitHub commit, not a guessed line range.
SECTIONS = [
 ('architecture', 'CLIP visual encoder', '02_web_demo/tail_rich_engine.py', 128, 144, 'TailRichEngine._ensure_visual',
  'E42 inherits this pinned ViT-L-14 loader. Weight SHA-256 is checked before use. Only model.visual is retained; visual parameters are frozen. This is CLIP ViT-L/14, not the B/32 baseline.'),
 ('architecture', 'Image preprocessing: full + crop', '02_web_demo/tail_rich_engine.py', 146, 151, 'TailRichEngine._images',
  'Convert to RGB, crop the full width between 20% and 94% of image height, apply the pinned CLIP preprocessing to each view and stack the two images.'),
 ('architecture', 'IndoBERT textual encoder', '02_web_demo/tail_rich_engine.py', 110, 126, 'TailRichEngine._ensure_front',
  'Verify IndoBERT files at the manifest revision, load tokenizer and model locally, retain the first 10 encoder blocks, freeze parameters. The two trained tail blocks are loaded separately by TailMTL.'),
 ('architecture', 'Text preprocessing at serving time', '02_web_demo/tail_rich_engine.py', 153, 164, 'TailRichEngine._front_inputs',
  'Tokenize with truncation at 256 tokens. Padding and special tokens are excluded from mean pooling. Canonical dataset requests bypass this path and use the audited 128-token cache. Noncanonical text and uploads use this 256-token path.'),
 ('architecture', 'Training cache extraction', '01_notebook/e41_cached_tail/extract.py', 17, 39, 'main',
  'E42 consumes the E41 frozen-front cache: headline [SEP] supporting text, maximum 128 tokens, hidden state after block 10, padding zeroed, and non-special-token pooling. It also stores the initial last-two-block weights. This source is an upstream cache dependency, not an E42 training launcher.'),
 ('architecture', 'Historical CLIP feature extraction', '01_notebook/e36_clip_l14/extract.py', 12, 35, 'extract',
  'The upstream E36 extractor computes frozen L/14 features for full and crop views, normalizes each 768-dimensional vector and records input/weight hashes. E42 reuses these visual features through E41.'),
 ('architecture', 'Shared representation and three heads', '01_notebook/e42_tail_grid/tail_model.py', 8, 18, 'Head; class_weights; CFG',
  'Head.shared is Linear(2304,256), ReLU, Dropout(0.3). One ModuleDict has task1_issue, task2_domain_sumber and task3_primary_entity_type heads. Class counts come from the checkpoint: 10, 7 and 8.'),
 ('architecture', 'Trainable tail, fusion and forward', '01_notebook/e42_tail_grid/tail_model.py', 19, 31, 'TailMTL.__init__; features; forward',
  'Two BertLayer blocks transform cached/front hidden states. Masked mean pooling gives a normalized text768 vector. Concatenate 2×visual1536 with text768 → 2304; shared features feed all three heads. At training time tail/shared/heads are trainable; serving freezes the loaded model.'),
 ('loss', 'Warm-start joint head training (historical only)', '01_notebook/e42_tail_grid/tail_model.py', 32, 38, 'warm_head',
  'Before each historical fold fit, a head is warmed for 120 epochs on training indices, AdamW lr=0.001 and weight_decay=0.0001, using frozen baseline mean features and the same weighted joint loss. E42 web startup never calls warm_head.'),
 ('loss', 'Class weighting, joint CE and gradient update', '01_notebook/e42_tail_grid/worker.py', 31, 44, 'main.reset; main.epoch',
  'Each task uses CrossEntropyLoss with training-subset class weights. Aggregate fixed task weights, divide by their sum, backpropagate one scalar through all heads/shared/tail. CUDA AMP scales gradients, unscales, clips norm to 1, steps AdamW and updates the scaler. The optimizer has separate tail and head learning rates.'),
 ('loss', 'Configuration grid and selection rule', '01_notebook/e42_tail_grid/tail_model.py', 40, 46, 'batch_tensors; CONFIGS; select_candidate',
  'Six candidates: tail LR {2e-6,2e-5,1e-4} × task weights {1:1:1,1:2:2}. Epoch candidates {0,2,4,8,12,24}. Selection maximizes the recorded inner score, with first-enumerated candidate/epoch resolving ties.'),
 ('loss', 'Nested training loop and checkpoint export', '01_notebook/e42_tail_grid/worker.py', 52, 74, 'main outer/inner loops',
  'Five outer folds, two Task-2-stratified inner folds. Score each candidate by the minimum across tasks of mean inner Macro-F1; select using inner folds only, reset, refit outer-training data and save state/config/classes/train/test indices. No training code is executed in this documentation task.'),
 ('serving', 'Checkpoint loading and fold validation', '02_web_demo/e42_engine.py', 42, 72, 'E42Engine.__init__',
  'Load five CPU checkpoints with weights_only=True; verify cache identity, class maps, disjoint train/test indices and full 740-ID coverage. Load state strictly, eval(), and disable parameter gradients. The local patch additionally validates manifest backend/version and required asset names before loading.'),
 ('serving', 'Dataset inference context', '02_web_demo/e42_engine.py', 99, 122, 'E42Engine.prepare_analysis',
  'A known sample ID selects its held-out fold. Check image SHA-256. Canonical headline/supporting use cached hidden states; edited text passes through the pinned front. The selected fold features are retained in _context.'),
 ('serving', 'New-image feature extraction', '02_web_demo/e42_engine.py', 123, 147, 'E42Engine.prepare_analysis',
  'For uploads, select all five folds, normalize full/crop CLIP embeddings, compute the frozen text front and each trained tail representation. Keep per-fold vectors; self.model references the active head for inherited LIME compatibility, not a newly trained head.'),
 ('serving', 'Prediction and probability ensemble', '02_web_demo/tail_rich_engine.py', 211, 232, 'TailRichEngine.predict_vector; _prob_banyak_teks',
  'Compute head softmax per active fold and average probabilities. _result dispatches to the E42 override, so predictions carry E42 backend/version. Text perturbations recompute the same trained tails and heads using the same active folds.'),
 ('xai', 'Task-specific visual attribution', '02_web_demo/tail_rich_engine.py', 245, 260, 'TailRichEngine.gradcam_terpadu',
  'Hook the penultimate CLIP transformer block. Recompute full/crop visual features while keeping the selected text vector fixed. For each task, average probabilities over active folds and differentiate the predicted-class probability with respect to the hooked activations.'),
 ('xai', 'Attribution calculation and heatmap assembly', '02_web_demo/tail_rich_engine.py', 261, 273, 'TailRichEngine.gradcam_terpadu',
  'Discard CLS, sum activation×gradient across channels, take absolute value, validate the patch grid, resize full and crop maps, insert crop into rows 44:210 of a 224×224 canvas, sum and normalize. Integrated heatmap is the normalized mean of the three task maps. This is not CNN Grad-CAM or attention rollout.'),
 ('xai', 'Headline occlusion', '02_web_demo/tail_rich_engine.py', 222, 243, 'TailRichEngine._prob_banyak_teks; atribusi_kata; _normalize',
  'Create the full headline and variants deleting one whitespace-delimited word at a time. Contribution is p(original predicted class) minus p(with word removed). Supporting text and image remain fixed; use the same pinned front/trained tail/active checkpoint heads.'),
 ('xai', 'Inherited LIME implementation', '02_web_demo/xai_core.py', 419, 454, 'XAIEngine.atribusi_kata_lime',
  'LIME uses 120 variants by default, bow=False, whitespace splitting and seed 42. Its classifier callback dispatches to TailRichEngine._prob_banyak_teks on E42. Surrogate coefficients are local word explanations. self.model is assigned by prepare_analysis, so the guarded train() path is not used; inherited train() rejects runtime training.'),
 ('xai', 'Model/XAI identity contract', '02_web_demo/e42_engine.py', 164, 171, 'E42Engine.xai_contract',
  'Report E42 model version, task, active folds, evaluation mode and methods. The web handler combines this contract with prediction metadata in the response and analysis snapshot.'),
 ('integration', 'Inference-to-XAI call chain', '02_web_demo/app.py', 548, 582, 'analyse_core',
  'Prediction uses the prepared E42 context, then gradcam_terpadu produces the integrated and selected-task maps. MODEL_LOCK serializes access to the mutable active-fold context across threaded requests.'),
 ('integration', 'LIME dispatch and occlusion fallback', '02_web_demo/app.py', 595, 615, 'analyse_core',
  'Single-analysis defaults to LIME; batch defaults to occlusion. LIME exceptions are logged and fall back to occlusion. This is an explanation-method fallback within E42, not a model/backend fallback.'),
 ('integration', 'Response metadata and provenance', '02_web_demo/app.py', 646, 679, 'analyse_core',
  'Response includes prediction metadata, XAI contract, analysis ID, image hash, input text, protocol and per-task heatmap URLs. Narrative explanation is a template assembled from model/codebook/annotator evidence, not generated by a language model.'),
 ('integration', 'Frontend displays actual model identity', '02_web_demo/index.html', 164, 178, 'fetch /api/models callback',
  'Frontend fetches /api/models and selects an E42-specific status message. This avoids presenting B/32 baseline architecture as the active E42 model.'),
 ('integration', 'Frontend heatmap and text rendering', '02_web_demo/index.html', 642, 655, 'render analysis heatmaps',
  'Frontend selects the task-specific heatmap returned by the backend. Word contributions are rendered later from atribusi_kata; all belong to the same response/snapshot.'),
 ('integration', 'Frontend word-contribution display', '02_web_demo/index.html', 676, 695, 'render word contributions',
  'Scale signed contributions by their maximum absolute value and render each headline word as a bar. These are backend-provided LIME coefficients or occlusion deltas, not attention weights.'),
 ('serving', 'Version and artifact manifest', '06_models/e42-tail-grid-v1/manifest.json', 1, 36, 'manifest root fields',
  'Backend/version, dataset SHA, cache-manifest SHA and all nine artifact SHA-256 entries identify the release. The manifest also pins CLIP and IndoBERT revisions and weight hashes.'),
]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.txt"):
        for old in ASSETS.glob(pattern):
            old.unlink()
    records, cards = [], {}
    font = ImageFont.truetype('DejaVuSansMono.ttf', 15)
    for index, (group, title, relative, start, end, symbol, explanation) in enumerate(SECTIONS, 1):
        path = PREFIX + relative
        source = subprocess.check_output(['git', '-C', str(AUDIT), 'show', f'{SHA}:{path}']).decode()
        lines = source.splitlines(keepends=True)
        assert 1 <= start <= end <= len(lines), (path, start, end)
        excerpt = ''.join(lines[start-1:end])
        local = (ROOT / path).read_text()
        assert excerpt in local, f'Excerpt changed locally: {path}:{start}-{end}'
        local_start = local[:local.index(excerpt)].count('\n') + 1
        name = f'{index:02d}-{Path(relative).stem}'
        lexer = JsonLexer() if relative.endswith('.json') else HtmlLexer() if relative.endswith('.html') else PythonLexer()
        code = Image.open(io.BytesIO(highlight(excerpt, lexer, ImageFormatter(
            style='monokai', font_name='DejaVu Sans Mono', font_size=16,
            line_numbers=True, line_number_start=start, image_pad=20, line_pad=5))))
        label = f'{path}  |  L{start}–L{end}  |  {SHA[:12]}'
        width = max(code.width, int(font.getlength(label)) + 40)
        image = Image.new('RGB', (width, code.height + 55), '#202622')
        image.paste(code, (0,55))
        ImageDraw.Draw(image).text((20,18), label, font=font, fill='#d7f8de')
        image.save(ASSETS / (name+'.png'))
        (ASSETS / (name+'.txt')).write_text(excerpt)
        url = f'https://github.com/yusepahmad/tempo-clip-indobert-xai/blob/{SHA}/{path}#L{start}-L{end}'
        record = dict(title=title, path=path, symbol=symbol, commit=SHA, start=start, end=end,
                      local_start=local_start, local_end=local_start+end-start, github=url,
                      source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                      excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(), image=name+'.png')
        records.append(record)
        cards.setdefault(group, []).append(f'''<article id="component-{index}"><span class="eyebrow">SOURCE {index:02d}</span><h3>{html.escape(title)}</h3>
<p>{html.escape(explanation)}</p><dl><dt>Symbol</dt><dd><code>{html.escape(symbol)}</code></dd><dt>File</dt><dd><code>{path}</code></dd><dt>Location</dt><dd>GitHub snapshot L{start}–L{end} · current local L{record['local_start']}–L{record['local_end']}</dd></dl>
<p><a href="{url}">Open exact source on GitHub ↗</a> · <a href="e42_source_assets/{name}.txt">Plain source excerpt</a></p>
<figure><div class="source-scroll"><img loading="lazy" src="e42_source_assets/{name}.png" alt="Actual source: {path}, lines {start} to {end}"></div><figcaption>Verbatim source rendering with syntax highlighting; no synthetic code. Scroll horizontally for long lines.</figcaption></figure></article>''')
    (ASSETS/'source-index.json').write_text(json.dumps(records, indent=2)+'\n')
    group_names = [('architecture','01','CLIP–IndoBERT implementation'), ('loss','02','Joint Loss & historical training'), ('serving','03','Checkpoint inference & serving'), ('xai','04','Explainable AI implementation'), ('integration','05','Backend → frontend integration')]
    sections = ''.join(f'<section id="{g}"><h2><span>{n}</span>{title}</h2>'+''.join(cards[g])+'</section>' for g,n,title in group_names)
    fold_rows = ''
    import torch
    for fold in range(1,6):
        cp = torch.load(ROOT/PREFIX/f'06_models/e42-tail-grid-v1/fold{fold}.pt', map_location='cpu', weights_only=True)
        c=cp['config']
        fold_rows += f"<tr><td>{fold}</td><td>{cp['config_index']}</td><td>{c['encoder_lr']}</td><td>{c['head_lr']}</td><td>{':'.join(str(int(x)) for x in c['loss_weights'])}</td><td>{cp['selected_epoch']}</td></tr>"
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>E42 · Source Code Reference</title>
<style>
:root{--ink:#172a3d;--muted:#526478;--line:#dce4eb;--mint:#b4f1d4}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f3f6f9;color:var(--ink);font:16px/1.65 system-ui,sans-serif}header{background:#102a36;color:white;padding:64px max(5vw,24px)}header p{max-width:900px;color:#c5d9df}h1{font-size:clamp(32px,5vw,60px);line-height:1.1;letter-spacing:-2px;margin:18px 0}header code{color:var(--mint)}.eyebrow{font-size:12px;font-weight:750;letter-spacing:2px;color:#16745a}header .eyebrow{color:var(--mint)}nav{position:sticky;top:0;background:#fffef9f5;backdrop-filter:blur(12px);padding:16px 5vw;border-bottom:1px solid var(--line);display:flex;gap:24px;flex-wrap:wrap;z-index:2}a{color:#116656;text-underline-offset:4px}nav a{font-size:14px;font-weight:650}main{max-width:1200px;margin:40px auto;padding:0 24px}section{scroll-margin-top:100px;margin:55px 0}h2{font-size:30px;line-height:1.2;border-top:1px solid var(--line);padding-top:28px}h2 span{font-size:15px;color:#16745a;display:block;margin-bottom:10px}h3{font-size:23px;margin:8px 0 12px}article,.panel{background:white;border:1px solid var(--line);border-radius:14px;padding:28px;margin:24px 0;box-shadow:0 4px 18px #19364a05}article p{max-width:950px}code{font:13px/1.7 'DejaVu Sans Mono',monospace;overflow-wrap:anywhere}dl{display:grid;grid-template-columns:100px 1fr;gap:6px 15px;font-size:14px}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}figure{margin:24px 0 0}.source-scroll{overflow:auto;border-radius:8px;background:#202622}.source-scroll img{display:block;max-width:none}figcaption{font-size:12px;color:var(--muted);margin-top:10px}.formula{font:19px/1.8 monospace;background:#eef9f3;border-left:4px solid #168062;padding:20px;overflow:auto}.flow{padding:22px;background:#e8f4ef;border-radius:10px;font-weight:650;line-height:2.1}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;border-bottom:1px solid var(--line);padding:12px}th{background:#eef3f6}.note{border-left:4px solid #cb8c26;padding:12px 20px;background:#fff8e9}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}.grid .panel{margin:0}footer{padding:40px 5vw;background:#102a36;color:#c5d9df;font-size:13px}@media print{nav{position:static}.source-scroll img{max-width:100%;height:auto}.source-scroll{overflow:visible}article{break-inside:avoid;box-shadow:none}body{background:white}}
</style><header><div class="eyebrow">ENGINEERING REFERENCE · VERIFIED SOURCE · 13 NOV 2026</div><h1>E42 source code,<br>from encoders to explanations.</h1><p>CLIP ViT-L/14 + IndoBERT trainable tail · shared representation · three joint task heads. A traceable reference for model implementation and Linux/Gunicorn serving.</p><p><code>e42-tail-grid</code> / <code>e42-tail-grid-v1</code><br>Audited GitHub snapshot: <code>COMMIT</code></p></header>
<nav><a href="#overview">Overview</a><a href="#architecture">Architecture</a><a href="#loss-summary">Joint Loss</a><a href="#serving">Inference</a><a href="#xai">XAI</a><a href="#integration">Integration</a><a href="#verification">Verification</a></nav><main>
<section id="overview"><h2><span>MODEL OVERVIEW</span>One shared representation, three tasks</h2><div class="flow">Image → CLIP-L/14 frozen → full768 + crop768<br>Headline + supporting → IndoBERT frozen front10 → trained tail2 → mean-pooled text768<br>concat(2 × full, 2 × crop, text) → shared Linear2304→256 / ReLU / Dropout0.3<br>→ issue10 · source-domain7 · entity-type8 → weighted Joint Loss (training only)</div>
<div class="grid"><div class="panel"><h3>Actual E42</h3><p>Frozen visual encoder; last two IndoBERT blocks, shared layer and all heads trained jointly. Serving uses five original outer-fold checkpoints, without retraining.</p></div><div class="panel"><h3>Legacy baseline</h3><p><code>xai_core.XAIEngine</code> / <code>mtl_engine.MTLDeliveryEngine</code>: CLIP-B/32 image512 + IndoBERT CLS768, shared1280→256, dropout0.4 and runtime head refit. It is an explicit historical backend.</p></div></div>
<p class="note">All screenshots show verbatim source at the fixed GitHub commit. The generator verifies that each excerpt also occurs unchanged in the current local file and records both line ranges. Local launcher/manifest/log patches are documented separately; they have no published commit URL yet. No fabricated GitHub links to unpublished changes.</p>
<p>Open the HTML alongside <code>e42_source_assets/</code>. No CDN, web font or external script is required. Machine-readable source hashes and ranges: <a href="e42_source_assets/source-index.json">source-index.json</a>.</p></section>
<section id="loss-summary"><h2><span>OPTIMIZATION OBJECTIVE</span>Three Cross Entropy losses, one update</h2><p>For each task t, class weights use only that fit's training subset. For present class c, w(t,c)=Ntrain/(Kpresent × count(t,c)); absent classes receive zero weight. PyTorch's weighted-mean CrossEntropyLoss divides weighted negative log likelihood by the sum of target-class weights in the batch.</p><div class="formula">Ljoint = (α1 Lissue + α2 Ldomain + α3 Lentity) / (α1 + α2 + α3)</div><p>The α values are fixed hyperparameters for a fit, either 1:1:1 or 1:2:2. They are not class weights and are not learned uncertainty weights. One backward pass accumulates gradients in shared/tail parameters and all task heads. Serving computes probabilities and XAI gradients only; it performs no optimizer update.</p><p>Historical tail training uses AdamW weight_decay=0.01, batch32, seed42, head LR0.0003. Below are the actual saved checkpoint configurations, read directly from <code>fold*.pt</code>; the module default is not assumed to describe every fold.</p><div style="overflow-x:auto"><table><thead><tr><th>Fold</th><th>Config index</th><th>Tail LR</th><th>Head LR</th><th>Task weights</th><th>Selected epoch</th></tr></thead><tbody>FOLDS</tbody></table></div></section>
SECTIONS
<section id="verification"><h2><span>REPRODUCIBILITY & DELIVERY</span>Verification notes</h2><div class="panel"><p>Checkpoint identity: <code>e42-tail-grid-v1</code>. All nine release asset hashes and dataset SHA are validated before model loading. Five outer-fold splits cover 740 unique IDs; strict state loading rejects incompatible parameters.</p><p>Local launcher changes: Linux uses <code>${TEMPO_BACKEND:-e42-tail-grid}</code>; Gunicorn uses <code>os.environ.setdefault('TEMPO_BACKEND', 'e42-tail-grid')</code>. Windows retains its conditional E42 default. Overrides are intentional and unknown backends raise visibly. E42 startup logs backend and version. Gunicorn remains one worker/four threads, without a second preflight model instance. Linux preflight exits before the application initializes.</p><p><strong>XAI scope:</strong> Visual attribution is class-specific absolute gradient × activation with text held fixed. LIME/occlusion perturb headline, not supporting text. E42's inherited LIME callback uses the E42 tails and heads. Historical revision evidence describing attention rollout or baseline B/32 should not be used to label the current web algorithm. Heatmaps are model sensitivity, not causal proof.</p><p><strong>Input-length limitation:</strong> The audited cache/training uses 128 tokens, whereas inherited serving preprocessing uses 256 for edited/new text and text perturbations. This existing difference is preserved and documented; ensemble uploads and edited inputs are not claimed to reproduce a new benchmark. Softmax scores are uncalibrated.</p><p><strong>Runtime evidence:</strong> See <a href="e42_production_verification.md">executed commands and observed results</a>, <a href="e42_production_deployment.md">Linux/Gunicorn preparation</a>, and <a href="../qa/e42-production/">HTTP evidence artifacts</a>. Startup validates checkpoint/cache assets; backbones are lazy-loaded and their pinned files are hash-checked when needed. Prepare backbone caches before enabling offline production traffic. Native Windows and a VPS deployment are separate verification scopes.</p></div><p>Related historical architecture audit: <a href="revisi-ii/R18_ARSITEKTUR_JOINT_LOSS.md">R18 architecture and Joint Loss</a>. Current web behavior above is established by source tracing and runtime evidence, rather than historical prose.</p></section></main><footer>E42 engineering reference · PNGs rendered directly from checked source · Immutable source commit COMMIT · Generated by scripts/build_e42_source_documentation.py</footer></html>'''
    document = document.replace('COMMIT', SHA).replace('FOLDS',fold_rows).replace('SECTIONS',sections)
    (ROOT/'docs/e42_source_code_documentation.html').write_text(document)
    print(f'Generated {len(records)} verified source screenshots and HTML reference')


if __name__ == '__main__':
    main()
