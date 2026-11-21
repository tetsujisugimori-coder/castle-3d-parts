# Stage 3-D-5D：Guide全10面の「実際の点評価」演算に対する保守的上界

## 問題を3つに切り分ける
今回の既存Guide/Qについて、距離 **1 mm** の誤差を一律に論じない。
1. **元BRepのネイティブSurface係数と表示係数が同じか**。これは実際の`BRep_Tool::Surface(face,location)`から取得し、保存済み全10面との厳密数値照合が必要。
2. **OCCT 7.8.1のPlaneにUV点を渡したときに計算する座標値の丸め**。ソースが定める有限個の四則演算とIEEE-754 binary64・最近接丸めから、全UV領域に対する保守的な上界を導ける。
3. **`BRepExtrema_DistShapeShape`が最小距離を見つける最適化・トリム・収束処理の誤差**。これは2とは別アルゴリズムであり、今回の境界から距離1mmという返値、Face/Edge公差、点評価の誤差上界を組み合わせるだけでは形式的な計算誤差上界にならない。

## 実ネイティブから取得する必要条件
- 固定Guide BRep（FCStd内のGuide.Shape.brp SHA-256 `043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261`）の10 Faceを同一OCCT 7.8.1で走査。
- `BRep_Tool::Surface(face,TopLoc_Location)`の実オブジェクトが**全件`Geom_Plane`**であることを確認。ネイティブの`Geom_Plane::Position()`から実原点とU/V単位方向、Locationの実平行移動、実UVBoundsをbinary64で取得。
- Face 0〜9のネイティブ原点＋Location、U/V軸、Boundsを、元の48件保存pcurveから実際に得た`trim-correspondence.json`の表示世界座標と有理数で直接照合。Locationの`-540,0,+100`を**二重適用しない**。U/V軸が直交する座標軸単位ベクトル`0,±1`で、位置も2進で正確に保存された整数であることを要求する。
- 実CIで`std::numeric_limits<double>::is_iec559`、`digits==53`、`std::fegetround()==FE_TONEAREST`を検査。失敗なら限定PASSを発行しない。
- **Locationの生Formと実効変換を混同しない。** 初回native診断は`NON_TRANSLATION_FACE_LOCATION`で停止。OCCTの`TopLoc_Location`合成で`gp_CompoundTrsf`等のFormを保持していても、実効3×3線形行列が厳密に単位行列かつScaleFactor=1なら幾何的には平行移動。この両条件を実ネイティブから成分ごとに厳密照合し、CentralMirrorや非単位行列は拒否する。Form enumと実効同一行列の両方を原票に残す。

## 根拠となる7.8.1の演算式
- [Geom_Plane.cxx#L251-L253](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/Geom/Geom_Plane.cxx#L251-L253)の`D0`は[ElSLib.cxx#L37-L46](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/ElSLib/ElSLib.cxx#L37-L46)の`PlaneValue`を呼ぶ。各成分 `U*dirU + V*dirV + local_origin` を計算する。
- [BRep_Tool.cxx#L77-L82](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_Tool.cxx#L77-L82)のLocationを適用する際、[gp_Pnt.cxx#L30-L43](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/gp/gp_Pnt.cxx#L30-L43)のgp_Translationなら各座標に平行移動量を加算する。非平行移動変換はこの証明器の対象外。
- `gp_Translation` Formでは直接座標加算を行う。実効変換が単位行列でも生Formが`gp_CompoundTrsf`等の場合は、[gp_Trsf.hxx#L440-L468](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/gp/gp_Trsf.hxx#L440-L468)のXYZ×3×3恒等行列と平行移動の経路になる。後者は`PlaneValue`の4演算に最大約6演算を加えた計10演算/座標成分で、今回採用する16演算の保守的上界内。実際の数値演算がIEEE binary64最近接で実行され、実数UVは入力時に1回だけ正しく丸められるという条件は変えない。

## 数学的な上界
`u=2^-53`、`γ16=(16u)/(1−16u)`。各Faceの成分jについて、実UVBoundsから `Umax=max(|Umin|,|Umax|)`、`Vmax`も同様に置く。ネイティブ原点`O`、単位軸`dU,dV`、平行移動`T`は実バイナリ値として分数で厳密に読む。

`M=|O_j|+|T_j|+Umax|dU_j|+Vmax|dV_j|`、入力丸め上限 `R=u(Umax|dU_j|+Vmax|dV_j|)` とすると、保守的な評価誤差上界は

`E_j = γ16(M+R)+R`。

これは実際にはほぼ5演算の経路を16演算で包絡した値である。軸・原点が正規化された線形式であることを実BRep原票で確かめて初めて、この限定証明を使う。各Face・成分の上界の最大値を`E`とする。任意のUV点の座標誤差のL2距離は`√3 E < 2E`、距離の三角不等式から

`dist(S_native_D0_float(U,V), Q_exact) >= 1 mm - 2E`

が**面の直接座標評価という操作に限り**条件付きで成立する。Python側は全式を`Fraction`で計算し、十進出力には必ず外向き丸めを使う。前工程の10 Faceの数学的トリム領域・48件保存pcurve・距離1 mmのPASSを前提として固定する。

**注意**：この距離下界は、Qを既存D2の正確な閉直方体としたときの`Geom_Plane::D0 + Location`による座標値の評価誤差に対するもの。OCCTが内部で選択するpcurve上のパラメータ位置誤差、任意のアルゴリズムの計算分岐、`BRepExtrema`が報告する最短距離の収束誤差、丸めモードを変えた実行、実Shape全体の空洞包含、連続閂運動には拡張しない。数値の正値を得ても`native_full_q_void_inclusion=UNKNOWN`、`brep_extrema_total_error_status=UNKNOWN`を維持する。

## CIと反例
既存PR #46の専用CIの全10面検査直後に、実BRepから直接生JSONを採取し、その記録値を照合して式を計算する1 stepを追加する。合成テストはSurfaceの原点移動、U/V軸の非単位化、Locationの変更、UVBounds変更、丸め条件の不成立、旧QモデルのFAILなどを拒否する。

原CAD、D2契約、48件・72件保存pcurve、既存原artifactを上書きしない。最新固定HEADで正式CI・証拠ZIP再取得と既存manifest/SHAの範囲を確認する。PRはDraft・マージHOLD。
