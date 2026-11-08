# 第3層 独立レビュー初回

確認日: 2026-11-08。主担当の作業ディレクトリから別ディレクトリへbyte snapshotを作り、独自反例で確認。GitHub remote/CIはまだこのレビュー対象ではない。

## 正常系・意味の確認

- 独立環境の既存・新規184試験は184 PASS、0 FAIL、0 skip。
- 比較1件と競合仮説2件、SRC10/OBS6集合を参照。田中城の19柱穴を個体19レコードに展開していない。
- 山中城の柱穴列と小径木等の同一構造への帰属を未確認と記載。初期2仮説はunverified/Cで、CADパラメータはnull。
- 数値比較は田中城の既存測定値への厳密参照。残存深さ・当初根入れ、芯々・縁間を区別。
- 報告事実と報告者解釈を別種の参照とし、HYPからHYPを証明根拠として参照できない。競合関係の循環は証明とは別で許される。
- 原報告書、図版、現地、CAD実行は本独立レビューでは未実施。考古学的確証を意味しない。

## P2候補

1. 状態変更の根拠不足: under_reviewからunverifiedへ戻すrevision2を、evidence空配列で受理。状態変更の根拠必須契約を満たすなら、降格でも変更根拠を構造化して保持する必要がある。
2. 棄却根拠の非対応: rejected状態のrevision evidenceにcounterevidenceではなく既存supportを指定しても受理。partly_supportedはsupportとの対応を検査する一方、counterevidence/rejectedは配列の非空のみ。少なくとも状態根拠と反証候補の対応を検査すべき。

## 追加確認点

- 過去snapshot内のOBS-9999参照をhash再計算すると受理。予定CIの旧版不変照合で防ぐなら検査実装と反例の証拠が必要。スキーマ検査だけでは過去参照の実在を証明しない。
- CADのrestorer_hypothesis基準/null値に他城OBS6を紐付けると、comparisons=[]でも受理。他城参照を許す全basisで比較限界が必須か、仕様を明確化する必要がある。
- 他城だけを支持候補としてpartly_supportedにする入力も受理。ただし比較限界と適用説明があれば研究上の限定支持を許す設計もあり得るため、自動的に欠陥とは判定しない。人間の意味レビューが必要。

反例5件はred-results.jsonと各入力JSON、実行コードcontrols.mjsに保存。旧validatorおよび全ソースはsnapshot-manifest.jsonにSHA256を保存。

暫定判定: PARTIAL、状態根拠のP2対応と最終remote/CI照合前の限定マージ推奨NO。
