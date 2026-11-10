# Stage 3-C 木戸の閉鎖機構・接合詳細

Issue [#28](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/28)。対象は castle-3d-parts のみ。山中城側を変更しない。

## 固定基準

Stage3B PR27はmerged。main `34956e1978794aa3d4858c564c51da37d84bfa27`、tree `ff66be2a6ba179d400be3a7e8fe6d4ee4a14eb83`。着手時の全追跡ファイルを `evidence/stage3c/baseline.json` にSHA-256記録。既存CAD、STEP、blend、GLB、研究台帳は不変とし、新候補をcad/stage3cへ分離する。既存のWeb機能を再利用する共通化は、許可されたファイル一覧と差分で説明し回帰検査する。

## 根拠と試作

`research-boundary.json` はSRC→OBS→HYP→DEC→VERをStage3C名前空間で結ぶ。旧台帳のheld/reference_onlyや現況情報を変更しない。

[JAANUSの閂](https://www.aisf.or.jp/~jaanus/deta/k/kannuki.htm)の一般語義と保持部材の説明を確認した。掲載の類例を戦国末期山中城の実測・標準仕様へ転用しない。[木戸門](https://www.aisf.or.jp/~jaanus/deta/k/kidomon.htm)の構成説明も一般比較に留める。資料画像は転載していない。

[三島市の環境整備説明](https://www.city.mishima.shizuoka.jp/page/1301.html)は西木戸口等の整備範囲と修景表示を述べるが、今回必要な閂・支持・仕口寸法の根拠を取得したわけではない。考古学的な木戸閉鎖機構は未確認。CAD値はすべて試作D。

## 動作契約

CADを形状・寸法・軸の正本とし、そこから抽出した共通仕様でWebの入力を制限する。閉鎖姿勢以外で閂移動を拒否し、閂が完全に引き抜かれていない場合は開放を拒否する。途中位置も施錠/解錠の二値へ丸めず表示する。不正入力は状態を変えない。

幾何学的接触、状態機械による拒否、実物の荷重伝達は異なる。ソフトウェアが開放を拒否しても、実物が施錠力に耐える証明ではない。支持接触があっても摩擦、変形、木材強度、締結、摩耗はUNKNOWN。

## 検証範囲

BRep common体積とdistToShapeによる標本検査を使用する。BBox重なりを貫通の最終判定にしない。連続角度・直動の標本間は、別の証明がない限りUNKNOWN。検査した標準形状以外のパラメータへ保証を一般化しない。

FreeCAD Qt offscreenおよびBlender backgroundの実起動・保存再読込と、人によるGUI操作は区別する。実機Safari、物理タッチ、手動GUIは記録がない限りNOT_TESTED。

候補Webビルドのみ。本番Pages、マージ、Draft解除は行わない。
