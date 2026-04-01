# readme-translation

DeepL API を使って `README.md` を英語（またはDeepLが対応する任意の言語）に自動翻訳するためのワークフローです。

## 特徴

- [DeepL API](https://www.deepl.com/pro-api) を用いた翻訳
- 見出し・リスト・コードブロック・画像・バッジなどのMarkdown書式を保持
- 翻訳元・翻訳先の言語を自由に設定可能
- 翻訳済みファイルをリポジトリへ自動プッシュ

## 使い方

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}

- uses: k42um/readme-translation@v1
  with:
    deepl_api_key: ${{ secrets.DEEPL_API_KEY }}
```

### ワークフローの全体例

```yaml
name: Translate README

on:
  push:
    branches:
      - main
    paths:
      - README.md
  workflow_dispatch:

jobs:
  translate:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: kazuma/readme-translation@v1
        with:
          deepl_api_key: ${{ secrets.DEEPL_API_KEY }}
          input_file: README.md
          output_file: README.en.md
          source_lang: JA
          target_lang: EN-US
```

## 入力パラメータ

| 入力 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `deepl_api_key` | **はい** | — | DeepL API キー。リポジトリのシークレットに保存してください。 |
| `input_file` | いいえ | `README.md` | 翻訳元ファイルのパス。 |
| `output_file` | いいえ | `README.en.md` | 翻訳結果の出力ファイルパス。 |
| `source_lang` | いいえ | `JA` | 翻訳元の言語コード（`JA`、`ZH`、`DE` など）。空文字列を指定すると DeepL が自動検出します。 |
| `target_lang` | いいえ | `EN-US` | 翻訳先の言語コード（`EN-US`、`EN-GB`、`FR` など）。 |
| `commit_changes` | いいえ | `true` | 翻訳ファイルを自動コミット・プッシュするかどうか。 |
| `commit_message` | いいえ | `docs: update translated README (auto-translated)` | 自動コミット時のメッセージ。 |
| `commit_user_name` | いいえ | `github-actions[bot]` | 自動コミットに使用する Git の `user.name`。 |
| `commit_user_email` | いいえ | `github-actions[bot]@users.noreply.github.com` | 自動コミットに使用する Git の `user.email`。 |

## セットアップ

1. [DeepL API](https://www.deepl.com/pro-api)のアカウントを作成してください。（基本無料）
2. ログイン後、**アカウント → APIキーと制限 → キーを作成**からAPIキーを取得し、コピーしてください。
3. 使用したいリポジトリにて **Settings → Secrets and variables → Actions → New repository secret** より `DEEPL_API_KEY` という名前でシークレットを追加します。
4. リポジトリの`.github/workflows/translate-readme.yml`を作成し、以下のコードをコピーすると、READMEが自動で英訳されるようになります！

```yaml
name: Translate README
on:
  push:
    branches: main
    paths: README.md
  workflow_dispatch:

jobs:
  translate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: k42um/readme-translation@v1
        with:
          deepl_api_key: ${{ secrets.DEEPL_API_KEY }}
```