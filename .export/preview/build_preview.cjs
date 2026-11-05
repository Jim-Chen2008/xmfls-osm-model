/* 构建：把 three.js / GLTFLoader / OrbitControls / GLB 全部内联成单文件预览页 */
const fs = require('fs');
const path = require('path');

const WORK = __dirname;
const GLB = 'C:/xmfls test/ds/xmfls-osm-model/dist/厦门外国语学校海沧校区-足球场原点.glb';
const OUT = 'C:/xmfls test/ds/xmfls-osm-model/dist/预览-足球场原点-查看器.html';

const three = fs.readFileSync(path.join(WORK, 'three128.js'), 'utf8');
const loader = fs.readFileSync(path.join(WORK, 'GLTFLoader.js'), 'utf8');
const orbit = fs.readFileSync(path.join(WORK, 'OrbitControls.js'), 'utf8');
const app = fs.readFileSync(path.join(WORK, 'app.js'), 'utf8');
const glb = fs.readFileSync(GLB);
const b64 = glb.toString('base64');

const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>厦门外国语学校（海沧校区）· 体块模型预览 — 足球场原点</title>
<style>
  :root{
    --ink:#28302a; --ink-soft:#4f574f; --muted:#7b8278;
    --paper:#f5f0e6; --panel:rgba(252,249,242,.90);
    --line:rgba(45,54,46,.14); --accent:#a45337; --green:#436451; --blue:#4f6f7d;
    --sans:"Inter","Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
    --mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;overflow:hidden}
  body{font-family:var(--sans);color:var(--ink);background:
    radial-gradient(120% 95% at 62% 10%,rgba(255,253,246,.96) 0%,rgba(244,239,229,.95) 42%,rgba(225,218,204,.96) 100%);}
  #stage{position:fixed;inset:0}
  #stage canvas{display:block;outline:none}
  #head{position:fixed;left:26px;top:22px;pointer-events:none;max-width:560px;z-index:2}
  #head::before{content:"";position:absolute;left:-40px;right:-90px;top:-34px;bottom:-26px;z-index:-1;
    background:radial-gradient(58% 62% at 26% 44%,rgba(250,246,238,.94) 0%,rgba(250,246,238,.72) 55%,rgba(250,246,238,0) 100%)}
  #head h1{text-shadow:0 1px 0 rgba(255,255,255,.65)}
  #head .badge{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:9px;letter-spacing:.13em;color:#f7f3e9;background:var(--green);border-radius:4px;padding:5px 8px 4px}
  #head h1{margin:10px 0 2px;font-size:clamp(18px,1.9vw,25px);font-weight:650;letter-spacing:.01em;line-height:1.2}
  #head p{margin:2px 0 0;font-size:11px;color:var(--muted);letter-spacing:.02em;line-height:1.6}
  #panel{position:fixed;right:22px;top:22px;width:268px;background:var(--panel);border:1px solid rgba(255,255,255,.55);
    border-radius:14px;box-shadow:0 22px 60px -30px rgba(45,38,25,.40),0 2px 8px rgba(45,38,25,.05);
    backdrop-filter:blur(16px) saturate(1.04);padding:14px 15px 12px}
  .blk+.blk{margin-top:13px;padding-top:12px;border-top:1px solid var(--line)}
  .blk h2{margin:0 0 8px;font-family:var(--mono);font-size:8.5px;letter-spacing:.13em;color:var(--muted);font-weight:500}
  .views{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  .view-btn{font:inherit;font-size:11px;padding:7px 0;border-radius:7px;border:1px solid var(--line);background:rgba(255,255,255,.42);color:var(--ink-soft);cursor:pointer;transition:.15s}
  .view-btn:hover{background:rgba(255,255,255,.8)}
  .view-btn.on{background:var(--green);border-color:var(--green);color:#f7f3e9}
  .toggles{display:grid;gap:2px}
  .toggles label{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--ink-soft);padding:4px 0;cursor:pointer}
  .toggles input{appearance:none;-webkit-appearance:none;width:12px;height:12px;border-radius:3px;border:1px solid rgba(45,54,46,.34);background:rgba(255,255,255,.5);position:relative;flex:0 0 auto}
  .toggles input:checked{background:var(--green);border-color:var(--green)}
  .toggles input:checked::after{content:"";position:absolute;left:2.5px;top:1px;width:5px;height:3px;border-left:1.5px solid #fff;border-bottom:1.5px solid #fff;transform:rotate(-45deg)}
  .legend{display:flex;align-items:center;gap:6px;font-size:10.5px;color:var(--ink-soft);padding:2px 0}
  .sw{width:14px;height:3px;border-radius:2px;flex:0 0 auto}
  .swx{background:#c0392b}.swz{background:#2f6fa8}.sw0{background:#fff;border:1px solid #b9b2a3;height:9px;width:9px;border-radius:50%}
  #meter{position:fixed;left:26px;bottom:20px;font-family:var(--mono);font-size:9.5px;color:var(--muted);letter-spacing:.04em;line-height:1.7;
    text-shadow:0 1px 0 rgba(255,255,255,.8),0 0 12px rgba(250,246,238,.95);z-index:2}
  #meter b{color:var(--ink-soft);font-weight:600}
  #loader{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--ink-soft);background:rgba(245,240,230,.72);z-index:20}
</style>
</head>
<body>
<div id="stage"></div>
<div id="head">
  <span class="badge">GLB · glTF 2.0</span>
  <h1>厦门外国语学校（海沧校区）体块模型</h1>
  <p>原点 = 足球场中心 ｜ X 轴 = 球场中线 ｜ Z 轴 = 球场长轴 ｜ Y 轴向上 ｜ 单位：米</p>
</div>

<div id="panel">
  <div class="blk">
    <h2>视角 <span id="viewName" style="color:var(--accent)"></span></h2>
    <div class="views">
      <button class="view-btn on" data-view="iso">轴测总览</button>
      <button class="view-btn" data-view="top">正俯视</button>
      <button class="view-btn" data-view="pitch">足球场</button>
      <button class="view-btn" data-view="gate">校门</button>
    </div>
  </div>
  <div class="blk">
    <h2>图层</h2>
    <div class="toggles">
      <label><input type="checkbox" data-layer="helpers" checked>坐标轴 / 网格 / 原点</label>
      <label><input type="checkbox" data-layer="base" checked>背景地面（5 km 垫板）</label>
      <label><input type="checkbox" data-layer="buildings" checked>建筑体块</label>
      <label><input type="checkbox" data-layer="landmarks" checked>场地设施 / 地标</label>
      <label><input type="checkbox" data-layer="sports" checked>田径场 / 足球场</label>
      <label><input type="checkbox" data-layer="roads" checked>道路中线</label>
      <label><input type="checkbox" data-layer="landuse" checked>周边用地</label>
      <label><input type="checkbox" data-layer="context" checked>邻校边界 / 栏杆</label>
    </div>
  </div>
  <div class="blk">
    <h2>图例</h2>
    <div class="legend"><span class="sw swx"></span>X 轴 · 足球场中线</div>
    <div class="legend"><span class="sw swz"></span>Z 轴 · 足球场长轴</div>
    <div class="legend"><span class="sw sw0"></span>原点 (0,0,0)</div>
  </div>
</div>

<div id="meter">左键拖动旋转 · 滚轮缩放 · 右键平移 · 键盘 1/2/3/4 切换视角<br>
模型：<b>253</b> 网格 / <b>10.6k</b> 三角面 · 坐标系与 GLB 一致</div>
<div id="loader">正在载入模型…</div>

<script>${three}</script>
<script>${loader}</script>
<script>${orbit}</script>
<script>window.__GLB_B64="${b64}";</script>
<script>${app}</script>
</body>
</html>
`;

fs.writeFileSync(OUT, html, 'utf8');
console.log('WROTE', OUT, (Buffer.byteLength(html) / 1048576).toFixed(2) + ' MB');
