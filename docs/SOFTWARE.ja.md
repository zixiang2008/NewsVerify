# NewsVerify ソフトウェア仕様書

**バージョン：** 0.7.1（Source） · **リリース日：** 2026-11-18  
**リポジトリ：** https://github.com/zixiang2008/NewsVerify  
**公開コンソール：** https://new.caishen.today（LAN：`http://192.168.8.253:8095`）

本文では、NewsVerify が存在する理由、参照した研究・評価資料、証拠から結論を導く論証方法、すべてのデータ源の根拠と組み合わせ方、そして直近のローカル実験結果を説明します。運用者、レビュアー、およびシステムを理解・保守する Agent 向けです。

---

## 1. なぜこのソフトウェアが必要か

ニュース、SNS、生成モデルは、個人が確認できるよりも速く「主張」を生み出します。スクリーンショット、転載、AI 要約は同じように確信的に見えても、証拠の裏付けは大きく異なります。手作業の事実確認は遅く、キーワード一致は信頼できず、商用の確認 API は不透明で自前の環境に置けません。

そこで NewsVerify は、**自己ホスト型で監査可能な主張検証ワークスペース**として設計されました。単一のモデル出力を信じるのではなく、次の順序で動作します。

1. 記事を独立に検証可能な原子的な主張へ分割する。
2. 各主張についてオープン Web の証拠を検索し、反証指向の問いも投げる。
3. 同じ通信社稿の転載をまとめ、「多くの媒体が言っている」を独立な複数情報源と誤認しない。
4. 6 つの固定ラベルから選択させ、必ず理由・反証・証拠のギャップを添える。
5. 公信力の高い 30 媒体で相互確認し、開ける出典リンクを保存する。
6. イベントを継続監視し、証拠フィンガープリントが実際に変わったときだけ通知する。

設計原則は、**証拠がなければ「証拠不足」と言う。「支持」をでっち上げない**。

---

## 2. 参照した研究資料と外部根拠

NewsVerify は、複数の公開研究・評価の伝統を工学的に統合したものです。ライセンス評価データベースの購入・再配布は行わず、公式スコアを捏造しません。

| 資料 | 貢献 | システムでの利用 |
| --- | --- | --- |
| FEVER 形式の主張検証 | 文書を原子主張へ分解し、支持／反証を別々に検索 | `app/verification/claims.py`、`evidence.py` |
| AVeriTeC（実世界主張検証） | 証拠優先、ギャップの明示、不確実性の保持 | 判定に `evidence_gaps`、`counter_argument`、6 ラベル |
| Google Fact Check Tools API | 専門機関の `textualRating` と審査日 | キー設定時に `search_google_factcheck()` で公式補助として先頭へ |
| Media Bias/Fact Check（MBFC） | 公開の「Factual Reporting」等級 | Top30 の `factual` フィールドの参考。有料 API は呼ばない |
| Reuters Institute『Digital News Report』 | 国別の報道trust調査 | 並び順の背景資料。記事単位の評価ではない |
| NewsGuard / Ad Fontes / AllSides | 信頼性・バイアス分類 | `not_connected` として記録し、未ライセンスならスコアを出さない |
| Pew Research / RSF | オーディエンス行動と報道の自由環境 | `context_only`。国の環境は真偽ではない |
| Veracity（arXiv:2506.15794）などのオープンシステム | 情報源の透明性：信頼性＋説明＋追跡可能 URL、独立性 | `independence_chain_id`、クリック可能な出典一覧、報道件数 |
| OpenAI 互換 LLM API | 検索証拠だけに基づく構造化推論 | 主／予備エンドポイントの自動切替、JSON 判定 |

6 つの評価体系メタデータは `app/ratings/systems.py` に集約し、ライセンス状態を明記しています。欠けている評価は欠けていると表示し、推測しません。

---

## 3. どんな論証方法で、どんな結論を出すか

### 3.1 6 段階パイプライン

| 段階 | 操作 | 成果物 |
| --- | --- | --- |
| ① 主張分解 | LLM が入力を設定上限内の原子主張へ分割 | `claims` |
| ② 証拠検索 | 主張ごとに原文クエリと反証クエリ | `sources` / `evidence` 候補 |
| ③ 独立性判定 | URL 重複除去＋本文フィンガープリントによる `independence_chain_id` | 独立証拠セット |
| ④ LLM 判定 | 証拠スニペットだけを構造化プロンプトへ | ラベル、確信度、理由、反証、ギャップ |
| ⑤ 媒体相互確認 | 幅広い検索結果をドメインで Top30 に照合し、重要媒体のみ `site:` 補足 | 30 件の点灯／灰色＋出典 |
| ⑥ 継続追跡 | 6h / 24h / 週で証拠と判定のフィンガープリントを比較 | 実質変化時のみ通知 |

#### 信頼情報源ホワイトリスト（v0.5.2 以降）

証拠プールは厳格なホワイトリスト（`app/verification/source_policy.py`）を使用し、次の 4 類のみを許可します。

| 区分 | 範囲 | 理由 |
| --- | --- | --- |
| Top30 公信力媒体 | Reuters、AP、AFP、BBC ほか 30 媒体と公式バリエントドメイン | 相互確認の基準 |
| 専門ファクトチェック機関 | Snopes、FactCheck.org、PolitiFact、Full Fact、AFP Fact Check、Lead Stories など | 公開主張の専門審査 |
| 世界的検索エンジン | Google、Bing、DuckDuckGo、Yahoo、Brave、Startpage | 追跡可能な検索入口のみ。編集証拠としては扱わない |
| 権威ある一次資料機関 | NASA、NOAA、WHO、UN、OECD、Science、PNAS など | 直接照合できる原資料 |

Baidu 百科/文庫、QQ、搜狐、虎嗅、Wikipedia などのアグリゲーター・百科事典・コンテンツファームは検索段階で拒否され、証拠プールにも画面の出典リンクにも入りません。ホワイトリストは `/api/source-policy` と画面の「信頼情報源ホワイトリスト」パネルで公開され、監査できます。

各段階は `jobs.result.progress` に書き込まれ、Web 画面でリアルタイムのタイムラインとして描画されます。

### 3.2 許可される結論

判定器は次のいずれか 1 つだけを選びます。

- `supported`：十分な支持証拠がある。
- `refuted`：十分な反証がある。
- `mixed`：支持と反証が併存する。
- `insufficient_evidence`：信頼できる証拠が見つからない（既定のフォールバック）。
- `outdated`：以前は真だったが現在は変化した。
- `not_checkable`：主観的・未来的など検証不能。

### 3.3 過剰断定を防ぐ規則

- 疑惑は事実ではなく、捜査は有罪ではない。
- 証拠がないことは「偽」の証明ではない。
- 取得失敗は fetch_failed と記録し、「証拠なし」に数えない。
- 開ける出典 URL のない判定は拒否するか `insufficient_evidence` に劣化させる。
- 同じ通信社稿の転載は 1 つの独立性チェーンとして扱う。
- 政治的・急変化な話題は時間境界と不確実性を保持する。
- 外部 URL はアクセス前に SSRF 検査を通す。

**最終的な結論の形**：主張ごとに制約付きラベル＋確信度＋理由＋反証＋証拠のギャップ＋引用 URL、イベントごとに要約＋30 媒体カバレッジ＋追跡状態。システムは「検索時点で証拠がどこまで支持したか」を報告し、永遠の真実を主張しません。

---

## 4. データ源の根拠・出所・組み合わせ方

### 4.1 入力チャネル

| チャネル | 入口 | 備考 |
| --- | --- | --- |
| Web コンソール | `POST /submit` / `POST /api/v1/check` | テキスト＋モード（full / top30 / method）＋追跡頻度 |
| Telegram Bot | `/check`、`/deep`、`/track`、`/status`、`/history` | aiogram ロングポーリング。トークン失效時は優雅に劣化 |
| Public API v1 | API Key ヘッダ | Agent・自動化向け |

### 4.2 検索と抽出

- `unified_search()` は設定により `ddgs`（旧名を保持）、Brave Search、SearXNG を選択。
- NAS 環境では `search_duckduckgo()` が `yahoo` バックエンドを優先し、失敗時のみ `duckduckgo` へ退避。ddgs が 7 バックエンドを総当たりする問題を避け、Top30 所要時間を約 146 秒→約 44 秒に短縮しました。
- キーがあれば Google Fact Check 結果を公式補助として先頭に置き、URL で重複除去します。
- `fetch_url()` は URL を検証し、プライベートネットワークをブロックし、コンテンツハッシュを計算します。
- `extract_text()` は trafilatura 系の抽出で本文を得て、判定へ渡すスニペットは長さを制限します。

### 4.3 情報源モデルと独立性

各証拠は `url`、`domain`、`content_hash`、`independence_chain_id`、`snippet_hash`、取得状態、任意の公開日時を保存します。独立性チェーン ID はドメイン＋本文先頭 80 文字の正規化文字列の SHA-256 接頭辞です。同一チェーンは折りたたまれ、通信社稿のカスケードが多くの独立証人と誤認されません。

### 4.4 Top30 媒体の根拠

`app/verification/top_media.py` は「事実精度＋編集の独立性」で 30 媒体を定義します。

1. 全球通信社・公共放送：Reuters、AP、AFP、BBC、NPR、PBS、DW、France 24、NHK World、ABC AU。
2. 国際・全国紙と経済媒体：NYT、Washington Post、Guardian、FT、WSJ、Economist、Time、Newsweek、CNN、Al Jazeera。
3. 専門ファクトチェック・学術・地域権威：Snopes、FactCheck.org、Politifact、Full Fact、The Conversation、Scientific American、Nature News、The Canadian Press、The Hindu、Sydney Morning Herald。

`check_top_media()` はまず少数の幅広い検索を行い、結果をドメインで一覧へ照合（`www.` や `bbc.co.uk` などの別名も処理）し、未命中の重要媒体にだけ `site:` を補足します。`hit_count > 0` なら緑に点灯し、そうでなければ灰色。各出典リンクも表示します。

### 4.5 組み合わせ順序

```
ユーザー入力
  -> Event + queued Job
  -> claims[]
  -> （原文検索＋反証検索）-> sources[] -> 独立性去重
  -> verdicts[]（6 ラベル制約付き LLM 出力）
  -> Top30 カバレッジ（ドメイン照合＋site: 補足）
  -> job.result { summary, progress, top_media, media_hits, total_reports }
  -> Telegram 通知＋Web 描画
  -> Subscription ポーリング -> フィンガープリント差分 -> Notification
```

LLM は OpenAI 互換クライアントで主／予備エンドポイント（`LLM_BASE_URL`、`LLM_BASE_URL_FALLBACK`）を呼びます。クライアント内部リトライは無効化し、`app/verification/llm.py` がエンドポイント切替と小さなサーキットブレーカーを担当します。

### 4.6 永続化

PostgreSQL テーブル：`events`、`claims`、`sources`、`evidence`、`verdicts`、`jobs`、`subscriptions`、`notifications`。子テーブルは `ON DELETE CASCADE`。ジョブ結果は JSON で保持し、パイプラインの進化に柔軟に対応しつつ中核の関係表は監査可能です。

---

## 5. 最終実験結果

以下は Synology N150-P NAS 上のローカル展開による結果であり、合成ベンチマークではありません。

| 検査項目 | 結果 |
| --- | --- |
| `/health` | HTTP 200 |
| フロントエンド JS 構文 | `node --check` 合格。v0.5.1 後は約 2.77 万文字 |
| `/api/top-media` | 30 媒体を返却（順位・事実等級・独立性・種別・URL） |
| 端到端の完全検証 | 検証サンプルは約 101 秒で `done` |
| 媒体相互確認 | 30 家中 10 家が点灯、20 件の開ける関連出典 |
| LAN と公開 | `http://192.168.8.253:8095` と `https://new.caishen.today` の両方が新ビルド |
| API 主予備切替 | 両エンドポイントとも HTTP 200。主を強制失敗させると予備へ切替成功 |
| 検索最適化 | yahoo 優先。Top30 がローカルで約 146 秒→約 44 秒 |
| 履歴整理 | バックアップ後に failed 15 件と孤立テスト 1 件を削除。残り 8 件はすべて成功 |
| 複数スタイル UI | 4 テーマを即時切替、選択はローカル保存、版本モーダルが履歴を表示 |

解釈：ローカル NAS では約 2 分で安定して監査可能な結果が得られます。最大のコストは媒体相互確認であり、そのため「幅広い検索によるドメイン照合を先に、定点 `site:` を後」にしています。個人・小チーム向けであり、法的・専門的な裁定権限を持つものではありません。

---

## 6. 使い方

### 6.1 Web コンソール

1. LAN または公開 URL を開き、PIN を入力。
2. 必要なら上部でスタイル（Aurora / Paper / Slate / Terminal）を選択。
3. テキストまたはリンクを貼り、モードと追跡頻度を選んで送信。
4. タスクは履歴の先頭に即時表示され、実行中は詳細ダイアログが 3 秒ごとに更新。
5. タスクをクリックすると判定・証拠・進捗タイムライン・30 媒体カバレッジを表示。
6. 「📡 追跡状態」で全更新を、「⚙️ 設定」で頻度・次回時刻・一時停止を変更。
7. 下部のシステムパネルで CPU・メモリ・ディスク・外部 API の状態を確認。

### 6.2 Telegram

`/help`、`/check <文本>`、`/deep <文本>`、`/track <イベントID> [6h|24h|week]`、`/untrack`、`/status`、`/history`、`/privacy`。

### 6.3 Public API v1

```bash
curl -H "X-API-Key: $API_KEY" https://new.caishen.today/api/v1/version
curl -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"text":"...","mode":"full","freq":"none"}' \
  https://new.caishen.today/api/v1/check
```

---

## 7. バージョンとリリース手順

バージョン番号と更新履歴を書く唯一の場所は `app/version.py` です。Web バッジ、ログイン画面、`/api/version`、`/api/v1/status`、`pyproject.toml`、`compose.yaml`、README、CHANGELOG はそこから派生または整合しています。

リリースごとに：

1. `app/version.py` の `VERSION`、`RELEASE_DATE`、`CODENAME`、`RELEASES` を更新。
2. `pyproject.toml`、`compose.yaml`、`CHANGELOG.md` を同期。
3. 英語・中国語・日本語のREADMEとソフトウェア文書を更新。
4. `./scripts/sync_github.sh` を実行し、機微情報を除いたソースを push。
5. NAS へ展開し、`/health`、`/api/version`、画面の版本バッジを検証。

---

## 7.5 v0.6.0 の新機能

- **テーマと音楽**：9 つの切り替えテーマ（Aurora/Paper/Slate/Terminal/Ocean/Forest/Sunset/Violet/Mono）をローカル保存。Web Audio 生成アンビエント音（雨/波/森/夜）は再生・停止・切替・音量調整が可能で、外部音源ファイルは不要です。
- **情報源の可読化と可視化**：Top30 パネルに常時スクロールバー。各証拠タイトルの右に媒体名・世界公信力ランク・事実評価・報道日を括弧で表示。
- **準拠した情報収集**（`app/ingest/open_web.py`）：公開 RSS / Google News RSS で候補を拡大し、robots.txt を尊重、ホスト別レート制限と有限リトライを実施。ログイン/ペイウォール/キャプチャの回避は行わず、全候補は信頼情報源ホワイトリストを通過してから証拠プールへ。
- **複数 IM 接入**（`app/integrations/`）：NoneBot/OneBot、Kirara AI などの成熟フレームワークの「アダプター＋設定駆動＋統合入口」方式を参考に、Telegram/Discord/Slack/飛書/釘釘/WeCom/公式アカウント/QQ(OneBot)/LINE/Matrix/汎用 Webhook のアダプターを提供。統合入口は `POST /api/v1/im/{key}/webhook`。
- **管理コンソール** `/admin`（PIN `1314`）：マスク済み API 設定、チャネル状態の閲覧とテスト返信。`.env` 変更後はコンテナ再起動が必要です。
- **理論ページ** `/theory`：方法論、信頼度バンド体系の由来、SVG 図解、出典一覧、学術・グローバル評価を公開。

## 7.6 v0.6.1 の新機能：アンビエント音源ライブラリ

- **20 種類の生成サウンドスケープ**（従来 4 曲）：ホワイトノイズ、シンギングボウル、禅庭、野鳥、细雨、雷雨、渓流、風鈴、虫の声、焚き火、寺の鐘、月光、竹林、雪落など。各曲は `noise` / `pad` / `chirp` / `strike` のレイヤーを Web Audio でリアルタイム合成するため、外部音声ファイルもネットワーク要件もありません。
- **操作**：音をクリックすると即再生、同じ音をもう一度クリックすると停止、別の音をクリックすると切替。一覧はスクロール可能で 20 種類すべてにアクセスでき、パネル下部に再生/停止ボタンも残しています。
- **自動フェードアウト**：5 秒操作がないとパネルがフェードアウトし、× ボタンから手動で閉じることもできます。クリック・マウス移動・ドラッグ・スクロールでタイマーが再開します。フェードアウトしても再生は続きます。
- **音量**：スライダーは `oninput` を使用し、ドラッグ中にリアルタイムで反映され、パーセンテージも表示します。曲と音量は `localStorage`（`nv_music_track`、`nv_music_vol`）に保存されます。
- **検証**：リリース前にレンダリング後スクリプト構文チェック（`ast` + `node --check`）と操作シミュレーションテスト（再生/停止/切替/音量）を実行します。

## 7.7 v0.7.0 の新機能：対話型 IM 接続ウィザード

- **設計参考**：AstrBot / NoneBot / Koishi などの成熟したマルチプラットフォーム框架的「アダプター＋設定駆動＋WebUI ウィザード」方式を参考にしつつ、**ランタイム自体は導入しません**（NAS の依存肥大化とアーキテクチャ書き換えを避ける）。既存の `app/integrations/` の上に対話型設定体験を追加しただけです。
- **ウィザード** `/admin/im`：11 の主要プラットフォーム（Telegram / Discord / Slack / 飛書 / 釘釘 / WeCom / 公式アカウント / QQ・OneBot / LINE / Matrix / 汎用 Webhook）をカード表示。4 ステップ：① 公式認証情報の取得案内（公式管理画面への直リンク付き）→ ② 動的フォーム入力 → ③ QR スキャン / 受信 URL コピー → ④ 実メッセージテスト。
- **コード不要・再起動不要**：認証情報は `im_channel_configs`（`app/integrations/channel_store.py`）に保存し、保存時に `ChannelRegistry.set_db_credentials()` でホットロード。表示時はマスキング（`1234••••mnop`）し、マスク値が実際の秘密を上書きすることはありません。旧 `NV_IM_*` 環境変数は互換フォールバックとして残しています。
- **QR 連携**：Telegram は `segno` で `t.me/<bot>?start` の SVG QR を生成し、スキャン後に `/start` を送ると統一 webhook が `bound_chat_id` を記録、ウィザードが `/bind-status` をポーリングして完了を表示します。飛書/釘釘/WeCom/LINE/QQ OneBot は各公式スキャン手順が異なるため、公式案内と受信 URL のワンクリックコピーを提供します。
- **実テスト**：`app/integrations/__init__.py` が各プラットフォーム公式形式のメッセージ（飛書 `msg_type:text`＋タイムスタンプ署名、釘釘 `msgtype:text`＋HMAC-SHA256 署名、WeCom、Discord `content`、Slack `text`、LINE `messages`、Matrix `m.text`、Telegram Bot API）を構築し、結果とエラーを状態パネルへ書き戻します。
- **検証**：15 項目の接続ロジックテスト（ガイド完全性、マスキング/マージ、各プラットフォーム形式と署名、未設定時の安全失敗、QR 生成）と、レンダリング後 JS の `node --check` を実施。

## 7.8 v0.7.1 の新機能：理論ページの引用体系と出典検証

- **内容**：`app/web/theory.py` を理論解説ページへ全面拡張。八章構成（なぜ枠組みが必要か、ニュース真偽判断の理論全景、理論と実装の対応、方法論、信頼度バンドの由来、体系図、学術評価、出典注釈）。
- **理論全景**：ニュースの真偽を判断する研究を四層に整理——哲学層（対応説/整合説/検証主義の真理論）、認知層（情報源信頼性、確認バイアス）、手法層（FEVER / AVeriTeC / Veracity / trafilatura）、機関層（MBFC / Ad Fontes / NewsGuard / AllSides / ロイター研究所）。
- **対応表**：各理論がシステムのどこに使われ、どう組み合わさるかを「哲学→出力形態、認知→バイアス対策、手法→再現可能な工程、機関→情報源序列」の鎖として明示。
- **出典注釈**：本文の `[1]`–`[17]` 番号引用が末尾へジャンプ。各項目に原文URL（arXiv / ACL Anthology / DOI / 公式ページ、複数ある場合はすべて）、初版発表機関、年、理論的根拠とシステム用途を記載。異なる原文URLは計 27 件。
- **出典検証**：旧ページの誤引用を修正——FEVER は arXiv:1803.05355（NAACL 2018）、AVeriTeC は arXiv:2305.13117（NeurIPS 2023）、trafilatura は ACL 2021.acl-demo.15。Hovland & Weiss 1951（DOI 10.1086/266350、イェール大）、Nickerson 1998（DOI 10.1037/1089-2680.2.2.175、タフツ大）、スタンフォード哲学百科 "Truth" 項目などの基礎資料を追加。
- **検証**：`py_compile` 成功、本文引用番号と注釈番号が完全一致（1–17）、HTML タグ閉合チェックすべて通過、誤った arXiv 番号の残存なし。

---

## 8. 限界

- 評価は参考であり、媒体順は諮問的なものです。
- 検索エンジンのレート制限により、新しすぎる・未インデックスの話題はカバーしきれない場合があります。
- LLM 判定は確率的であり、証拠とギャップと併読する必要があります。
- PIN は個人用コンソールの保護です。複数人へ公開するなら HTTPS・ユーザー別認証・レート制限を追加してください。
- 結果はある時点のスナップショットです。継続追跡は事実が変わることへの備えです。
