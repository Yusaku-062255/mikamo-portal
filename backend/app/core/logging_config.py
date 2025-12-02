"""
ロギング設定（JSON形式、Cloud Logging対応）
"""
import logging
import sys
import structlog
from typing import Any


def setup_logging():
    """
    ロギングを設定（JSON形式で出力、Cloud Logging対応）
    """
    # 標準ロギングの設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # structlogの設定
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # コンテキスト変数をマージ
            structlog.processors.add_log_level,  # ログレベルを追加
            structlog.processors.TimeStamper(fmt="iso"),  # ISO形式のタイムスタンプ
            structlog.processors.StackInfoRenderer(),  # スタック情報
            structlog.processors.format_exc_info,  # 例外情報
            structlog.processors.JSONRenderer()  # JSON形式で出力
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> Any:
    """
    ロガーを取得
    
    Args:
        name: ロガー名（省略時は呼び出し元のモジュール名）
    
    Returns:
        structlogロガー
    """
    return structlog.get_logger(name)

