# Stage 3-D-5 Guideの閉材料・両端開放空洞の分離検証

対象：Draft PR #46 の固定Guide（GATE_BoltGuide_Left）、扉0°、D2第1葉 [0,35/32] mm、代表姿勢35/64 mm。元BRep・契約・既存72式とその原票は変更しない。

## なぜ材料と空洞を別に扱うか
(1) 実Solidの材料集合が候補外側境界の内側にあること（外側包含）と、(2) Guideを貫通する閉通過領域が実Solidの開補集合に入ること（内側包含）は異なる命題。追加の薄い仕切りや閉塞面は、(1)に反しなくても(2)に反する可能性がある。候補有理数モデルでは既存の全境界・原子セル検査で(1)(2)を別々に検証済み。これをOCCT実集合へ昇格させるには別の橋渡しが必要。

## 今回の追加した診断の根拠
- 既存の保存pcurve72/72 PASSのうちGuide48件を固定したまま、全10 Face・12 Wire（外輪10・内輪2）の向き付き使用48件と、一対一対応する保存pcurve使用の集合・順序を確認する。既存のtrim-correspondenceのFace側の候補材料側判定もそのまま再利用する。
- D2固定契約から導いた材料側、内壁の空洞側、穴中心、上下の壁、貫通穴の両端外部、外側空間の12点を、正確な整数mmとして固定する。候補モデルに対するIN/OUT期待値は直方体の厳密有理数演算から別に求める。境界点は許可しない。
- 同一CI環境で固定Guideの元BRepを読み、OCCT 7.8.1 BRepClass3d_SolidClassifierが報告する各点のIN/OUT/ON/UNKNOWNを取得。ソース・対象BRep・点一覧・実行値・終了値を原artifactに収録する。分類にはPrecision::Confusion()を使用し、その実値も記録する。これはカーネルの判定公差であり、幾何誤差の上界ではない。
- 明らかに異なるサンプル状態、原BRep変更、保存pcurve使用の欠落、inner Wireの消失、順序の違い、片方向の候補包含だけのPASS昇格を拒否する。実BRepを改変した故障試験ではなく、合成記録の故障試験として区別する。
- 元のall-point証明、面・Wire・Edgeの連続対応、finite error、全状態の位置・分類については既存の限定結果を保存する。有限個のSolidClassifier結果を増やしても全点集合の数学的な同値性は証明できない。

## 判定
今回は、全Face/Wire/Edge使用の*観測済みの向き*と保存pcurveの一対一対応、および代表領域12点のnative分類がD2有理数モデルと矛盾しないことを限定PASS/FAILとして判定する。

ただし、材料の「実Solid外側包含」と「実空洞内側包含」は両方ともUNKNOWNを維持する。OCCTのFace/trim/pcurve/3D曲線/Orientationから実際の全点占有集合を導く根拠と有限実誤差、全状態の配置同値性は別の証明義務である。代表実区間NOT_TESTED、128区間NOT_TESTED、総合PARTIAL、Draft・マージHOLDを維持する。

原票：追加のguide-solid/guide-solid.json、sample-requests.tsv、occt-classifier.stdout.json、occt-classifier.stderr.txt、専用build stdout/stderr/exit、既存のstored-pcurve・trim・boundary原票とroot SHA manifest。承認範囲外の新規長期保全・独立再監査を一律追加しない。必要な既存形式でのartifact取得とSHA/CRC再照合を行う。
