# Stage 3-C 製品受入検証（2026-11-14）

元実装はHEAD `445f37182f07dae98441bc2a57f103e140c628a9`、tree `9005551d740e5fc70451e8986df5056480d80d06`。原ZIP/bundle/patch/台帳と既存worktreeのソースは維持し、既存の独立復元repositoryで追加候補を作る。yamanaka-historical-terrainは対象外。原証拠ZIPと実行ログは案件専用領域／正式CI artifactへ保存し、大容量CAD原本・原artifactを再コミットしない。

## 開始時の正式CI原証拠

別担当がrun [43591306326](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/43591306326)のartifact14112691722を取得した。47,891,651 bytes、SHA-256 `42d1692b8be91edd2b687c3150458bc3acae8ea19369d0c544dbbeb042400715`がGitHub digestと一致。38 entryと正常16 trace ZIPのCRCを検査。`git.txt`はmerge-ref `a79b7e86b1b378891d991a76a7e1977b869c070a`で、mainと提出HEADを親に持ち、treeが提出候補と一致する。

原Nodeログ487 PASS、CAD portable23部材・91角度・141閂位置・故障11件PASS。正常16条件はtraceの実engine、初期画面幅、motion、操作呼出し、拒否、resizeから照合した。故障34条件はresults行があるが個別PNG/traceは未収録（NOT_OBTAINED）。この旧CIは新しい履歴実装の証拠ではない。詳細は `evidence/stage3c/acceptance-20261114/initial-ci-independent.json`。

`gh run view --log`のCLI cache書込は権限拒否で停止した。権限変更や別経路での同cache取得は行わず、取得済みartifact内原ログを用いた。ローカルにFreeCAD/Blenderはないとの本人確認に基づき、レジストリ探索・ホストへのアプリ導入はしない。

## 今回の変更

- CAD履歴は文書transactionを所有するセッションledgerで管理。外部編集・不正target・native履歴名改変を拒否する。
- Web履歴は施錠・解錠・角度入力・アニメーションのUndo/Redoを提供する。保存／再読込と履歴の境界は[契約](history-contract.md)へ明記。
- before-code fixtureと同一反例を保持し、RED→GREENを再現できるスクリプトを追加。
- 既存Web2例外は基準／候補hashと許可patchを固定し、共有viewer自体のhashも照合。不正1byte変更を負対照で拒否する。最終挙動は3-B/3-A/2-D回帰で別検証。
- browser runnerはWindowsパス・案件専用依存を使用し、Chromium sandboxを有効にする。固定正常16条件を維持し、全故障のPNG/traceを保存。3-Bには鍵／履歴UIの不在、カメラ復帰、synthetic hidden停止、WebGL context lossを追加。
- Stage2D故障対照の保留レスポンスはfinallyで解放し、観測期限を設ける。通常のselectOption試験は維持する。故障注入経路と実ユーザー通常入力を区別する。
- CIはportable、Windows browser各stage、Debian trixie native再生成を分離。専用TMPDIR/TEMP、終了コード、原ログ、source/build hash、全artifact entryのhash台帳を保存する。

## 検査の区分

純粋Web履歴7件、CAD transaction double19件、CAD/Web状態domain64組一致、保存証拠のportable検査、実ブラウザ、実FreeCAD/Blender再生成は別判定。単純なエラーロールバックを履歴実装とは呼ばない。

別担当は独立のWeb反例5群（721frame gesture等）とCAD反例を実行した。native件数・姿勢が正しくても履歴名を改変する反例で誤受理を発見し、作者修正後に同じ反例を再注入してGREEN。実ソフトnative受入はこのdoubleの成功とは区別する。独立報告は `evidence/stage3c/acceptance-20261114/independent-*-history.json`。

最終CI native jobは保存ソースから新規生成し、全source hashと生成物hash、保存済み32,650pair測定との意味的比較、23部材のBRep対称差、STEP ID、TechDraw寸法3組、保存・別プロセス再読込、native履歴、blend/GLB各6姿勢を検査する。バイトhash差は記録し、形状・寸法一致と混同しない。生成物はartifactに収録する。

この文書は候補の検査方法と実施済み旧証拠照合を記録する。**最終HEAD・正式CI URL/digest・各受入結果・未解決指摘は、最終CI取得後のIssue #28／PR #29追記を正本とする。CI成功やマージ可を先取りしない。**

## 限界

材料強度・実物の荷重支持・史実機構・全連続経路はUNKNOWN/NOT_TESTEDを維持。静的91角度・141閂位置は連続安全保証ではない。FreeCADバッチでGUI moduleを初期化しても、手動GUI操作とは呼ばない。実機iPhone Safari・物理touchはNOT_TESTED。総合PARTIALと限定技術受入は分離し、Draft維持。マージ・公開・Issue closeを行わない。

## native CI初回の環境失敗と修正

run43599339799のnative job132460526735はCAD処理前のgit showがdubious ownershipでexit128。原job logを正規APIで取得して確認した。artifact14115497309は343 bytes、SHA-256 `14ece740287b69295b6e8b1c422d742f8797120d7bf1eef91c5e7689b28ff6ca`。空git.txtと台帳だけなので、native生成・再読込はこのrunではNOT_TESTEDである。失敗を残し、CIの既知checkoutパスだけをgit -c safe.directoryでコマンド単位に指定する。ホスト全体の設定・所有権・ACLは変更しない。修正後runは別に照合する。

## 実生成で発見したSTEPと検証器の不整合

run43599726462（候補e53d67d）のnativeはFCStd/STEP/blend/GLB再生成と32,650pairの意味的比較まで成功したが、STEP ID検査で停止した。旧Part.export出力は汎用PRODUCTと無名solidを持ち、23 PartIDを埋め込んでいない。裸形状の順番対応を受入根拠にしない。新buildはOCAF Import.export/Import.insertで23 PartIDとLabelを保持し、一意なLabel辞書とBRep対称差で検証する。CORE11＋履歴4のsource hashを明示し直すため、旧保存生成物は新ソース検査では意図的に不合格となる。正しい隔離再生成成果を取得後、必要な正式生成物だけ更新し、最終CIで再照合する。旧原本は445f3718と保全ZIPに残る。

別担当は旧Blender再読込検査へ、外接寸法を保つ頂点変形と面欠落を注入し誤受理を実証した（synthetic bpy adapterであり実Blender実行とは区別）。新検証器は全頂点の座標対応と向きを含む三角形集合を照合し、glTFの頂点分割・並び替えだけ許容する。同じ反例を拒否し、正当なfloat32丸めも23部材すべて受理することを独立確認。最終nativeでは実blend/GLBの各23部材×6姿勢へこの検証器を適用する。

## 名前付きSTEPの階層と微小な頂点丸め

run43600661295の名前付きSTEP rawには23 PartIDが入ったが、読込Shapeの件数検査で停止した。組立aggregateをleafと同じ集合へ数えた可能性を調べるため、次候補はassert前に全読込objectのinventoryを保存する。23個の単一solid leafのLabel集合を厳密照合し、それ以外のShapeは全23leafに一致するvalid23-solid aggregateだけ許可する。原因の仮説と、次CIの実測結果を区別する。

mesh検証器の独立反例では、同一境界点の5e-16m差がfloat32丸めで一つになる正常な転送をexact-tuple検査が拒否した。元fixtureを保持し、sourceを固定代表点への距離min(1e-9m, 比較許容値/1000)以内だけ同値化する。近傍の連鎖でclusterを無制限に広げない。出力に元unique数・同値化後数・最大距離と許容値を記録する。欠落・変形・逆向き・重複の三角形反例は引き続き拒否する。

2-Dの旧traceでは、最後のresearch viewerがstatus要素の存在だけでcloseされ依存配信が未完了の例があった。新runnerはstatus[data-loaded=true]とnetworkidleまで待ち、最後のJS/HTTPエラー検査を実ロード後に行う。元の正常行列と全assertは維持する。

## STEP集約検査のnative異常と参照datumの分類

run43601558970のinventoryでroot App::Partが23solidを持ち、そのほかに23個の正しいPartID leafを持つことを確認した。ただし新しいPart.makeCompound呼出しでSIGSEGVとなり、このrunのnative受入はFAIL。原artifactは119,841 bytes、SHA-256 `b47203aea85bef8ea2f65c6d852651ea3f5947eedd96a17aeb7febc4a6c86ea2`。直接原因の詳細はUNKNOWN。検査をskipせず、既存aggregateの23solidをleaf形状へ境界・体積・BRep対称差で唯一対応させ、全件消費する検査へ変更する。

原inventoryにはApp::Originの3軸/3平面も含まれ、solid0であっても正規の参照datumだった。App::Part→Origin→6Roleの正逆所有リンク、型、名称を確認して参照として分類する。任意の余剰faceや未知objectを除外するのではない。全objectを既知leaf・aggregate・所有Origin・6datumへ分類できなければ拒否する。次CIでこのAPI経路と実測を確認する。

## 確認済みnative成果の正式生成物への反映

run [43602228621](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/43602228621)、生成ソースHEAD `0d3f142c00cc98391d32cde8603223e78a3029f7`のnative jobは全8コマンド成功。原ZIP1,186,293 bytes、SHA-256 `fc7c57b8de2d14d3ee3c7b6bb7ab3189751db0ba49905b6fc0b7b498058bc562`、87entryのCRC/台帳と現行CADソース15件hashを照合した。別担当も同原票を読み、23CAD/STEP IDとBRep、31object分類、aggregate23solidの完全一対一（全対称差0）、TechDraw3寸法組、別プロセス状態/履歴再読込、75履歴状態の実BRep移動、32,650pair測定、blend/GLBの276 object-pose頂点・三角形を照合した。

独立剛体変換計算によるDoor/Boltの最大bounds誤差は2.27e-13mm。blend/GLB最大頂点誤差は2.366236835271437e-7m。実原票でsource weldの使用は0件であり、5e-16m反例は検証器の正当roundtrip互換性試験である。FreeCAD1.0.0+dfsg-8+deb13u3、Blender4.3.2、PySide5.15.16を原package記録から確認した。

30個のmanifest宣言ファイルのうちbyte差のあった20件だけ正式generatedへ反映した。runtime/cache/履歴試験出力はコピーしない。4主要binaryはすべて旧版とbyte差があるが、全23CAD BRepの意味的一致と新STEP IDを実ソフトで確認している。旧原本は445f3718、bundle、保全ZIPで保持する。この反映後はportable検査も再びPASSとなった。最終HEADの全CI原artifact照合は別に行い、完了判定はIssue/PR追記へ記録する。
