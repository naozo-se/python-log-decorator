from custom_log import log, get_logger

# ログオブジェクト取得
logger = get_logger()


# 例外確認
def raise_error():
    raise Exception("Error!!!!")


@log(logger)  # 関数に対してログデコレーターを指定
def temp(data={}):
    logger.info(data)


@log(logger)  # 関数に対してログデコレーターを指定
def main():
    # ログを直接使用
    logger.info({"a": "c"})

    # 関数呼び出し
    temp({"a": "b"})

    # 例外確認関数を実行
    return raise_error()


if __name__ == "__main__":
    main()
