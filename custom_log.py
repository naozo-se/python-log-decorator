import inspect
import logging
import os  # osモジュールをインポート
from functools import wraps

# ファイル名
# log_filename = "test.log" # グローバル変数から削除
# ファイル名
log_level = logging.INFO

def get_logger(log_filename="test.log"):  # log_filenameを引数に追加
    """
    ログオブジェクト(logging.Logger)の取得関数

    Args:
        log_filename (str): ログファイル名 (デフォルト: "test.log")

    Returns:
        logger (logging.Logger): logging.Loggerのインスタンス
    """

    # ログ出力フォーマット指定 (プロセスIDを追加、タブをスペースに置換)
    log_format = (
        "[%(asctime)s] [%(process)d] %(levelname)s %(exc_filename)s"  # \t を削除しスペースに
        " - %(exc_funcName)s:%(exc_args)s:%(exc_lineno)s -> %(message)s"
    )

    # ロガーの取得 (ルートロガーではなく、このモジュール専用のロガー)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level) # ロガー自体のレベル設定が重要
    logger.addFilter(CustomLogFilter())

    # 既存のハンドラをクリア (テストなどで複数回呼ばれる場合のため)
    if logger.hasHandlers():
        logger.handlers.clear()

    # ファイルハンドラの設定
    fh = logging.FileHandler(log_filename, mode='a') # mode='a'で追記
    fh.setLevel(log_level)
    fh.setFormatter(logging.Formatter(log_format))
    logger.addHandler(fh)

    # コンソールハンドラの設定
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(log_format))
    logger.addHandler(ch)

    logger.propagate = False # ルートロガーへの伝播を防ぐ (二重出力防止)

    # ログオブジェクトを返す
    return logger


def log(logger):
    """
    各関数に対して、デコレーター(@log(logger))でloggerを引数にとるためのラッパー関数

    Args:
        logger (logging.Logger) 
        ※各プログラムの開始時にtget_loggerで取得したオブジェクトを引数で指定する

    Returns:
        _decoratorの返り値
    """

    def _decorator(func):
        """
        デコレーターを使用する関数を引数とする

        Args:
            func (function)

        Returns:
            wrapperの返り値
        """

        # funcのメタデータを引き継ぐ
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            実行処理

            Args
            -------
            *args, **kwargs: funcの引数

            Returns
            -------
            func(*args, **kwargs)
                func実行時の返り値
            """

            # 関数名
            func_name = func.__name__
            # 引数のログ出力内容を整形
            arg_parts = []
            if args:
                arg_parts.append(str(args))
            if kwargs:
                arg_parts.append(str(kwargs))
            exc_args = ", ".join(arg_parts) if arg_parts else ""

            # loggerで使用するためにfuncに関する情報をdict化
            module_file = inspect.getmodule(func).__file__
            extra = {
                "exc_filename": os.path.basename(module_file) if module_file else "UnknownFile",
                "exc_funcName": func_name,
                "exc_lineno": func.__code__.co_firstlineno,
                "exc_args": exc_args,
            }
            # 開始ログ
            logger.info(f"[START] {func_name}", extra=extra)

            try:
                # 関数の実行
                return func(*args, **kwargs)
            except Exception as err:
                # エラーハンドリング
                logger.error(  # logging.exception を logger.error に変更
                    f"[EXCEPTION] {func_name} {err}", exc_info=True, extra=extra
                )
            finally:
                # 関数終了時のログ
                logger.info(f"[END] {func_name}", extra=extra) # logging.info を logger.info に変更

        return wrapper

    return _decorator


class CustomLogFilter(logging.Filter):
    """
    loggerの定義フィルタークラス
    """

    def filter(self, record):
        """
        呼び出し元のファイル名、関数名、行番号、引数を表示するためのフィルタ関数

        Returns:
            True: 無条件でフィルタを使用
        """

        # 実行ファイル名
        record.exc_filename = getattr(record, "exc_filename", "")
        # 実行関数名
        record.exc_funcName = getattr(record, "exc_funcName", "")
        # 実行行
        record.exc_lineno = getattr(record, "exc_lineno", 0)
        # 実行関数における引数
        record.exc_args = getattr(record, "exc_args", "")

        return True


if __name__ == "__main__":
    import argparse
    import sys
    import os # os をインポート
    import runpy # runpy をインポート
    import builtins # builtins をインポート

    parser = argparse.ArgumentParser(description="Python script execution with custom logging.")
    parser.add_argument("target_script", help="Path to the Python script to execute.")
    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    parser.add_argument(
        "--log_file", default="activity.log", help="Path to the log file."
    )
    # --log_lines はAST変換を伴うため、このステップでは一旦コメントアウト
    # parser.add_argument(
    #     "--log_lines",
    #     nargs="*",
    #     type=int,
    #     help="Specific lines to add logging statements (e.g., 10 25).",
    # )

    args = parser.parse_args()

    # グローバル変数 custom_log.log_level をコマンドライン引数で上書き
    # このモジュール内のグローバル変数 log_level を設定する
    # global log_level # globalキーワードはトップレベルスコープでは不要（削除）
    log_level = getattr(logging, args.log_level.upper())

    # get_logger を呼び出してロガーインスタンスを取得
    # この時、上で書き換えられたグローバルな log_level と、コマンドライン引数の log_file が使用される
    logger_instance = get_logger(log_filename=args.log_file)

    # builtins に logger と log (デコレーターラッパー自体) を登録
    # これにより、対象スクリプトは import 文なしにこれらの名前を参照できる
    builtins.logger = logger_instance
    builtins.log = log  # log 関数 (デコレーターを返す関数) を登録

    # 実行前のログ
    logger_instance.info(f"Attempting to run {args.target_script} with injected logger and log decorator", extra={
        "exc_filename": os.path.basename(args.target_script),
        "exc_funcName": "__main__",
        "exc_lineno": 0,
        "exc_args": "",
    })

    try:
        # runpy を使ってターゲットスクリプトを実行
        sys.path.insert(0, os.path.dirname(os.path.abspath(args.target_script)))
        runpy.run_path(args.target_script, run_name="__main__")

        logger_instance.info(f"Finished execution of {args.target_script}", extra={
            "exc_filename": os.path.basename(args.target_script),
            "exc_funcName": "__main__",
            "exc_lineno": 0,
            "exc_args": "",
        })

    except Exception as e:
        logger_instance.error(f"Exception during execution of {args.target_script}: {e}", exc_info=True, extra={
            "exc_filename": os.path.basename(args.target_script),
            "exc_funcName": "__main__",
            "exc_lineno": 0,
            "exc_args": "",
        })
