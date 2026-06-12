# Student Education System - AI適応型学習プラットフォーム

大学のプログラミング教育向けに開発されたAI学習支援システムです。
AWS Bedrock (Claude 3 Haiku) を活用し、学生ごとの理解度に応じた課題出題・自動採点・TAチャットボットを提供します。

## システム構成

```
student/
├── api/            # FastAPI バックエンド (REST API)
│   ├── main.py
│   ├── routers/    # auth, assignments, dashboard, chat, admin
│   └── schemas/    # リクエスト/レスポンス定義 (Pydantic)
├── db/             # データベース層 (SQLite + SQLAlchemy)
│   ├── models.py   # ORMモデル (Student, Lecture, Assignment 等)
│   ├── database.py # エンジン・セッション管理
│   └── seed.py     # サンプルデータ投入
├── llm/            # LLM統合 (AWS Bedrock)
│   ├── bedrock_client.py  # Claude 3 Haiku 呼び出し
│   ├── prompts.py         # 採点・出題・TAボット用プロンプト
│   └── memory.py          # 学生プロファイル(弱点・得意分野)構築
├── vectorstore/    # RAG (検索拡張生成)
│   ├── build_index.py     # FAISSインデックス構築
│   ├── retriever.py       # ベクトル検索
│   └── documents/         # 教材 (Markdown)
├── ui/             # Streamlit フロントエンド
│   ├── app.py
│   ├── i18n.py            # 日本語/英語 対応
│   ├── views/             # login, assignment, ta_chat, dashboard
│   └── components/        # sidebar, charts (Plotly)
├── data/           # 実行時データ (gitignore対象)
│   ├── student.db         # SQLiteデータベース
│   └── faiss_index/       # ベクトルインデックス
├── config.py       # 設定ファイル
├── requirements.txt
└── run.sh          # 起動スクリプト
```

## 主な機能

| 機能 | 説明 |
|------|------|
| 課題出題・自動採点 | LLMが学生の弱点に応じた課題を生成し、回答をスコア付きで自動採点 |
| TAチャットボット | RAGで教材を検索し、文脈に基づいた回答を提供 |
| ダッシュボード | 日次推移・トピック別成績をグラフで可視化 |
| 適応学習 | 学生のスコアに応じて難易度・出題トピックを自動調整 |

## 技術スタック

- **バックエンド:** FastAPI / SQLAlchemy / SQLite
- **フロントエンド:** Streamlit / Plotly
- **LLM:** AWS Bedrock (Claude 3 Haiku + Amazon Titan Embed Text v2)
- **ベクトル検索:** FAISS
- **認証:** bcrypt + Bearerトークン

## 前提条件

- Python 3.10 以上
- AWSアカウント (Bedrock の利用権限が必要)
- pip または pip3

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd PBL_2026
```

### 2. Python仮想環境の作成・有効化

```bash
python -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows
```

### 3. 依存パッケージのインストール

```bash
pip install -r student/requirements.txt
```

### 4. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の変数を設定してください。

```dotenv
AWS_ACCESS_KEY_ID=<あなたのAWSアクセスキー>
AWS_SECRET_ACCESS_KEY=<あなたのAWSシークレットキー>
AWS_SESSION_TOKEN=<セッショントークン (一時認証情報の場合)>
AWS_DEFAULT_REGION=us-east-1
AWS_BEARER_TOKEN_BEDROCK=<Bedrock用ベアラートークン>
```

> `.env` は `.gitignore` に含まれているため、リポジトリにはコミットされません。

### 5. FAISSインデックスの構築

TAチャットボットのRAG検索に必要なベクトルインデックスを構築します。

```bash
cd student
python -m vectorstore.build_index
```

`data/faiss_index/` 配下に `index.faiss` と `chunks.json` が生成されます。

### 6. サンプルデータの投入 (任意)

デモ用の学生・講義・課題データを投入できます。

```bash
cd student
python -m db.seed
```

投入されるサンプルアカウント:

| 学生コード | 名前 | パスワード |
|-----------|------|-----------|
| s2024001 | 田中太郎 | demo123 |
| s2024002 | 鈴木花子 | demo123 |
| s2024003 | 佐藤健二 | demo123 |

## 起動方法

### 一括起動 (推奨)

```bash
cd student
bash run.sh
```

FastAPI (ポート 8000) と Streamlit (ポート 8501) が同時に起動します。
`Ctrl+C` で両方のサーバーを停止できます。

### 個別起動

ターミナルを2つ開いて、それぞれ以下を実行します。

**ターミナル1 - APIサーバー:**

```bash
cd student
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**ターミナル2 - フロントエンド:**

```bash
cd student
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

## アクセスURL

| サービス | URL |
|---------|-----|
| Streamlit (学生向けUI) | http://localhost:8501 |
| FastAPI (APIサーバー) | http://localhost:8000 |
| Swagger UI (APIドキュメント) | http://localhost:8000/docs |
| ヘルスチェック | http://localhost:8000/health |

## 設定のカスタマイズ

主な設定は `student/config.py` で管理されています。環境変数での上書きも可能です。

| 設定項目 | デフォルト値 | 環境変数 |
|---------|------------|---------|
| LLMモデル | `anthropic.claude-3-haiku-20240307-v1:0` | `BEDROCK_MODEL_ID` |
| 埋め込みモデル | `amazon.titan-embed-text-v2:0` | `EMBEDDING_MODEL_ID` |
| AWSリージョン | `us-east-1` | `AWS_REGION` |
| APIベースURL | `http://localhost:8000` | `API_BASE_URL` |
