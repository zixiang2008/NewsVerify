# NewsVerify

**自己ホスト型・監査可能なニュース事実確認ワークスペース。** バージョン **0.5.0（Atlas）** · 2026-11-17。

NewsVerify はニュースを検証可能な主張へ分割し、オープン Web の証拠を検索し、情報源の独立性を判定し、6 種類に制約された判定を出力し、公信力の高い 30 媒体と相互確認し、イベントの実質的な変化を継続追跡します。

- 公開コンソール：https://new.caishen.today
- LAN コンソール：`http://192.168.8.253:8095`
- ソース：https://github.com/zixiang2008/NewsVerify

## まず読む文書

| 文書 | 言語 | 目的 |
| --- | --- | --- |
| [README.md](README.md) | English（既定） | クイックスタートと文書案内 |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 | 快速开始与文档导航 |
| [README.ja.md](README.ja.md) | 日本語 | クイックスタートと文書案内 |
| [docs/SOFTWARE.en.md](docs/SOFTWARE.en.md) | English | 完全なソフトウェア仕様 |
| [docs/SOFTWARE.zh-CN.md](docs/SOFTWARE.zh-CN.md) | 中文 | 完整软件说明书 |
| [docs/SOFTWARE.ja.md](docs/SOFTWARE.ja.md) | 日本語 | ソフトウェア仕様書 |
| [docs/PROJECT.md](docs/PROJECT.md) | 中文 | アーキテクチャ・データモデル・展開詳細 |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | English | 6 体系と判定規則 |
| [docs/API.md](docs/API.md) | English | Public API v1 リファレンス |
| [CHANGELOG.md](CHANGELOG.md) | English | バージョン履歴 |

詳細は [ソフトウェア仕様書](docs/SOFTWARE.ja.md) を先に読み、必要に応じて `PROJECT.md` で構成と展開を確認してください。

## 0.5.0 の主な変更

- 切り替え可能な 4 つの UI テーマ：Aurora / Paper / Slate / Terminal。
- 上部ナビゲーション、バージョンバッジ、「バージョンと更新」ダイアログ。
- バージョン番号を `app/version.py` に統一。
- 英・中・日の完全文書と、ワンコマンドの GitHub 同期スクリプト。
- NAS の実行環境を最新ソースで再ビルドし検証済み。

全履歴は [CHANGELOG.md](CHANGELOG.md) を参照してください。

## Synology NAS クイックスタート

```bash
cd /volume2/docker/newsverify
cp .env.example .env && chmod 600 .env
DOCKER=/volume2/@appstore/ContainerManager/usr/bin/docker
$DOCKER compose up -d --build
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8095/api/version
```

Docker 内から NAS 上の LLM サービスへアクセスする場合は、例：`http://172.17.0.1:3065/v1` のような Docker ゲートウェイを使ってください。設定例は `.env.example`。`.env` は絶対にコミットしないでください。

## 3 つの入口

- **Web：** PIN を入力し、テキスト／URL を貼り、モードと追跡頻度を選択して、リアルタイムのノードタイムラインと 30 媒体カバレッジを確認。
- **Telegram：** `/check`、`/deep`、`/track`、`/untrack`、`/status`、`/history`、`/privacy`。
- **API v1：** `/api/v1/` 配下の `X-API-Key` 認証エンドポイント。

## 技術スタック

Python 3.12 · FastAPI · aiogram · SQLAlchemy asyncpg · PostgreSQL 16 · OpenAI 互換 LLM（主／予備切替）· ddgs/Brave/SearXNG 検索 · trafilatura 抽出 · Docker Compose。

## 安全性と範囲

PIN、任意の API Key、外部 URL の SSRF 検査、独立性による重複排除、制約付き判定ラベルにより過信を抑えます。NewsVerify は意思決定支援ツールであり、法的・専門的な裁定機関ではありません。結果はある時点のスナップショットです。

## リリース手順

1. `app/version.py`、`pyproject.toml`、`compose.yaml`、`CHANGELOG.md` を更新。
2. 英・中・日の文書を更新。
3. `./scripts/sync_github.sh` を実行し、機微情報を除いたソースを push。
4. NAS に展開し、`/health`、`/api/version`、画面のバージョンバッジを検証。
