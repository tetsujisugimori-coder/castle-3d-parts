# Stage 3-D-5D: Bolt/Guide固定BRepの境界対応と証明範囲

## 対象
統合済みPR #39の基盤からPR #46の代表診断を拡張する。固定SHAのFCStd内のBolt/Guideと固定D2契約を使用し、扉角度0°、D2 ordinal0 [0,35/32]mm、代表35/64mmだけを対象とする。既存CAD・履歴・PR #40/#41は変更しない。

## 厳密な有理数モデル内での証明
1. FreeCADの全頂点/Edge/Wire/Faceを取得し、未参照・開いたwire・非Plane/Line・非多様体・trim欠落を既存の全インベントリ検査で拒否する。Solidが1個で閉じて有効かどうかも観測するが、それ自体はnative実集合同値の証明ではない。
2. 全Lineの保存IEEE係数をFractionへ厳密変換し、origin+t*directionの両端が対応する頂点と一致するか調べる。Affineモデルの全パラメータについて成立する式の検査であり、nativeのpcurve/Surface実体への橋渡しは含まない。
3. 全Planeとtrimから有理数ポリゴンの閉材料集合を再構築する。巻き方向を候補モデル向けに正規化した場合は操作を全件記録し、nativeの向きの意味はUNKNOWNに保つ。
4. D2のBolt直方体とGuideの4個の材料直方体を独立の期待集合とする。双方の全端点が作る共通格子上で、全開原子セルの占有を厳密に照合する。各正体積閉直方体の有限和は内部の閉包と一致するので、相互包含によって表現モデルの材料集合の等しさが境界を含めて従う。これは任意の実CAD曲面の有限点サンプリングとは違う。
5. Guide候補の閉材料の開補集合へ、閉通過領域が厳密に入るか調べる。接触はFAIL。全原子直方体間の最短距離二乗をFractionで求め、mm²で保存する。Bolt/Guideの候補間距離も同じ式で照合する。一姿勢の表現モデルの結果のみでありnative区間安全性は認めない。

## 実CAD安全性へ昇格できない理由
FreeCADが返した浮動小数/トポロジ/Line/Planeが、OCCTの全trimmed surface・pcurve・3D曲線・OrientationおよびSolidの実材料側と完全に集合同値である根拠は未成立。isValidやSameParameter等の観測だけで連続実集合を証明しない。保存Shape、Document、Parent、World配置の同値性、有限なnative実誤差上界、全姿勢の連続運動の根拠も残る。Boolean体積0や正距離はそれらの代用ではない。

したがって実材料包含・実空洞包含はUNKNOWN、実代表区間および128実区間はNOT_TESTEDのまま。解析128 PASSと混ぜない。

## 反例と収録
全辺のLine端点ずれ、trim欠落、法線反転、片方向だけの包含、想定材料の拡大、空洞との接触、欠落した候補を合成入力で拒否する。合成正常/故障と実FreeCADは必ず別ラベルにする。

専用workflowのnative jobは新規のboundary-correspondence.jsonに全取得トポロジと条件付き対応証明を保存し、report.jsonにはサマリーを入れる。固定SHA、checkout HEAD、元のerror/失敗ログ、収録原物を保持する。失敗原物は成功原物に置換しない。

**限定合格**は表現モデルの双方向一致と開空洞の厳密包含のみを意味し、OCCT-native実集合の安全PASSではない。
