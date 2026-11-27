# 城郭3D部品ライブラリ 開発ロードマップ追補

2026-11-27 JST。2026-11-24ロードマップを置き換えず、Stage 4-B以降の提出単位と西木戸口を追補する。

1. **Stage 4-A 組立基盤**：[#47](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/47)の部品組立データ基盤、山中城向け需要台帳、工房の編集・保存・再読込、展示室と工房の相互移動を活用する。展示室の個別部品観察の役割を残す。[第1便の記録](stage4a/README.md)・[配信統合 #51](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/51)。
2. **Stage 4-B 部品を建築単位で提供**：個別のCAD試作・形状検査を許容しつつ、成果・試験・資料は建築上意味のある組立単位で提出する。第1便は [#52](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/52) の左門扉、板材6配置と上下横桟2配置。正本と配置を別管理。根拠が不足する接合は仮定またはUNKNOWNで、史実・強度・実稼働を認定しない。
3. **後続**：需要と根拠を照合後、右門扉、門柱、門全体、城別採用に分けて判断する。今便に含めない。開閉、荷重、連続運動は別研究。西櫓等の他需要は未配置・未採用のまま扱う。
4. **役割と受入**：歴史体験側は優先順位、部品ライブラリは根拠・正本・版・組立技術試験、山中城側は城内での採用・配置・公開。Draft提出→CI→独立レビュー→必要な証拠保全→明示承認の順とし、限定受入だけで公開や採用を進めない。

Stage 4-B 第2便の提出候補は [西木戸口の左右の門（D1）](stage4b/west-gate-wave2.md)。山中城での試験導入は別判断。第3便候補は基礎・支持と上部構造の設計単位で、史料上確認できない点を最初に切り分ける。

## 2026-11-28：Stage 4-B 第2便の限定受入・公開

- [Issue #55](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/55)・[PR #56](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/56)：D1の左右門扉・門柱・支持部品を限定受入。対象HEAD `4b50b1517dc315cbc356cf02859a62f633d0548d`、mainマージ／公開コミット `8f07c93ce0ed9a68dcae03d0debb5fd21ba43e6d`、両者同一tree `3cbd845807f63f3819b91ba90493e41d24197697`。[Pages run 46078977673](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/46078977673) 成功。
- [需要台帳](../assembly/stage4a/yamanaka-demand.json) の YAM-004/005 はライブラリ公開済みの試験導入候補。採用・配置は未承認で、山中城側の成果は変更しない。
- WebKit専用APTの `file://` 混在検出は非阻害P3としてOPEN。ランナーや設定の変更・一般化時に混在入力の負対照を行う。実機Safari、連続開閉全域、実物の荷重・抜け止め、現地適合・史実寸法は未確認。既存Stage 3の一般判定は不変。
- 第3便の候補は引き続き構想段階。制作開始は未承認で、着手しない。
