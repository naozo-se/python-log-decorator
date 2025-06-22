# from custom_log import log, get_logger # custom_log.py経由で実行するためコメントアウト

# ログオブジェクト取得
# logger = get_logger() # custom_log.py経由で実行するためコメントアウト
# 'logger' と 'log' は custom_log.py によって builtins に注入される想定


# 例外確認
def raise_error():
    # logger.info("About to raise an error") # 注入されたloggerを使える
    raise Exception("Error!!!!")


@log(logger)  # 関数に対してログデコレーターを指定 (loggerはbuiltinsから参照される)
def temp(data={}):
    logger.info(data) # loggerはbuiltinsから参照される


@log(logger)  # 関数に対してログデコレーターを指定 (loggerはbuiltinsから参照される)
def main():
    # ログを直接使用
    logger.info({"a": "c"}) # loggerはbuiltinsから参照される

    # 関数呼び出し
    temp({"a": "b"})

    # 例外確認関数を実行
    return raise_error()


if __name__ == "__main__":
    # このスクリプトを直接 python main.py で実行すると、
    # logger や log が未定義のため NameError が発生する。
    # python custom_log.py main.py のように実行する必要がある。
    logger.info("main.py started via custom_log.py") # 動作確認用に追加
    main()
    logger.info("main.py finished via custom_log.py") # 動作確認用に追加
