# Stage 3-D-5 — fixed stored pcurve provenance

対象は [Draft PR #46](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/46) の扉0°、D2第1葉中点35/64 mm、Bolt / Guide 左のみ。元の式は前回固定版 `37f2f0262b6af9b84a2a5944a4eb289e87818600` の [公式原票](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/44762388102/artifacts/14642965077) 内 `one-slice/trim-correspondence.json`（SHA-256 `412e4488136ecb28a59a616c4d33d010ffaf75ff4e3ab962bfcf138920f9afe3`）。公式の既存FreeCAD採取をそのまま再実行し、このハッシュで照合から動かさない。固定FCStd・2件の元Shape.brpは[前回の原本ハッシュ](CONTINUOUS-TRIM.md)を継承する。

## 代表使用と接続

代表は `GATE_Bolt` のFace 0 / Wire 0 / global Edge 0 / ordered use 0（0始まり）。連結点・非seamの直線と平面、同一パラメータ、非identityの全体Locationを同時に確かめられる最小の使用。Face/WireはReversed、Edge使用はForward。pcurve・3D曲線とも `[0,40]`。Surfaceおよび3D Edge曲線の実効Locationは回転なし・並進 `(-25565/64, -115, 1000) mm`、代表使用の両曲線表現の相対Locationはidentity。SameParameter、SameRangeはともにtrue。

固定BRepを修復・保存せずに読み、BoltのLocationだけ既存式と同じ35/64 mmの解析用並進を施す。同じネイティブプロセス内で、

1. [OCCT 7.8.1のFace指定API](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_Tool.cxx#L261-L313) が返した保存フラグを明示取得する。
2. indexed overloadで同じSurfaceハンドル・実効Locationに該当する保存表現を列挙し、そのうち唯一のpcurveハンドルと区間の一致を要求する。代表はedgeの保存pcurve列挙2件中1件、選択rank 1（1始まり）。
3. 実Edgeの `BRep_TEdge::Curves()` でも相対Location付きの曲線表現を照合する。代表の2D/3D表現のordinalはそれぞれ2 / 1（1始まり）。別プロセスでポインタ値を比較しない。FreeCADの表示係数への接続は固定入力、位相インデックス・Face–Wire–Edgeの順序、配向、Location、区間を先に照合し、最後に前回と同じ係数を比較する。係数やハッシュだけで保存由来を認定しない。
4. 両実行プロセスについてロードしたOCCT実体の実パスとSHA-256を照合する。バージョン文字列だけでは合格させない。原票にABI、FreeCADモジュール、コンパイラ版を残す。

## 展開ゲート・対照

代表PASS、合成レコード対照（正常1、故障12）と、OCCTで保存表現のない平面上のEdgeから**非nullの生成pcurve**が返る対照を確認してはじめて全件を取得する。故障対照は保存なし、生成の誤認、範囲ずれ、トポロジーおよび実効Locationずれ、対象使用・向き・順序違い、フラグfalse/取得不能、複数表現候補、seam不明。合成対照は原BRepの変造を含まない。seam・多義的な表現・未対応型は成功にしない。

開発中の最初の展開ではGuideの16使用を、Surface LocationがFaceの位相Locationと異なるという理由で誤って拒否した（初回レポートSHA-256 `e82542525cf792d7d83593fde214e6824bf7ad0642ca21f51fb9498f91411b7a`）。実効Locationと位相Locationは一般に別物であるため、実効 $`L_{edge}L_{representation}`$ を別に確認し、旧位相Locationと旧世界係数を両方維持する方式へ是正した。異なる実効Locationへすり替える対照は引き続き拒否する。

## CIと受入範囲

既存専用workflowのDebian環境で開発パッケージを使い、`stored_pcurve.cpp` を実体ライブラリへリンクする。既存テストと同じ `one_slice.py` で得た式を `verify_stored_pcurve.py <binary> <trim-correspondence.json> <new-evidence-directory> <new-input-directory>` へ渡す。BRepコピーは原ZIPの外に置く。出力は代表判定、対照、採取生JSON、各使用の明示判定、終了値とruntime/ABIの根拠。単体試験は `python3 -B -m unittest discover -s cad/stage3d5d -p 'test_*.py'`。

限定受入は保存pcurveと既存の表示係数の式を正しく関連付けるところまで。SameParameter/SameRangeのtrueをネイティブ実曲面の厳密等式・誤差ゼロ・材料側の集合証明へ昇格させない。既存P1の式、P2の候補判定は維持。実材料外側・実空洞内側・有限実誤差・全状態はいずれもUNKNOWN。代表連続区間はNOT_TESTED、総合PARTIAL、Draft・マージHOLD。

初回の[正式CI](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/44768211413)（HEAD `14c9b1db`）は、Debianのヘッダー `NCollection_AliasedArray.hxx` がなくコンパイルで終了し、代表／全件は未到達。[正式失敗原ZIP](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/44768211413/artifacts/14644249380) は保持する。不足していたヘッダーは[Debian amd64のlibocct-visualization-dev](https://packages.debian.org/trixie/amd64/libocct-visualization-dev/filelist)に属するため、CIの同版開発依存だけを追加する。ビューや表示処理は実行しない。C++/Pythonの式・合否条件・原BRepには変更なし。
