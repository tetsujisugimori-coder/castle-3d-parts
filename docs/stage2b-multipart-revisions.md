# Stage 2-B: 木柵の複数部品・連続改訂・図面

Refs #18。基準 main `34f43b3b1765de7a52994adb7175dc2c146f8db3`、tree `963bf0c064e4b78d67717be9307af0aa8980cc34`。Stage 2-A PR #17 はマージ済みであることをGitHub APIで確認した。今回の依頼はDraft PR・独立レビューまでで、マージ・Pages公開は行わない。

## 範囲と原本

既存451ファイルを保全し、追加ディレクトリだけで木柵の改訂を扱う。研究27記録をcommit・版・hashで固定し、現行台帳は読取専用。既存DECは保留、cad.eligibilityはreference_only。既存台帳のA/B/C/Dの定義を優先し、今回の新しい数値・配置・形状は全てD試作。山中城の実測値、正式採用、歴史的存在の確証ではない。

FreeCADが形状原本。公開パラメータはm、FreeCAD内部はmm、Blenderはm/Z-up、GLBはm/Y-up。角柱・平頭・横木の背面突合せはD。新しい接合金物や門・櫓の歴史復元は追加しない。

## 改訂

- B0: Stage2-Aの最終2.2m高・芯間隔1.2m・幅0.15m・5柱2横木のユニットを再現し、同版2ユニットをX=0m/6mに配置する。単体の全幅は4.95m。
- B1: B0の柱高だけを2.4mへ変更。高さに従属する横木のZ位置も式から更新する。位置・柱数・間隔は変更しない。
- B2: B1を継承し、U01はB1、U02の間隔だけを1.3mにしたB2とする。混版の依存を明示する。

2ユニットの端部は接続しない。間隙はB0/B1で1.05m、B2で0.85m。全体のX範囲と木材自体の長さの和を混同しない。並置の全幅は10.95m、B2は11.15m。干渉検査は生成した静止形状に限定し、施工・構造強度・地表接地は未検証。

## ファイル

- `design/stage2b/`: 保全基準、固定研究snapshot、追記型部品/改訂台帳、幾何差分。
- `cad/stage2b/spec.json`: D制作仕様。`generated/B0,B1,B2/`: assembly.FCStd/step/blend/glb、unit.FCStd/step、TechDraw投影を含む原本、drawing.svg、audit・mesh・manifest。
- `cad/stage2b/` と `blender/stage2b/`: 実再生成スクリプト。
- `scripts/stage2b.mjs`: 台帳/親版/参照/hash/原本保全/生成物の検証。
- `site/stage2b/`: 読取専用の3版GLB比較。版変更は研究台帳やCADへの適用ではない。
- `evidence/stage2b/`: 実ソフト・回帰・故障・ブラウザ・独立証拠。失敗を成功で上書きしない。

FCStd/STEPは保存時刻等によりバイトが変わり得る。hashは個別成果物識別に使い、再現性は部品ID・配置・寸法・体積・投影と別に検査する。GLBもhash一致だけで幾何学的一致を主張しない。

## 読取専用ビューア

リポジトリルートで `python3 -m http.server 8000 --bind 127.0.0.1`、`http://127.0.0.1:8000/site/stage2b/` を開く。公開サーバやPagesへデプロイしない。Three.js 0.180.0の外部CDNが必要。CIでは同じ未変更配布物をローカルroute mappingし、CDN配信そのものは検査しない。版選択、回転、ズーム、リセット、図面・manifestへのリンク。並行ロードは世代番号で古い完了を無効化し、失敗時は以前のモデルを成功として残さない。

## 検証区分

実FreeCAD/Blenderのheadless/background実行、ネイティブ保存・再読込、STEP再読込後メッシュ変換、GLB再読込を、GUI手操作とは区別する。Playwright Chromium/WebKitは375/390/765/1280px×通常/reduced-motionの16条件。故障はGLB404、旧モデルへのすり替え、WebGL喪失を各エンジンで検査する。実機iPhone Safari・物理タッチ・GUI手操作はNOT_TESTED。

TechDrawはネイティブ投影図の存在と外部SVG投影の成功、寸法参照の成否を個別に扱う。寸法文字を置けたことをネイティブ寸法拘束の成立と呼ばない。詳細はCAD auditと失敗履歴を参照する。

最終HEAD・CI原ZIP・独立レビューの判定はPR本文と正式レビューに記録する。研究上の確証不足とソフトウェア検証を分離する。

## 独立反例からの修正

独立担当が初回SVGの平面図の欠落、ネイティブ投影の縮尺消失、図面改変の誤受理、未検証寸法のPASS偽装、台帳の横木断面と生成形状の不整合を発見した。旧原本と反例を保全し、投影transform・実寸の補助線・Custom縮尺/配置保存・図面検証・横木断面契約を修正した。

SVGは今回の3版に限り、独立目視した出力hashを期待値として固定する。新規改訂へ一般化した図面検査ではない。寸法計測JSONはCAD/台帳の数値から別計算し、ページ上の線分長÷縮尺が表示寸法に一致することも検査する。将来の版追加は図面の再レビューと期待値更新が必要。ネイティブ寸法参照のNOT_TESTEDを改変してPASSにすることは拒否する。

CLI pushは認証不足で失敗したため、正式GitHub APIのblob/tree/commit/refで提出する。Git push成功とは表現しない。

## Shallow checkout

初回提出後、既存workflowのdepth1相当cloneで基準commit不在による失敗を再現した。既存workflowを変更せず、Stage2Bの研究検査に限定fallbackを追加。基準commitが存在する場合はGitの原bytesから再構築して照合する。基準commit不在かつGit自身がshallow=trueと報告するときだけ、SHA256固定bundleと全研究・補助資料の現行bytes、研究ファイル集合を照合する。非shallowの欠落や任意commit、bundle改変を救済しない。これは履歴取得を実施したとの主張ではない。REDとGREENを保存する。
