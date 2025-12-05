"""
AI利用ログモデル

テナント・ユーザー・用途ごとのAI呼び出しを記録し、
コスト可視化・料金設計に活用する。

記録内容:
- どのテナント・ユーザーが
- どの用途（purpose）で
- どのティア・モデルを使い
- どれだけトークンを消費したか
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class AiUsageLog(SQLModel, table=True):
    """AI利用ログモデル（コスト可視化・従量課金設計用）"""
    __tablename__ = "ai_usage_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # テナント・ユーザー情報
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    business_unit_id: Optional[int] = Field(default=None, foreign_key="business_units.id")

    # AI呼び出し情報
    purpose: str = Field(index=True)  # "staff_qa", "management_decision" など
    tier: str = Field(index=True)     # "basic", "standard", "premium"
    model: str                        # 実際に呼ばれたモデル名

    # トークン使用量（取得できない場合はnull）
    tokens_input: Optional[int] = Field(default=None)
    tokens_output: Optional[int] = Field(default=None)

    # 応答時間（ミリ秒、取得できない場合はnull）
    response_time_ms: Optional[int] = Field(default=None)

    # エラー情報（成功時はnull）
    error: Optional[str] = Field(default=None)

    # 会話ID（紐づく会話がある場合）
    conversation_id: Optional[int] = Field(default=None, foreign_key="conversations.id")
