# Stage 3-D-5D：固定Face 0の実行時判定線・交差Edge診断

## 対象と理由
PR #46の固定Guide BRep、Face 0、OCCT 7.8.1、既存のUV5点だけを1回、実際に動いている分類器内部で観測する。既存のC++ `guide_face0_classifier.cpp`とその5点分類結果、保存pcurve72式・元CAD・D2契約には変更を加えない。線の選択を独立実装で**再演した結果を「native実測」と称しない**。

## 計測方法
診断専用の`face0_trace_hooks.cpp`をELF共有ライブラリとしてコンパイルし、既存の実OCCT分類器バイナリ実行に限って`LD_PRELOAD`する。以下のOCCT 7.8.1公開C++メンバー関数に**実際の動的呼び出しが来た場合だけ**、`dlsym(RTLD_NEXT)`経由で原処理を呼び出した後に、読み取り専用のイベントを追記する。

- `BRepClass_FaceExplorer::OtherSegment`：元のUV点・選ばれた候補判定線の原点と方向・長さ・選択の有無。内部のリトライも順序を保持。
- `BRepClass_Intersector::Perform`：実際に判定線と照合したFace0のEdge、元BRepのpcurve両端、使用向き、呼出公差、BndBoxフラグとgap閾値、IsDone、交差点・重なり数。
- `BRepClass_FClass2dOfFClassifier::Compare`：比較したEdgeの向き、closest intersection indexとその時点でのIN/OUT/ON/UNKNOWN。closest>0のEdgeを候補として抽出。これが最終的な数値誤差の上界というわけではない。

元実行のstdout JSONと、LD_PRELOAD付きの同一C++バイナリが返したstdout JSONを**全内容一致で比較**し、同じ5点への出力が不変であることを確認する。各Edgeは実Face0内の1～8のordinalと、実pcurveの両端2点から固定の保存pcurve使用へ一意に接続する。イベント番号・Query番号・Edgeセット・公差設定を独立に照合し、実際にインターセプトされた判定線と交差点の存在を検査する。

この計測は実関数に対する動的フックであって、静的コードから再構成する擬似トレースとは異なる。ただしELFシンボルへのフックが失敗する場合や、該当する処理がバイナリから直接内部結合されフックを通らない場合もある。その場合は**FAIL/NOT_CAPTURED**として終了し、「どの線が選択されたか」を推測で補完しない。

## 受入・故障対照
- 5点以外を分類しない。新しい点サンプリングを追加しない。
- `face0-trace/hook-events.ndjson` と、`face0-trace/native-interposed.stdout.json`、`face0-trace/native-interposed.stderr.txt`、`face0-trace/trace-report.json`、実行・ビルド終了値、共有ライブラリSHA-256、nm/ldd情報を原artifactに保存。
- Python `verify_face0_trace.py` は実トレースがなければ失敗。欠落した候補判定線、交差結果、外来Edge、異なるFace、五点外、異なるBndBox設定、トレースの欠落/改竄、元5点結果との不一致を拒否する。合成反例 `test_verify_face0_trace.py` は正常なトレースの形式検査であり、OCCTの実実行とは区別。
- 先の原証拠を改変しない。専用CIにトレース用の1ステップだけ追加して原稿・証拠を取得する。外部CADカーネルの導入や他9面・128区間の分析に拡大しない。

## 限界
トレースが収録できたときの限定技術受入は「固定5点について実際に選ばれた判定線と比較されたEdge/最も近い交差候補の記録」である。判定線の中間値・幾何交差器`Geom2dInt_GInter`内部の丸めの形式的証明までは含めない。入力値の量子化誤差0・理想リングの点ごとの頑健距離4/6/0/0/1mmは従来の成果のまま。

OCCTの全数値誤差上界、全点Face集合、実Solidの材料・貫通空洞包含は**UNKNOWN**、代表連続区間は**NOT_TESTED**、PR #46は**Draft・マージHOLD**を維持。
