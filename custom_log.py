import inspect
import logging
from functools import wraps

# ファイル名
log_filename = "test.log"
# ファイル名
log_level = logging.INFO

def get_logger():
    """
    ログオブジェクト(logging.Logger)の取得関数

    Returns:
        logger (logging.Logger): logging.Loggerのインスタンス
    """

    # ログ出力フォーマット指定
    log_format = (
        "[%(asctime)s] %(levelname)s\t%(exc_filename)s"
        " - %(exc_funcName)s:%(exc_args)s:%(exc_lineno)s -> %(message)s"
    )

    # ログの設定
    logging.basicConfig(format=log_format, level=log_level, filename=log_filename)
    logger = logging.getLogger(__name__)
    logger.addFilter(CustomLogFilter())

    # コンソール出力設定
    console = logging.StreamHandler()
    console.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

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
            # 引数のログ出力内容(kwargsがある場合は両方出力)
            exc_args = (args, args + (kwargs,))[any(kwargs)]

            # loggerで使用するためにfuncに関する情報をdict化
            extra = {
                "exc_filename": inspect.getfile(func),
                "exc_funcName": func_name,
                "exc_lineno": inspect.currentframe().f_back.f_lineno,
                "exc_args": exc_args,
            }
            # 開始ログ
            logger.info(f"[START] {func_name}", extra=extra)

            try:
                # 関数の実行
                return func(*args, **kwargs)
            except Exception as err:
                # エラーハンドリング
                logging.exception(
                    f"[EXCEPTION] {func_name} {err}", exc_info=True, extra=extra
                )
            finally:
                # 関数終了時のエラー
                logging.info(f"[END] {func_name}", extra=extra)

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
        record.exc_filename = getattr(record, "exc_filename", record.filename)
        # 実行関数名
        record.exc_funcName = getattr(record, "exc_funcName", record.funcName)
        # 実行行
        record.exc_lineno = getattr(record, "exc_lineno", record.lineno)
        # 実行関数における引数（要考慮）
        record.exc_args = getattr(record, "exc_args", record.args)

        return True
