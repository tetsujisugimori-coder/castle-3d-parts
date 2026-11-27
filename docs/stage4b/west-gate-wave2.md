# 西木戸口・左右の門（Stage 4-B 第2便、試作D1）

[#55](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/55)。基準 main `e4f0247b34fe3ab9ac0a96bbb6bdbab0e86c135d`、tree `f32490e2a6043da1148679b020d2024f5be79db5`。第1便 #53（マージ `eaabc5fe0a2514c4fad7cdf7a51f862c1134c5bb`）と組立単位の方針 #54 は統合済み。D0の資産・別カタログ・展示を残す。今回は門扉と支持の基本構造を工房内で試作し、史実としての復元、実物の製造、採用や配置を承認しない。

## 基準の区別

| 根拠と確認箇所 | D1への反映と限界 |
|---|---|
| [三島市・山中城跡の発掘調査](https://www.city.mishima.shizuoka.jp/page/2145.html) §3 建物 | 北ノ丸の発掘遺構は門柱の存在を考える城内の別例。西木戸口の本模型の寸法、仕口や軸受を発掘確認したものではない。 |
| [三島市・環境整備事業](https://www.city.mishima.shizuoka.jp/page/1301.html) 49・50年度 | 西木戸口の整備箇所を確認。工事記録を戦国期の門扉寸法や型式の証拠にしない。 |
| [山中城 #64](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/pull/64) / [推定Cの固定制作式](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/blob/c4888f96f4d46db7d571055896004852c02050df/scripts/phase3b-build-blender.py#L88-L106) | 左右の板材・桟・門柱の区別を参照。D0で整理済みの板材・桟正本をそのまま使う。D1における左右対称・扉の平面化・閉鎖隙間・柱芯・支持構造は、Cの地形座標や部品寸法をそのまま転写したものではない。 |
| [大野城心のふるさと館・北石垣城門の軸受遺構](https://www.onojo-occm.jp/kiji0036723/index.html) | 別時代・別城の軸受着想に限る。木柱・リング・腕や金属色の根拠ではない。D1の径、高さ、クリアランス、開き方向、材質色はいずれも操作・組立検証の仮定。 |

## 部品と提供仕様

試験導入候補 ID `YAM-WEST-GATE-BASIC D1`。閉鎖例は [v2 example.json](../../assembly/stage4b-wave2/example.json)、処方は [design.json](../../assembly/stage4b-wave2/design.json) と [poses.mjs](../../assembly/stage4b-wave2/poses.mjs)。[カタログ](../../assembly/stage4b-wave2/catalog.json) と [SHA256SUMS](wave2-SHA256SUMS) で配信用と各正本のバイトを固定する。利用時は採用した**固定PRコミット**とファイルハッシュを引継ぎ票に記録する。カタログの baseline は本便開始時のライブラリmainであり、新規ファイルの作成コミットではない。需要は [YAM-004/005](../../assembly/stage4a/yamanaka-demand.json) に反映した。

| 正本ID／版 | 数 | 名目寸法・原点 |
|---|---:|---|
| YAM-WEST-LEFT-BOARD D0 | 12 | 270×130×2850 mm。元の板下隅。右用コピーを作らず、X方向に鏡対応する配置のみ。 |
| YAM-WEST-LEFT-RAIL D0 | 4 | 1850×170×150 mm。元の桟下隅。上・下、左右で同一正本。 |
| YAM-WEST-POST D1 | 2 | 300×300×3000 mm。柱底面中心。左右とも同じ正本を180°変えて配置。 |
| YAM-WEST-BEARING D1 | 4 | 200×100×50 mm 包絡。座面軸芯。外径100、内径54 mm、側方ブラケット付き。 |
| YAM-WEST-PIVOT D1 | 4 | 155×50×110 mm 包絡。ピン底面軸芯。径50 mm。回転腕を一体の展示部品にした。実接合や軸方向保持は未設計。 |

各D1部品は [FCStd / STEP / 配信GLBとmanifest](../../cad/stage4b/west-gate-wave2/) および [編集用Blenderファイル](../../blender/stage4b/wave2/) を持つ。右手座標で Z 上。Xは幅、Y正は扉裏および開く方向。CAD mm、工房/GLB m、名目1:1。glTF表示は `(x,y,z)→(x,z,-y)` を一度適用する。現地座標、方位、基礎高、模型を実物へ転用するときの荷重や施工はUNKNOWN／NOT_TESTED。

- 左は閉鎖時 X<0、右は X>0。柱底面中心 `(±2300,200,0)`。回転軸 `(±2000,200)`、支持ステーション Z=400/2100 mm。板底面 Z=20 mm。門の中心線 X=0、中央閉鎖隙間40 mm、柱間内法4300 mm。固定比較姿勢は左 +90°、右 −90°。任意角アニメーションや荷重を扱う工房機構ではない。
- 柱・軸受の取付面、軸受・ピンの軸芯に8本のv2関係を保存。軸芯は部品基準線の一致で物理的滑り止めや荷重伝達の証明ではない。ピン腕と桟、桟と板は幾何学上の面接触で、釘・ほぞ・蝶番の現物仕様は主張しない。径54/50 mmの半径方向の遊び2 mm、腕と軸受上面に10 mm。抜け止め、浮き上がり、耐力、基礎への定着、回転運動安全性、既存Stage 3の実Solid一般判断は未検証。
- 既存展示から第2便へ進み、左右単独、柱、軸受、ピン、4姿勢を観察。工房リンクは表示中の固定姿勢を引き継ぐ。工房で固定姿勢を選ぶと現配置を置換するため、編集配置は先に保存する。既存v2形式で個別の部品ID・姿勢・位置・関係を保存・再読込。旧カタログとSHAが異なるため、既存の保存ファイルは旧画面で開く。
- 山中城側は変更していない。次は山中城での別承認の試験導入（推定Cの差し替えを意味しない）。第3便の候補は、証拠がある範囲での基礎・支持および門上部の設計単位。屋根・周辺柵・石垣は今回外。

## 検査・再生成

```bash
node scripts/stage4b/wave2/catalog.mjs --check
node --test
node scripts/build-stage2d-site.mjs
node --test scripts/stage4a-pages-check.mjs
node scripts/stage4b/wave2/poses-json.mjs > 独立作業領域の新規poses.json
# Debian 13 / FreeCAD 1.0.0 / OCCT 7.8.1
env PYTHONPATH=/usr/lib/freecad-python3/lib LD_LIBRARY_PATH=/usr/lib/freecad-python3/lib QT_QPA_PLATFORM=offscreen /usr/bin/python3 -B scripts/stage4b/wave2/native.py --poses 独立作業領域のposes.json
blender --background --factory-startup --python-exit-code 1 --python scripts/stage4b/wave2/mesh.py -- check
```

再生成は既存固定資産を置換せず、別作業コピーの空のWave 2資産ディレクトリで `native.py --generate --mesh 新規mesh.json`、続いて `mesh.py -- generate mesh.json`、`catalog.mjs --generate`。再生成時間とツールビルドによりバイトが変わる。正式証拠の扱いは中央規約と案件個別承認に従い、再生成物は過去実行の原票と同一視しない。

ネイティブ読戻しはFCStdとSTEPを解析形状と差集合で比較し、単純な外接寸法のみを根拠にしない。固定4姿勢では各26ソリッド・325組を境界で候補化して正体積交差を検査、各32面の指定接触を照合した。ピンと軸受のみ別途0–90°を5°刻みの19点で確認し、4 mm偏心を負対照で検出。葉と柱・対向葉は一次元投影の91サンプル。これは有限サンプルと設計矩形の参考値で、現物や任意編集後の安全保証ではない。Blender原本とGLBは個別に再読込し、閉じた面、向き、体積・境界を照合する。実機Safari、実部材試験は対象外。
