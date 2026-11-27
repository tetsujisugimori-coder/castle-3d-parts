import {cp,mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const base='cad/stage4b/west-gate-wave2';
const meta='dist/deployment-manifest.json';
const paths=[
 ...['catalog.json','example.json','design.json','poses.mjs'].map(n=>'assembly/stage4b-wave2/'+n),
 ...['post','bearing','pivot'].flatMap(n=>['glb','manifest.json'].map(ext=>base+'/west-gate-'+n+'.'+ext))
];
for(const path of paths) {
 await mkdir('dist/'+path.slice(0,path.lastIndexOf('/')),{recursive:true});
 await cp(path,'dist/'+path);
}
const insert=(s,mark,value)=>{
 if(s.split(mark).length!==2)throw Error('wave2 distribution marker drift: '+mark);
 return s.replace(mark,value);
};
const home='dist/index.html',old='dist/stage4b/exhibit/index.html';
await writeFile(home,insert(await readFile(home,'utf8'),'</nav>','<p><a id="west-gate-wave2" href="./stage4b/wave2/exhibit/">西木戸口 左右の門</a>（試作D1：開閉と支持構造）</p></nav>'));
await writeFile(old,insert(await readFile(old,'utf8'),'</nav>',' · <a href="../wave2/exhibit/">第2便・左右の門</a></nav>'));
const template=await readFile('dist/stage4a/workshop/index.html','utf8');
const buttons=choices=>choices.map(([id,label])=>`<button type="button" data-preset="${id}" aria-pressed="${id==='closed'}" disabled>${label}</button>`).join('');
const order=[['closed','閉鎖'],['left','左だけ開放'],['right','右だけ開放'],['both','両開放']];
for(const kind of ['exhibit','workshop']){
 const folder='dist/stage4b/wave2/'+kind, exhibit=kind==='exhibit';
 await mkdir(folder,{recursive:true});
 let html=template.replaceAll('STAGE 4-A','STAGE 4-B / 第2便')
  .replaceAll('城郭組立工房',exhibit?'西木戸口・左右の門':'西木戸口・組立工房')
  .replaceAll('./workshop.','../../../stage4a/workshop/workshop.')
  .replace('href="../../"','href="../../../"');
 html=insert(html,'<body>',`<body data-model="west-gate-wave2" data-view="${kind}">`);
 html=insert(html,'</nav>',exhibit?' · <a id="open-wave2-workshop" href="../workshop/">この固定姿勢を工房で開く</a> · <a href="../../exhibit/">第1便・左門扉</a></nav>':' · <a id="open-wave2-exhibit" href="../exhibit/">左右の門の展示に戻る</a></nav>');
 html=insert(html,'部品を選び、配置し、接続する。','板材・横桟を再利用した、回転支持の試作D1。');
 html=insert(html,'</header>',`<p aria-live="polite">表示：<strong id="wave2-state">閉鎖</strong></p>
 <div class="buttons" aria-label="門扉の固定姿勢">${buttons(order)}</div>
 ${exhibit ? '<div class="buttons" aria-label="左右と支持部品">'+buttons([['inspect-left','左側のみ観察'],['inspect-right','右側のみ観察'],['post','門柱'],['bearing','軸受ブラケット'],['pivot','支持ピンと腕']])+'</div>' : '<p>固定姿勢を選ぶと編集を置き換えます。編集内容は先にv2 JSONとして保存してください。</p>'}</header>`);
 html=insert(html,'試作D・参照模型。接続点の一致のみを検査します。史実、実物強度、全体干渉、連続運動、安全性、山中城への配置は未確認です。',
 '試作D1。接続点の一致と決められた姿勢の表示です。史実、荷重、軸方向の脱落防止、連続運動の安全性、現地配置は未確認。');
 html=insert(html,'<section class="panel persistence"',`<section class="note"><h2>見どころと根拠</h2>
 <p>左右の葉とも板材6枚・横桟2本。門柱2本、軸受4個、支持ピン4個。葉は閉鎖時に中央40 mmの設計隙間があり、左右とも同じ奥行き側へ90°開きます。</p>
 <p>第1便のD0と山中城の推定Cを参照。軸受とピンの構成・寸法・色は模型上の仮定で、西木戸口で発掘確認された形ではありません。緑点は工房接続の位置で、構造安全性を意味しません。</p>
 <p><a href="https://www.city.mishima.shizuoka.jp/page/1301.html">三島市・山中城跡の調査</a> · <a href="../../../${base}/west-gate-bearing.manifest.json">軸受の固定メタデータ</a></p></section><section class="panel persistence"`);
 if(exhibit) html=insert(html,'</head>','<style>.workspace{display:block}.workspace>.library,.workspace>.edit,.persistence{display:none}</style></head>');
 await writeFile(folder+'/index.html',html);
}
const manifest=JSON.parse(await readFile(meta,'utf8'));
manifest.stage4b_wave2_assets=Object.fromEntries(await Promise.all(paths.map(async p=>[p,createHash('sha256').update(await readFile('dist/'+p)).digest('hex')])));
await writeFile(meta,JSON.stringify(manifest,null,2)+'\n');
console.log('Stage 4-B wave 2: D1 gallery and workshop entries included');
