"""
スタッフQA用AIサービス

現場向けの最低限AI（ログ＋ナレッジを元に答えるスタッフ用QA）
クラウドLLMの「一番軽いモデル」を使用し、コスト最適化を意識した設計
"""
from typing import List, Dict, Optional
from sqlmodel import Session, select
from app.core.config import settings
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.models.knowledge_item import KnowledgeItem
from app.models.conversation import Conversation, Message
from app.services.ai.client import AiClientFactory
from app.repositories.knowledge_repository import get_knowledge_context
import structlog

logger = structlog.get_logger()


class StaffQAService:
    """スタッフQA用AIサービス（軽量モデル使用）"""
    
    def __init__(self):
        # スタッフQA用の軽量モデルClientを取得
        self.ai_client = AiClientFactory.get_staff_client()
        self.max_tokens = getattr(settings, "AI_MAX_TOKENS_STAFF", 1000)
        self.temperature = getattr(settings, "AI_TEMPERATURE_STAFF", 0.5)
    
    def _build_staff_system_prompt(self, business_unit_name: str) -> str:
        """
        スタッフQA用のシステムプロンプトを構築
        
        Args:
            business_unit_name: 事業部門名（例: "ミカモ喫茶"）
        
        Returns:
            システムプロンプト文字列
        """
        return f"""あなたは株式会社ミカモの{business_unit_name}で働くスタッフの質問に答えるAIアシスタントです。

役割:
- レシピ、メニューの作り方、手順書、注意事項などの現場で必要な情報を提供する
- 簡潔で分かりやすい回答を心がける
- わからないことは「わからない」と正直に言う

回答方針:
- 日本語で、です・ます調で回答する
- 専門用語は避け、現場スタッフが理解しやすい言葉を使う
- 手順は箇条書きで明確に示す
- 安全に関する注意事項があれば必ず含める

コンテキスト:
- 以下の「関連ナレッジ情報」を参照して回答してください
- ナレッジ情報にない質問には、「申し訳ございませんが、その情報は現在登録されていません。マネージャーに確認してください。」と答えてください
"""
    
    def _build_context(
        self,
        session: Session,
        business_unit_id: Optional[int],
        conversation_id: Optional[int],
        user_question: str
    ) -> str:
        """
        スタッフQA用のコンテキストを構築（必要最小限）
        
        Args:
            session: データベースセッション
            business_unit_id: 事業部門ID
            conversation_id: 会話ID（会話履歴を取得するため）
            user_question: ユーザーの質問
        
        Returns:
            コンテキスト文字列
        """
        context_parts = []
        
        # 1. 関連ナレッジ情報を取得（事業部門に紐づくKnowledgeItem）
        if business_unit_id:
            knowledge_context = get_knowledge_context(
                session,
                query=user_question,
                business_unit_id=business_unit_id,
                limit=3  # コスト最適化のため3件まで
            )
            if knowledge_context:
                context_parts.append(f"【関連ナレッジ情報】\n{knowledge_context}\n")
        
        # 2. 直近の会話履歴（同じConversation内の最新3件まで）
        if conversation_id:
            statement = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(3)
            recent_messages = session.exec(statement).all()
            
            if recent_messages:
                # 時系列順に並び替え
                recent_messages.reverse()
                context_parts.append("【直近の会話履歴】\n")
                for msg in recent_messages:
                    role_label = "ユーザー" if msg.role == "user" else "AI"
                    context_parts.append(f"{role_label}: {msg.content[:200]}...")  # 200文字まで
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def answer_staff_question(
        self,
        session: Session,
        user: User,
        business_unit: Optional[BusinessUnit],
        user_question: str,
        conversation_id: Optional[int] = None
    ) -> str:
        """
        スタッフQA用の回答を生成
        
        Args:
            session: データベースセッション
            user: ユーザー情報
            business_unit: 事業部門情報
            user_question: ユーザーの質問
            conversation_id: 会話ID（会話履歴を取得するため）
        
        Returns:
            AIからの応答テキスト
        """
        try:
            business_unit_id = business_unit.id if business_unit else None
            business_unit_name = business_unit.name if business_unit else "全社"
            
            # システムプロンプトを構築
            system_prompt = self._build_staff_system_prompt(business_unit_name)
            
            # コンテキストを構築（必要最小限）
            context = self._build_context(
                session,
                business_unit_id,
                conversation_id,
                user_question
            )
            
            # ユーザーメッセージを構築
            user_message_content = f"""{context}

【質問】
{user_question}

上記の情報を元に、簡潔で分かりやすい回答をしてください。"""
            
            # 軽量モデルで応答を生成
            messages = [
                {"role": "user", "content": user_message_content}
            ]
            
            answer = await self.ai_client.generate_reply(
                system_prompt=system_prompt,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            
            logger.info(
                "Staff QA answer generated",
                user_id=user.id,
                business_unit_id=business_unit_id,
                question_length=len(user_question),
                answer_length=len(answer)
            )
            
            return answer
            
        except Exception as e:
            logger.error("Staff QA service error", error=str(e), exc_info=True)
            # エラー時はフォールバック応答
            return "申し訳ございませんが、現在AIサービスが利用できない状態です。しばらくしてから再度お試しください。"
    

