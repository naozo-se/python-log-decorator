# Python カスタムロギングユーティリティ

このプロジェクトは、Pythonアプリケーションに詳細なログ出力機能を追加するためのユーティリティです。
関数の実行（開始、終了、引数、例外）の自動ロギングや、任意の場所での手動ロギングをサポートし、マルチプロセス環境でも動作するように設計されています。

## 特徴

- **関数デコレーター**: `@log(logger)` デコレーターを使用して、関数の呼び出し情報を簡単にログ記録できます。
    - 関数の開始と終了
    - 関数へ渡された引数
    - 関数内で発生した例外とスタックトレース
- **直接ロギング**: 標準の `logging` モジュールと同様のインターフェース (`logger.info()`, `logger.debug()` など) で、任意の場所にログを出力できます。
- **マルチプロセス対応**: 複数のプロセスから同時にログを書き込んでも、各ログエントリにプロセスIDが付与され、識別可能です。
- **インポート不要な実行モード**: 対象のスクリプトを変更せずに、本ユーティリティ経由で実行することでログ機能を追加できます。
- **柔軟な設定**: ログファイル名やログレベルをカスタマイズ可能です。

## セットアップ

必要なライブラリはありませんが、テストを実行するには `pytest` が必要です。

```bash
pip install pytest
```

## 使用方法

本ユーティリティは、ライブラリとしてインポートして使用する方法と、CLIツールとして既存のスクリプトにログ機能を注入する方法の2通りで利用できます。

### 1. ライブラリとしての使用

お使いのPythonスクリプトに `custom_log` モジュールをインポートして使用します。

```python
# your_script.py
from custom_log import get_logger, log

# ロガーインスタンスを取得 (ログファイル名やログレベルは custom_log.py 内で設定可能)
# または get_logger の引数で指定 (例: get_logger(log_filename="my_app.log"))
logger = get_logger(log_filename="application.log") # custom_log.pyのget_loggerはlog_filename引数を持ちます

@log(logger)
def my_function(name, count=1):
    logger.info(f"Executing my_function with {name} and {count}")
    if count < 0:
        raise ValueError("Count cannot be negative")
    return f"Hello, {name}!" * count

if __name__ == "__main__":
    my_function("World", count=2)
    try:
        my_function("ErrorCase", count=-1)
    except ValueError as e:
        logger.error(f"Caught an expected error: {e}")
    logger.debug("Script finished.") # DEBUGレベルのログ
```

上記のように記述し、スクリプトを実行すると、`application.log`（または指定したファイル）にログが出力されます。

### 2. CLIツールとしての使用 (インポート不要)

既存のスクリプト (`your_script.py`) を変更せずにログ機能を追加したい場合に便利です。
`custom_log.py` を通して対象のスクリプトを実行します。

**対象スクリプトの例 (`your_script.py`):**
```python
# このスクリプトでは custom_log のインポートは不要です。
# `logger` と `log` は custom_log.py によって実行時に提供されます。

@log(logger) # logger は実行時に注入される
def greet(name):
    logger.info(f"Greeting {name}") # logger は実行時に注入される
    return f"Hello, {name}"

if __name__ == "__main__":
    greet("Alice")
    logger.debug("greet function was called.") # DEBUGレベル
```
**実行コマンド:**
```bash
python custom_log.py your_script.py [オプション]
```

**オプション:**
-   `your_script.py`: ログ機能を適用したい対象のPythonスクリプト。
-   `--log_file <filename>`: ログを出力するファイル名を指定します (デフォルト: `activity.log`)。
-   `--log_level <LEVEL>`: ログレベルを指定します (例: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`、デフォルト: `INFO`)。

**例:**
```bash
python custom_log.py your_script.py --log_file my_app_activity.log --log_level DEBUG
```
この方法で実行すると、`your_script.py` は `logger` と `log` をグローバルに利用できる状態で実行され、指定されたファイルにログが出力されます。`your_script.py` 内に `custom_log` のインポート文やロガー取得処理を記述する必要はありません。

## ログフォーマット

ログは以下の形式で出力されます（一部のフィールドはログの種類によって異なります）。

`[%(asctime)s] [%(process)d] %(levelname)s %(exc_filename)s - %(exc_funcName)s:%(exc_args)s:%(exc_lineno)s -> %(message)s`

-   `%(asctime)s`: ログが記録された日時 (例: `2023-10-27 12:34:56,789`)
-   `%(process)d`: ログを生成したプロセスのID (例: `12345`)
-   `%(levelname)s`: ログのレベル (例: `INFO`, `DEBUG`, `ERROR`)
-   `%(exc_filename)s`: ログが出力された元のファイル名 (例: `your_script.py`)
-   `%(exc_funcName)s`: ログが出力された関数名 (例: `my_function`)
-   `%(exc_args)s`: (デコレーター使用時) 関数に渡された引数 (例: `('World',), {'count': 2}`)
-   `%(exc_lineno)s`: ログが出力された行番号 (例: `42`)
-   `%(message)s`: ログメッセージ本体 (例: `[START] my_function`, `Executing my_function...`, `[END] my_function`)

## テストの実行

テストは `pytest` を使用して実行できます。

1.  `pytest` をインストールします:
    ```bash
    pip install pytest
    ```
2.  リポジトリのルートディレクトリで以下のコマンドを実行します:
    ```bash
    pytest
    ```

これにより、`test_custom_log.py` 内のテストケースが実行されます。
