"""
ミドルウェア（リクエストID生成、エラーハンドリング）
"""
import uuid
import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

logger = structlog.get_logger()


async def add_request_id(request: Request, call_next):
    """
    リクエストごとにrequest_idを生成し、ログに紐づける
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # コンテキスト変数にrequest_idを設定
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def global_exception_handler(request: Request, exc: Exception):
    """
    未捕捉例外を一元的に処理
    クライアントには一般化されたエラーレスポンスを返し、
    ログには詳細を記録
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # ログに詳細を記録（PIIは含めない）
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=traceback.format_exc(),
    )
    
    # クライアントには一般化されたエラーを返す
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "内部サーバーエラーが発生しました。しばらく時間をおいて再度お試しください。",
            "request_id": request_id,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTP例外を処理
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "http_exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    バリデーション例外を処理
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "validation_error",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "入力データに誤りがあります。",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )

