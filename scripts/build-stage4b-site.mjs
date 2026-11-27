/** Stage 4-B additions to the official 2-D / 4-A distribution. */
import {readFile,writeFile,cp,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const base = 'cad/stage4b/west-gate-left';
const assets = [
  'assembly/stage4b/catalog.json','assembly/stage4b/example.json','assembly/stage4b/fixed-leaf.mjs',
  ...['west-gate-board-web','west-gate-rail-draft','west-gate-left-leaf']
    .flatMap(stem=>[`${base}/${stem}.glb`,`${base}/${stem}.manifest.json`]),
];
for(const path of assets){
  await mkdir('dist/'+path.split('/').slice(0,-1).join('/'),{recursive:true});
  await cp(path,'dist/'+path);
}
const insert=(s,mark,val)=>{
  if(s.split(mark).length!==2)throw Error('Stage 4-B HTML marker changed: '+mark);
  return s.replace(mark,val);
};
const home='dist/index.html';
await writeFile(home,insert(await readFile(home,'utf8'),'</nav>',
  '<p><a id="west-gate-exhibit" href="./stage4b/exhibit/">山中城・西木戸口の左門扉</a>（試作D：完成組立と構成部品）</p></nav>'));
const template=await readFile('dist/stage4a/workshop/index.html','utf8');
for(const kind of ['exhibit','workshop']){
  const folder='dist/stage4b/'+kind;
  await mkdir(folder,{recursive:true});
  const exhibit=kind==='exhibit';
  let html=insert(template,'<body>',`<body data-model="west-gate-left" data-view="${kind}">`)
    .replaceAll('./workshop.','../../stage4a/workshop/workshop.')
    .replaceAll('STAGE 4-A','STAGE 4-B')
    .replaceAll('城郭組立工房',exhibit?'西木戸口の左門扉':'左門扉の組立工房');
  html=insert(html,'</nav>',exhibit?
    ' · <a id="open-gate-workshop" href="../workshop/">左門扉を工房で開く</a></nav>':
    ' · <a id="open-gate-exhibit" href="../exhibit/">左門扉の展示へ戻る</a></nav>');
  html=insert(html,'</header>',exhibit?`<p>完成した左門扉、板材1枚、横桟1本を切り替えて観察できます。</p>
<div class="buttons" aria-label="観察する模型"><button type="button" data-preset="assembly" aria-pressed="true" disabled>左門扉全体</button><button type="button" data-preset="board" aria-pressed="false" disabled>板材1枚</button><button type="button" data-preset="rail" aria-pressed="false" disabled>横桟1本</button></div>
</header>`:'</header>');
  html=insert(html,'部品を選び、配置し、接続する。',exhibit?'試作Dの構造を見る。':'部品を選び、配置を編集する。');
  html=insert(html,'試作D・参照模型。接続点の一致のみを検査します。史実、実物強度、全体干渉、連続運動、安全性、山中城への配置は未確認です。','試作D・参照模型。史実・接合・強度・開閉は未確定です。');
  html=insert(html,'<section class="panel persistence"',`<section class="note" aria-labelledby="gate-evidence">
<h2 id="gate-evidence">構成、寸法と制作根拠</h2>
<ul><li>組立：幅1,850 × 奥行300 × 高さ2,850 mm。基準は板の左下隅。</li>
<li>板材：270 × 130 × 2,850 mm、同じ正本を6配置。模型上の均一な隙間は20 mm。</li>
<li>上下横桟：1,850 × 170 × 150 mm、同じ正本を2配置。板の背後に置き、板底から400／2,100 mm。</li></ul>
<p>山中城の推定C模型を寸法・部材構成の参考にした試作Dです。板を同一平面に揃え、横桟は重なりのない面接触に変更。歴史的な形状・寸法、接合方法、実物強度、開閉機構は未確定です。山中城への採用・配置は未承認です。</p>
<a href="https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/blob/16e22645ee0d0c03926c4e15a753c7e64fb2c450/scripts/phase3b-build-blender.py#L92-L100">参照した推定C制作式</a>
 · <a href="../../${base}/west-gate-left-leaf.manifest.json">固定配信メタデータ</a>
</section>
<section class="panel persistence"`);
  if(exhibit) html=insert(html,'</head>','<style>.workspace{display:block}.workspace>.library,.workspace>.edit,.persistence{display:none}</style></head>');
  await writeFile(folder+'/index.html',html);
}
const metadata='dist/deployment-manifest.json';
const version=JSON.parse(await readFile(metadata));
version.stage4b_assets={};
for(const path of assets)version.stage4b_assets[path]=createHash('sha256').update(await readFile('dist/'+path)).digest('hex');
await writeFile(metadata,JSON.stringify(version,null,2)+'\n');
console.log('Stage 4-B left leaf: fixed models and both workshop entry points included.');

await import('./stage4b/wave2/site.mjs');
