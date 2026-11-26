# Stage 4-B 第1便：山中城・西木戸口の左門扉（試作D0）

Refs #52, #47, #49, #51。成果単位は左門扉1組。右門扉、門柱、門全体、開閉・荷重、山中城側での実装は本便に含まない。

## 制作根拠と座標

固定した山中城 main [16e22645](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/tree/16e22645ee0d0c03926c4e15a753c7e64fb2c450)。[部位資料](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/blob/16e22645ee0d0c03926c4e15a753c7e64fb2c450/docs/west-gate-left-door-components.md) の左は `gate.door.1.0..5` と `gate.door.rail.1.0.45 / 1.2.15`。北門柱は別部品。固定制作式の [box定義](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/blob/16e22645ee0d0c03926c4e15a753c7e64fb2c450/scripts/phase3b-build-blender.py#L42-L54) と [配置](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/blob/16e22645ee0d0c03926c4e15a753c7e64fb2c450/scripts/phase3b-build-blender.py#L92-L100)、および既存出力台帳 `evidence/phase3b/native/blender-build.json` を照合。箇所とハッシュは下の表を参照。

| 項目 | 推定C模型（制作式／出力台帳） | 試作D0 |
|---|---|---|
| 幅・厚さ・高さ | 板6枚、270×130×2,850 mm。元の式はE/N/Z順で 130/270/2850 mm。角は25 mm Bevel設定（外観D、設定値がそのまま実効半径と仮定しない） | 正本板1種類。ローカルX/Y/Zで270/130/2850 mm、直方体 |
| 厚さに沿う並び | 隣接する中心差はE/Nで約57.614/284.219 mm、各部材は+0.20 rad。各板の幅軸に約267.108 mm、奥行軸に約112.931 mmの投影差。単純な 290−270 は実メッシュの隙間ではない | 部材中心を同一平面に整列し、X方向のピッチ290 mm、設計上のすき間20 mmを5箇所に明示 |
| 横桟 | 共通箱寸法1,850×170×150 mm、E=-190.7 m、N=-33.85 m、板基準底より400および2,100 mm高い。中心の並びと桟の面位置が揃う式ではない | 正本横桟1種類。板の背面Y=130 mmで全6枚へ横桟ごとに面接触。Xの中心を板群の中心に合わせ、ZはCと同じ400・2,100 mm |
| 支持・回転・縮尺 | 地表の支持高は制作台帳上 548.6599731445312 m、板底はその50 mm上。ローカルE/N/Z、EPSG:6676関連の配置、C模型上の姿勢のみ | B01の下隅が (0,0,0)。右手Z-up、X幅、Y奥行（背面側を正）、Z高さ、全8配置の回転0。CAD mm、工房・GLB m、名目1:1。GLBは (x,y,z)→(x,z,−y)。現地の支持高・原点・方位変換はUNKNOWN、採用/配置承認なし |

C模型の数値は、当時の史料で確認した門扉寸法ではない。DはCの部材構成と箱寸法の参考化であり、原GLBの置換互換を保証しない。角落とし・現物の仕口・釘・木栓・蝶番・軸受・開閉方向はUNKNOWN。技術的な支持や固定を保証しないため、接合部品は追加せず、工房v2の接続点も0とした。色は展示用で樹種や材料の証拠ではない。

| 山中城の参照ファイル | SHA-256 |
|---|---|
| `scripts/phase3b-build-blender.py` | `691a106232f85dcfcd6b568507e0ad02328b96cba8dda88e6bd94ff7289b6b98` |
| `scripts/phase3b-recipe.py` | `6e296f750cdb7dacd9a03ad4149155b9320a63983b416e6e88d078f9ad6e5c45` |
| `production/yamanaka-phase3b.blend` | `b12d1ff362c4f3b04b3d90f365f541b68bbf70f2e6c5ef55ad2520da8da47765` |
| `public/data/phase3b.glb` | `894f76faa3b601bbfb65ec1f153de972f62c3b502135ac9e46e51bdaa4c42a4c` |
| `evidence/phase3b/native/blender-build.json` | `fb4cf61216605e3227bc7dded7ebbe0865b28bf61555154ed26dc95045853b92` |

## 正本・組立・提供

- `YAM-WEST-LEFT-BOARD D0`、`YAM-WEST-LEFT-RAIL D0`、`YAM-WEST-LEFT-LEAF D0`。CADは [cad/stage4b/west-gate-left](../../cad/stage4b/west-gate-left/)、編集用メッシュは [blender/stage4b](../../blender/stage4b/)、配置正本は [spec.json](../../cad/stage4b/west-gate-left/spec.json)。同名STEPは交換用、3つのGLBは配信用。各バイトのハッシュは [SHA256SUMS](SHA256SUMS)。ライブラリ外への提供時は、採用者が本PRの受入済みコミットと該当SHAを固定する。編集中の Draft、現行 main や山中城の採用済み版と混同しない。
- 既存試作ZIP `castle-stage4b-west-gate-board-prototype.zip`（93,614 B、SHA-256 `aaea9cdf8955e6a1d289fc05cb778d914c3977274d4c596ab2f5541623e1d128`）の10ファイルの内包ハッシュを照合。板FCStd/STEP/.blendは原バイトを再利用し、元ZIPや内容の保存位置は変更しない。板の配信GLBだけ、同じFCStdから材質Dと識別タグを加えて別名で派生。
- [v2組立例](../../assembly/stage4b/example.json) は板B01…B06／横桟R01,R02を独立配置し、定義は2種。名目外形1,850×300×2,850 mm。部品カタログの基準参照commitと正規化JSON SHA-256の双方を保持。基準commitは従前の工房・試作調査の公的基準で、今回追加する部品バイトの出典は本PRの固定HEAD/資産SHAで示す。編集設計はv2一般契約、固定初期例は個数・各ID・姿勢も別途固定照合。不正な参照・非有限座標や範囲超過は有効配置を変更せず拒否する。
- 旧工房の設計をそのまま読める従来カタログ画面は不変。第1便は別の固定カタログで開く。保存形式は共通だがカタログのSHAが異なるため、相互に読み替えない。接触はこの固定例のみ検査し、任意編集後の構造検査を提供しない。
- [山中城向け需要台帳](../../assembly/stage4a/yamanaka-demand.json) のYAM-001/002/003にD0候補を追記。供給準備のみ、採用・架設は別判断。

## 検査と再生成

FreeCAD 1.0.0 / OCCT 7.8.1、Blender 4.3.2、Debian 13 x86_64。GUI操作ではなくネイティブAPIとBlenderバッチを使用。

- FCStd、STEPを実再読込し、各部材の単位、原点、8頂点、12稜線、6平面・面積、外形、体積を既知の直方体と照合。左扉FCStd/STEPの8配置。同一部材の複製は出力用で、配置は独立記録。OCCTで28組の正体積交差（しきい値0.001 mm³）を検査し、12面接触を40,500 mm²/面で照合。初期例の20 mmの隙間5件。1 mm貫入／1 mm離れ／1 mm隙間拡大の3負対照を拒否。
- Blender原本を再読込し、GLBをさらに新規シーンへ再取込み。座標・寸法だけでなく2 μmのしきい値で全頂点の8隅対応、6境界面の2三角形、対向向きの稜線被覆を照合。組立は8オブジェクト/2メッシュ。実Solidの一般的な厳密同値、有限誤差上界、荷重・連続運動の安全性を証明したものではない。
- 展示トップ → 左門扉展示（板材・横桟・全体切替）→ 左門扉の工房 → 展示、従来の工房と展示室も残す。実ブラウザ試験は固定提出HEADのCI原票を参照。実機iPhone Safari、実物/現地検証はNOT_TESTED。
- 歴史検証用ファイルは変えず、公式Pagesの既存ビルダーへ最後の追加合成だけを登録。変更前のビルダーはStage 4-A移行の記録を上書きせず、[一つ前の正確な版とハッシュ](../../evidence/stage4b/pages-integration/)をチェーンで検証する。既存Pages公開条件・既存workflow定義は変更せず、PR限定の専用ブラウザ検査のみを追加する。Draftにおける静的配信検査はデプロイではない。

```bash
export PYTHONPATH=/usr/lib/freecad-python3/lib LD_LIBRARY_PATH=/usr/lib/freecad-python3/lib QT_QPA_PLATFORM=offscreen
/usr/bin/python3 -B scripts/stage4b/native.py --negative
blender --background --factory-startup --python-exit-code 1 --python scripts/stage4b/mesh.py -- check
node --test
node scripts/build-stage2d-site.mjs
node --test scripts/stage4a-pages-check.mjs
```

再生成するときは空の別フォルダを使う。`native.py --generate <空CADフォルダ> --mesh <新規JSON>`、続いて `blender --background --factory-startup --python-exit-code 1 --python scripts/stage4b/mesh.py -- generate <JSON> <空出力フォルダ>`。FreeCAD文書の保存時刻やツール版により再生成バイトは変わり、原本の置換は行わない。版付きの派生物・ハッシュを意図的に更新するときだけ別枝で `node scripts/stage4b/build-catalog.mjs --generate` を用い、通常検査は `--check`。
