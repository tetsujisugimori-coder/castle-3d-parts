# Stage 3-D-5D：Guide Face 0をOCCT FaceClassifierで5点直接照合

## 目的と固定条件
- 固定Guide Face 0（負X端面、Reversed、外輪1と内輪1）を、同じBRep／OCCT 7.8.1で直接分類する。
- 既存の厳密な表示係数モデル、8件の保存pcurve、72件の全検査、D2は変更せず再利用する。既存PR #46のDraftを維持。
- 新規診断はFace 0のみ。ほかの9面、Solid全体、0〜35/32 mmの連続移動は対象外。

## 前提モデル（数学的領域）
Surfaceの表示係数 S(u,v)=(-200,-130-v,990+u) mm。
R=[0,60]×[-130,0]（外輪を含む）、H=(9,51)×(-36,-14)（内輪の開内部）。
D=R\H と定義し、内輪・外輪境界を面に含める。表示係数の厳密候補モデルとD2端面の同値性は前工程の face-region.json で限定PASS、面積6,876 mm²。

## 固定5点
| UV (mm) | 数学的な位置 | OCCTの期待状態 |
|---|---|---|
| (5,-20) | 面内部 | IN |
| (20,-20) | 内輪の穴内部 | OUT |
| (9,-20) | 内輪境界 | ON |
| (0,-20) | 外輪境界 | ON |
| (-1,-20) | 面外部 | OUT |

境界が数学的にFace集合に含まれることと、有限公差の分類APIがONを返すことは別概念である。OCCTの実測が異なった場合は原値を残し、判定はFAILまたはUNKNOWNとする。公差の値を結果合わせのため変更しない。

## native採取
新規 guide_face0_classifier.cpp は元Guide Shape.brpを読取り専用で開き、OCCT 7.8.1の TopExp::MapShapes でFace 0（0始まり）を選択。Face総数10、Face orientation Reversed、Wire数2を検査する。BRep_Tool::NaturalRestriction / Tolerance / Surface(F,Location)、BRepTools::UVBounds、面のアフィン枠とLocationを記録する。BRepClass_FaceClassifier::Perform(face,gp_Pnt2d,tol) で固定5点を直接分類し、素のJSONを証拠に残す。tolにはPrecision::PConfusion()を使用し、実値を原票に残す。

verify_face0_uv.py は既存face-region.jsonのPASS、原FCStd/D2/BRep SHA-256、Face幾何枠/UVBounds/NaturalRestriction等を検査し、数学モデルから導いた期待状態と実nativeの5状態を照合する。失敗はFAILであり、BRep原物を修正・再保存しない。

## 限定判定と証明の境界
- 5点が期待通りなら「固定Guide Face 0の5点に対するOCCT FaceClassifierによる数値分類整合」は限定PASS。
- NaturalRestriction=falseを明示取得できれば、自然なパラメータ矩形だけではなくWireによって領域制限されるFaceであることの補助証拠となる。ただしtrue/falseだけで全域の同値性は証明しない。
- OCCT 7.8.1の BRepClass_FaceExplorer は分類のため元FaceをFORWARDに正規化し、向き付きWire/pcurveを走査する。BRepTopAdaptor_FClass2d は浮動小数による輪郭離散化と公差判定を含む。5点の一致はこの実行の観測値であり、無限に多い全点の形式的同値性を保証しない。
- 実際のnative面集合と候補連続領域の厳密な同値、有限実誤差の上界、全Solid材料/空洞包含、連続運動の安全PASSはUNKNOWN/NOT_TESTEDを維持する。

## 証拠・受入
専用CIは既存のFreeCAD・保存pcurve・face-region検査の後に、コンパイル・FaceClassifier5点実行を加える。出力はface0-uv/native-face0.stdout.json、native-face0.stderr.txt、face0-uv-report.json、コンパイルstdout/stderr・終了コード、検証stdout/stderr・終了コード。固定HEADの実行と原artifactの必要最小限の再取得・CRC・SHAを確認する。

既存証拠を再保存しない。新規独立CADカーネルや余分な多数点サンプリングを必須化しない。原結果が成立してもDraftとマージHOLDは継続。
