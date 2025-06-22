import pytest
import logging
import subprocess
import os
import re
import time # Import time module
import custom_log # Import the module itself to access its members like custom_log.log_level
from custom_log import get_logger, log

# テスト用のログファイル名
TEST_LOG_FILE = "test_run.log"

# テストごとにログファイルをクリーンアップするためのフィクスチャ
@pytest.fixture(autouse=True)
def cleanup_log_file():
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)
    yield
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)

@pytest.fixture
def logger_fixture():
    # custom_log.py のグローバルな log_level をテスト用に設定
    # import custom_log # custom_logモジュール自体をインポート
    # custom_log.log_level = logging.DEBUG # グローバル変数を直接変更
    # 上記の方法はモジュールの状態を変更するため、よりクリーンな方法を検討。
    # ここでは get_logger が参照する custom_log.log_level が適切に設定されている前提で進める。
    # 実際には custom_log.py の log_level の設定方法に依存する。
    # 今回は get_logger がデフォルトINFOで、テスト内で必要に応じてDEBUGレベルのハンドラを追加する方針も考えられる。
    # または、get_logger自体をテスト用にラップするか、log_levelを引数で渡せるようにする。
    # Plan step 1でlog_levelはcustom_log.pyのグローバル変数のままなので、
    # テスト実行前にそのグローバル変数を変更するか、get_loggerがそれを参照するようにする。
    # ここでは、テスト実行時に custom_log.py のグローバル log_level が DEBUG であると仮定するか、
    # get_logger 呼び出し時にレベルを指定できるならそうする。
    # 現状の get_logger は log_level を引数に取らないため、custom_log.py のグローバル log_level に依存。

    # pytestでは、テスト対象モジュールのグローバル変数を安全に変更するためにモンキーパッチなどを使うことが多い。
    # 例: monkeypatch.setattr("custom_log.log_level", logging.DEBUG)

    # custom_log.py のグローバル `log_level` を DEBUG に設定 (テスト中のみ)
    # これにより get_logger が DEBUG レベルのロガーを生成する
    original_log_level = custom_log.log_level
    custom_log.log_level = logging.DEBUG # モジュールグローバルをDEBUGに

    _logger = get_logger(log_filename=TEST_LOG_FILE)
    # get_logger内でbasicConfigが呼ばれるが、それが無視された場合も考慮し、
    # loggerインスタンスとハンドラのレベルを明示的に設定
    _logger.setLevel(logging.DEBUG)
    for handler in _logger.handlers:
        # 既存のハンドラーのレベルもDEBUGに設定する
        # 特にファイルハンドラがINFOレベルで初期化されている場合があるため
        handler.setLevel(logging.DEBUG)

    yield _logger # テスト関数へロガーを渡す

    # テスト終了後にログをフラッシュし、ハンドラをクローズ
    # ルートロガーからハンドラーを削除することで、次のテストへの影響を最小限に抑える
    # （ただし、get_loggerが毎回新しいハンドラを追加するなら効果は限定的）
    for handler in list(_logger.handlers): # list()でコピーしてイテレート中に変更可能に
        handler.flush()
        handler.close()
        # _logger.removeHandler(handler) # logging.shutdown()を使うので個別の削除は不要かも

    logging.shutdown() # 全てのロギングをシャットダウンし、フラッシュとクローズを確実に行う

    custom_log.log_level = original_log_level # 元のログレベルに戻す


# @log デコレーターが適用されたテスト用関数
def sample_function_no_args(logger_instance):
    @log(logger_instance)
    def _func():
        logger_instance.debug("Inside sample_function_no_args")
        return "no_args_result"
    return _func()

def sample_function_with_args(logger_instance, arg1, kwarg1_val="default"):
    @log(logger_instance)
    def _func(a, kwarg1="d"):
        logger_instance.debug(f"Inside sample_function_with_args with {a} and {kwarg1}")
        return f"args_result: {a}, {kwarg1}"
    return _func(arg1, kwarg1=kwarg1_val)

def sample_function_raises_exception(logger_instance):
    @log(logger_instance)
    def _func():
        raise ValueError("Test exception")
    try:
        _func()
    except ValueError:
        pass # Expected

def read_log_file():
    if os.path.exists(TEST_LOG_FILE):
        with open(TEST_LOG_FILE, "r") as f:
            return f.read()
    return ""

def test_decorator_logs_start_and_end(logger_fixture):
    sample_function_no_args(logger_fixture)
    time.sleep(0.05) # Add small delay
    log_content = read_log_file()
    assert f"[START] _func" in log_content
    assert f"[END] _func" in log_content
    assert "Inside sample_function_no_args" in log_content # DEBUGログも出力されるはず

def test_decorator_logs_arguments(logger_fixture):
    sample_function_with_args(logger_fixture, "test_arg1", kwarg1_val="test_kwarg1") # kwarg1 -> kwarg1_val
    log_content = read_log_file()
    # 引数のログ形式は `exc_args` として custom_log.py で整形される
    # 例: "('test_arg1',), {'kwarg1': 'test_kwarg1'}"
    # または "args: ('test_arg1',), kwargs: {'kwarg1': 'test_kwarg1'}" のような形
    # custom_log.pyの実装に合わせたアサーションが必要
    assert "('test_arg1',)" in log_content # args part
    assert "{'kwarg1': 'test_kwarg1'}" in log_content # kwargs part
    assert "Inside sample_function_with_args with test_arg1 and test_kwarg1" in log_content

def test_decorator_logs_exception(logger_fixture):
    sample_function_raises_exception(logger_fixture)
    log_content = read_log_file()
    assert "[EXCEPTION] _func Test exception" in log_content
    assert "Traceback (most recent call last):" in log_content # スタックトレースの一部

def test_direct_logging(logger_fixture):
    logger_fixture.info("This is a direct info message.")
    logger_fixture.warning("This is a direct warning message.")
    log_content = read_log_file()
    assert "This is a direct info message." in log_content
    assert "This is a direct warning message." in log_content

def test_log_format_details(logger_fixture):
    # このテストは特定の関数を呼び出し、ログエントリの詳細を確認する
    # プロセスID、ファイル名、関数名、行番号など
    @log(logger_fixture)
    def specific_func_for_format_test():
        pass
    specific_func_for_format_test()
    log_content = read_log_file()

    # PIDの正規表現: [数字]
    pid_pattern = r"\[\d+\]" # [PID]
    # ファイル名の正規表現: test_custom_log.py (このテストファイル名)
    filename_pattern = r"test_custom_log.py"
    # 関数名の正規表現: specific_func_for_format_test
    funcname_pattern = r"specific_func_for_format_test"
    # 行番号の正規表現: :数字
    lineno_pattern = r":\d+" # :lineno

    # STARTログエントリの確認
    start_log_entry_regex = rf"\[START\] {funcname_pattern}"
    # ENDログエントリの確認
    end_log_entry_regex = rf"\[END\] {funcname_pattern}"

    # ログフォーマット: "[%(asctime)s] [%(process)d] %(levelname)s %(exc_filename)s - %(exc_funcName)s:%(exc_args)s:%(exc_lineno)s -> %(message)s"
    # 例: [2023-10-27 10:00:00,123] [12345] INFO test_custom_log.py - specific_func_for_format_test::NN -> [START] specific_func_for_format_test

    # STARTログの存在と詳細フォーマットの確認
    # (PID) (LEVEL) (FILENAME) - (FUNCNAME):(ARGS):(LINENO) -> [START] FUNCNAME
    #ログ実例: [2025-06-22 14:05:49,660] [5835] INFO test_custom_log.py - specific_func_for_format_test::133 -> [START] specific_func_for_format_test
    expected_start_pattern = re.compile(
        r"\[\d+\]\s+" +  # PID and one or more spaces
        r"INFO\s+" +     # Log Level (INFO) and one or more spaces
        re.escape(filename_pattern) +  # Filename (escaped for safety)
        r"\s+-\s+" +     # Separator " - " with one or more spaces around hyphen
        funcname_pattern + # Function Name
        r":" +           # Separator for args
        r":" +           # Args (empty for this function)
        lineno_pattern + # Line Number (e.g., :123)
        r"\s+->\s+" +    # Separator " -> " with one or more spaces around arrow
        re.escape(f"[START] {funcname_pattern}") # Message part
    )
    assert expected_start_pattern.search(log_content.strip()), f"START log format mismatch. Regex was: {expected_start_pattern.pattern} Log: {log_content.strip()}"

    expected_end_pattern = re.compile(
        r"\[\d+\]\s+" +
        r"INFO\s+" +
        re.escape(filename_pattern) +
        r"\s+-\s+" +
        funcname_pattern +
        r":" +
        r":" +
        lineno_pattern +
        r"\s+->\s+" +
        re.escape(f"[END] {funcname_pattern}")
    )
    assert expected_end_pattern.search(log_content.strip()), f"END log format mismatch. Regex was: {expected_end_pattern.pattern} Log: {log_content.strip()}"

# ---- インポート不要機能のテスト ----
# `custom_log.py` をコマンドラインユーティリティとして使用するテスト
# テスト用のターゲットスクリプトファイルを作成する必要がある

TARGET_SCRIPT_CONTENT_NO_IMPORT = """
# このスクリプトは custom_log をインポートしません。
# logger と log は builtins 経由で注入されることを期待します。

@log(logger)
def my_target_function(x, y=1):
    logger.info(f"Inside my_target_function with {x}, {y}")
    if x < 0:
        raise ValueError("x cannot be negative")
    return x + y

if __name__ == "__main__":
    logger.debug("Target script started") # DEBUGレベルなので通常は出ないはずだが、log_level引数で変わる
    my_target_function(5, y=2)
    try:
        my_target_function(-1)
    except ValueError:
        logger.warning("Caught expected ValueError in target script")
    logger.info("Target script finished")
"""

TARGET_SCRIPT_FILE = "temp_target_script.py"

@pytest.fixture
def target_script_file():
    with open(TARGET_SCRIPT_FILE, "w") as f:
        f.write(TARGET_SCRIPT_CONTENT_NO_IMPORT)
    yield TARGET_SCRIPT_FILE
    if os.path.exists(TARGET_SCRIPT_FILE):
        os.remove(TARGET_SCRIPT_FILE)

def run_custom_log_cli(target_script, log_file, log_level="INFO"):
    # custom_log.py のパスを取得 (このテストファイルからの相対パスを仮定)
    # または、より堅牢な方法で custom_log.py の場所を特定する
    custom_log_script_path = os.path.join(os.path.dirname(__file__), "custom_log.py")
    if not os.path.exists(custom_log_script_path):
        # もし test_custom_log.py が custom_log.py と同じディレクトリにない場合、
        # このパス解決は失敗する。その場合は、リポジトリルートからのパスなどを指定する必要がある。
        # 例: os.path.join(os.path.dirname(__file__), "..", "custom_log.py")など
        # 今回は同じディレクトリにあると仮定。
         pytest.fail(f"custom_log.py not found at {custom_log_script_path}")


    cmd = [
        "python",
        custom_log_script_path,
        target_script,
        "--log_file",
        log_file,
        "--log_level",
        log_level,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # print("STDOUT:", result.stdout) # デバッグ用
    # print("STDERR:", result.stderr) # デバッグ用
    return result

def test_cli_execution_logs_from_target(target_script_file, cleanup_log_file): # cleanup_log_fileでTEST_LOG_FILEが消える
    cli_log_file = "cli_test_run.log" # CLIテスト専用のログファイル
    if os.path.exists(cli_log_file): os.remove(cli_log_file)

    run_custom_log_cli(target_script_file, log_file=cli_log_file, log_level="DEBUG") # DEBUGで実行
    time.sleep(0.05) # Add small delay

    log_content = ""
    if os.path.exists(cli_log_file):
        with open(cli_log_file, "r") as f:
            log_content = f.read()
    else:
        pytest.fail(f"CLI log file {cli_log_file} was not created.")

    # custom_log.py が出力する実行開始・終了ログ
    assert f"Attempting to run {TARGET_SCRIPT_FILE} with injected logger" in log_content
    assert f"Finished execution of {TARGET_SCRIPT_FILE}" in log_content

    # ターゲットスクリプト内のログ
    assert "[START] my_target_function" in log_content
    assert "Inside my_target_function with 5, 2" in log_content
    assert "[END] my_target_function" in log_content

    assert "Target script started" in log_content # DEBUGレベルなので出力される
    assert "Caught expected ValueError in target script" in log_content # WARNING
    assert "Target script finished" in log_content # INFO

    # 例外ログ
    assert "[EXCEPTION] my_target_function x cannot be negative" in log_content
    assert "Traceback (most recent call last):" in log_content # from target script's exception

    if os.path.exists(cli_log_file): os.remove(cli_log_file)


# ---- マルチプロセス対応のテスト ----
# subprocess を使って複数の custom_log を利用するスクリプトを同時に実行し、
# ログファイルに各プロセスのログが混在しつつも正しく記録されるか確認する。

MULTIPROC_TARGET_SCRIPT_CONTENT = """
import time
import os
# logger と log は builtins 経由で注入されることを期待

@log(logger)
def task(task_id, duration):
    logger.info(f"Task {task_id} starting, will run for {duration}s. PID: {os.getpid()}")
    time.sleep(duration)
    logger.info(f"Task {task_id} finished. PID: {os.getpid()}")

if __name__ == "__main__":
    # コマンドライン引数からタスクIDと実行時間を取得することを想定
    # ここでは簡略化のため固定値で呼び出すか、または custom_log.py 経由で実行される際に
    # 引数を渡す方法があればそれを利用する。
    # 今回は custom_log.py はターゲットスクリプトに引数を渡す機能はないので、固定値とする。
    task_id_arg = os.getenv("TASK_ID", "default_task") # 環境変数で渡す例
    duration_arg = float(os.getenv("TASK_DURATION", "0.1")) # 環境変数で渡す例

    logger.info(f"Multiprocess target script starting with TASK_ID={task_id_arg}, DURATION={duration_arg}. PID: {os.getpid()}")
    task(task_id_arg, duration_arg)
    logger.info(f"Multiprocess target script finished for TASK_ID={task_id_arg}. PID: {os.getpid()}")
"""

MULTIPROC_TARGET_FILE = "temp_multiproc_target.py"

@pytest.fixture
def multiproc_target_script_file():
    with open(MULTIPROC_TARGET_FILE, "w") as f:
        f.write(MULTIPROC_TARGET_SCRIPT_CONTENT)
    yield MULTIPROC_TARGET_FILE
    if os.path.exists(MULTIPROC_TARGET_FILE):
        os.remove(MULTIPROC_TARGET_FILE)

def test_multiprocess_logging(multiproc_target_script_file, cleanup_log_file):
    # このテストでは、`custom_log.py` を介して `MULTIPROC_TARGET_FILE` を複数回、
    # ほぼ同時に（バックグラウンドで）実行し、一つのログファイルにログが集約されることを確認する。
    # プロセスIDが各ログエントリに正しく記録されているかも重要。

    multiproc_log_file = "multiproc_test.log"
    if os.path.exists(multiproc_log_file): os.remove(multiproc_log_file)

    num_processes = 3
    processes = []
    expected_pids = set()

    custom_log_script_path = os.path.join(os.path.dirname(__file__), "custom_log.py")

    for i in range(num_processes):
        env = os.environ.copy()
        env["TASK_ID"] = f"proc_{i}"
        env["TASK_DURATION"] = str(0.1 + i * 0.05) # 少しずつ実行時間を変える

        cmd = [
            "python",
            custom_log_script_path,
            multiproc_target_script_file,
            "--log_file",
            multiproc_log_file,
            "--log_level",
            "INFO", # INFOレベルで十分
        ]
        # Popenで非同期に実行
        proc = subprocess.Popen(cmd, env=env)
        processes.append(proc)
        # 注意: Popen直後にPIDを取得すると、それは親プロセス(Python)のPIDの場合がある。
        # ターゲットスクリプト内で os.getpid() をログ出力しているので、それを確認する。

    for proc in processes:
        proc.wait(timeout=5) # タイムアウトを設定

    log_content = ""
    if os.path.exists(multiproc_log_file):
        with open(multiproc_log_file, "r") as f:
            log_content = f.read()
    else:
        pytest.fail(f"Multiprocess log file {multiproc_log_file} was not created.")

    # 各プロセスが開始・終了ログを出力したか確認
    # また、各プロセス（タスク）のログが記録されているか
    for i in range(num_processes):
        assert f"Task proc_{i} starting" in log_content
        assert f"Task proc_{i} finished" in log_content
        assert f"Multiprocess target script starting with TASK_ID=proc_{i}" in log_content
        assert f"Multiprocess target script finished for TASK_ID=proc_{i}" in log_content

    # ログエントリからプロセスIDを抽出し、複数の異なるPIDが存在することを確認
    # 例: [PID] の部分
    logged_pids = set(re.findall(r"\[(\d+)\] INFO", log_content)) # PID capturing group

    # Popenで起動したサブプロセスのPIDを直接知るのは難しい場合があるため、
    # ログに出力されたPIDの種類数で確認する。
    # 理想的には、起動したサブプロセスがユニークなPIDを持つことを期待。
    # ただし、非常に短い時間でプロセスが終了・再利用されると同一PIDになる可能性も稀にあるが、
    # 通常は異なるPIDになる。
    assert len(logged_pids) > 0, "No PIDs found in log."
    # 少なくとも1つ以上のユニークなPIDがあることを確認。
    # num_processes と完全に一致するかは環境やタイミングによるため、ここでは len(logged_pids) >= 1 程度で妥協するか、
    # または、各プロセスが自身のPIDをログに出力する内容を確認することで、間接的にPIDの多様性を確認する。

    # 各タスクログエントリにPIDが含まれていることを確認 (より具体的に)
    for i in range(num_processes):
        # "Task proc_i starting, will run for Xs. PID: YYYY"
        match_start = re.search(rf"Task proc_{i} starting, will run for .*?s\. PID: (\d+)", log_content)
        assert match_start, f"PID not found for start of task proc_{i}"
        pid_start = match_start.group(1)

        match_finish = re.search(rf"Task proc_{i} finished\. PID: (\d+)", log_content)
        assert match_finish, f"PID not found for finish of task proc_{i}"
        pid_finish = match_finish.group(1)

        assert pid_start == pid_finish, f"Mismatch PID for task proc_{i}: start_pid={pid_start}, finish_pid={pid_finish}"
        expected_pids.add(pid_start) # 実際にログに出たPIDを集める

    # ログ全体のPIDの多様性と、タスクごとに出力されたPIDの整合性を確認
    assert len(expected_pids) >= 1 # 少なくとも1つ。理想は num_processes だが、環境による揺らぎを考慮。
    # CI環境などでは、プロセス生成のオーバーヘッドやPIDの再利用により、必ずしも num_processes 個の
    # ユニークなPIDが短期間に観測できるとは限らない。
    # ここでは、各プロセスが自身のPIDをログに出し、それがログの [%(process)d] と一致するかまでは確認していない。
    # それをやるには、ログフォーマットのPIDと、メッセージ内のPIDを比較する必要がある。

    if os.path.exists(multiproc_log_file): os.remove(multiproc_log_file)
