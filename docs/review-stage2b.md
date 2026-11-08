# Stage 2-B 独立レビュー作業記録

実装担当とは別の担当による監査。最終提出HEAD・CI原artifactの確認前であり、本書だけで最終PASSとはしない。

## 独立実行

- 基準commit `34f43b3b1765de7a52994adb7175dc2c146f8db3` の451ファイルを `git show` から直接読み、現行bytesと全一致を確認した。主担当の保全manifest判定をそのまま追認したものではない。
- 独自 `reopen.py` でB0/B1/B2のFCStdをFreeCAD 1.0.0で再読込。14 solids、全体寸法、STEP再読込bounds、部品ID、パラメータ編集/recomputeを確認。
- 独自 `blender_reopen.py` でBlender 4.3.2からblendとGLBを各版再読込。14 meshes、各post中心座標、高さ、B2混版ID、D/reference_onlyを確認した。
- これはheadless/backgroundの実ソフト実行であり、GUI手操作・実機Safari・施工強度の試験ではない。

## 指摘と反例

1. **P2 図面表示欠落**：当初SVGのTOP投影が縦に回転しページ下端へ切れた。線が非常に薄く、同長の寸法線は形状に接続していなかった。Inkscapeで独立レンダリングして検出。`drawing-before.png` を保全した。
2. **P2 ネイティブ投影縮尺**：FCStd再読込でScale=1.0となり、意図した.018が維持されなかった。ScaleType=Custom/.02へ修正後、独立再読込で.02を確認。view位置の保存順についても主担当側が追加修正中。
3. **P2 図面と検査の分離**：SVG寸法10950→99999または投影g削除を再hashするとfullCheckが受理。図面内容自体の契約が不足していた。`counterexamples.mjs`、`red.json`、旧検証ソースを保存。
4. **P2 未検証の昇格**：native_linked_dimensions/native_dimension_statusをPASSへ変更してもvalidateAudit受理。実際の未成立寸法参照と状態判定の結合不足。
5. **P2 rail寸法の無視**：全版のrail.width_mを9mにし親hashを再計算してもvalidateSpecが受理。CADはpost.width*.66を使い台帳rail値が検査されていなかった。`rail-counterexample.mjs`、`rail-red.json`。

最初の反例ハーネスではGitコピーを省いたため、意図した検査前にGit不足で停止した。その実行は成功対照に数えず `harness-missing-git.json` として残し、Gitを含むコピーで再実行した。

## 図面修正の目視

修正版B2を独立Inkscapeで描画。正面・TOP・側面がページ内に収まり、柱高2400、間隔1200/1300、全幅11150、横木中心高800/1600、深さ249mm、D/reference_onlyが表示されることを確認。`drawing-B2-after.png`。

TechDrawネイティブ投影と、FreeCAD形状投影から作るSVG寸法線は別工程。ネイティブDrawViewDimensionの有効リンクは未検証であり、SVGの成功をその成功に置き換えない。

## 保留

同一反例GREEN、最終成果の新規remote取得、最終CI原ZIPのSHA/API digest、原PNG/JSON再計算、正式GitHub COMMENTレビューは完了後追記する。現時点のマージ推奨は未判定。

## 修正後の独立再検証

追加54試験成功を独立実行で確認。rail寸法の同一反例は `RAIL_SECTION` で拒否へ改善。旧SVGの同じ破損bytesを保存済み旧検証ソースと新検証ソースへ与え、旧ACCEPT→新DRAWING_GOLDENを確認。誤寸法SVG SHA256は `d921b817a70fe5df79d0528485840d316a87e6014a65ee16fff99ee1482d5f4f`、投影欠落SVGは `44cca659a29d56f1b491ef791e3cbe83ae7e7b7634f0520c0699c020f4c9b243`。旧検証の3-script契約と新4-script契約は各々に合わせたfixture metadataを使い、破損SVG入力自体の同一性を固定した。

新形式SVGでも実際に文字列・投影が変化したことを検査した上で拒否を確認。無変化のreplaceをGREEN扱いしていない。native状態をPASSへ昇格する2反例は `NATIVE_DIMENSION_STATUS` で拒否。

修正後の実スクリプトを独立担当が再実行し `/tmp/stage2b-independent-replay-02` に新規生成。各版のGLB、SVG、寸法測定JSON、mesh bytesが提出版と一致。cad/blender audit JSONも一致。`replay-comparison.json`。FCStd/STEP/blendのバイナリ一致を主張せず、実再読込で寸法・構成を検査した。

縮尺はネイティブ3viewとも.02。図面Golden検査は今回のレビュー済み固定3版限定で、将来任意モデルの一般的な製図検証器ではない。新改訂には再生成と独立図面レビューが必要。

ローカル修正範囲の未解決P1/P2は現時点で確認していない。TechDrawネイティブ寸法リンクはNOT_TESTEDであり、依頼全体を完全PASSとしない。最終remote/CI証拠と正式レビューは引き続き保留。
