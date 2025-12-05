"""
スタッフQA用AIサービス

現場向けの最低限AI（ログ＋ナレッジを元に答えるスタッフ用QA）
クラウドLLMの「一番軽いモデル」を使用し、コスト最適化を意識した設計

SaaS対応: テナント設定からAIプロンプトを動的に取得
"""
from typing import Optional
from sqlmodel import Session, select
from app.core.config import settings
from app.models.user import User
from app.models.business_unit import BusinessUnit
from app.models.conversation import Message
from app.models.tenant import Tenant, TenantSettings
from app.services.ai.client import AiClientFactory
from app.repositories.knowledge_repository import get_knowledge_context
import structlog

logger = structlog.get_logger()


# デフォルトのシステムプロンプトテンプレート
# TenantSettings.ai_company_context が設定されている場合はそちらを優先
DEFAULT_STAFF_PROMPT_TEMPLATE = """あなたは{company_name}の{business_unit_name}で働くスタッフの質問に答えるAIアシスタントです。

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


class StaffQAService:
    """スタッフQA用AIサービス（軽量モデル使用）"""

    def __init__(self, tenant_settings: Optional[TenantSettings] = None):
        """
        スタッフQAサービスを初期化

        Args:
            tenant_settings: テナント設定（ティアポリシー適用用）
        """
        # テナントのティアポリシーを取得
        self._purpose = "staff_qa"
        if tenant_settings and tenant_settings.ai_tier_policy:
            # ティアポリシーを適用してクライアントを作成
            self.ai_client = AiClientFactory.create_for_purpose_with_policy(
                self._purpose,
                tenant_settings.ai_tier_policy
            )
            # effective tierを計算して保存
            original_tier = AiClientFactory.get_tier_for_purpose(self._purpose)
            self._effective_tier = AiClientFactory.apply_tier_policy(
                original_tier,
                tenant_settings.ai_tier_policy
            ).value
        else:
            # デフォルト: スタッフQA用の軽量モデルClientを取得
            self.ai_client = AiClientFactory.get_staff_client()
            self._effective_tier = AiClientFactory.get_tier_for_purpose(self._purpose).value

        # モデル名を保存（ログ用）
        self._model = getattr(self.ai_client, "model", "unknown")

        # テナント設定のトークン上限をオーバーライド
        if tenant_settings and tenant_settings.ai_max_tokens_override:
            self.max_tokens = tenant_settings.ai_max_tokens_override
        else:
            self.max_tokens = getattr(settings, "AI_MAX_TOKENS_STAFF", 1000)

        self.temperature = getattr(settings, "AI_TEMPERATURE_STAFF", 0.5)

    @property
    def purpose(self) -> str:
        """用途を取得"""
        return self._purpose

    @property
    def effective_tier(self) -> str:
        """ポリシー適用後のティアを取得"""
        return self._effective_tier

    @property
    def model_name(self) -> str:
        """使用モデル名を取得"""
        return self._model

    def _get_tenant_settings(self, session: Session, tenant_id: int) -> Optional[TenantSettings]:
        """
        テナント設定を取得

        Args:
            session: データベースセッション
            tenant_id: テナントID

        Returns:
            TenantSettingsオブジェクト（存在しない場合はNone）
        """
        statement = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        return session.exec(statement).first()

    def _build_staff_system_prompt(
        self,
        business_unit_name: str,
        tenant_settings: Optional[TenantSettings] = None,
        company_name: str = "DXポータル"
    ) -> str:
        """
        スタッフQA用のシステムプロンプトを構築

        テナント設定が存在する場合は ai_company_context を使用し、
        存在しない場合はデフォルトテンプレートを使用する。

        Args:
            business_unit_name: 事業部門名（例: "ミカモ喫茶"）
            tenant_settings: テナント設定（オプション）
            company_name: 会社名（テナント設定がない場合のフォールバック）

        Returns:
            システムプロンプト文字列
        """
        # テナント設定からカスタムコンテキストを取得
        if tenant_settings and tenant_settings.ai_company_context:
            # カスタムコンテキストがある場合は、それをベースにプロンプトを構築
            base_context = tenant_settings.ai_company_context
            return f"""{base_context}

現在、{business_unit_name}のスタッフからの質問に回答しています。

回答方針:
- 日本語で、です・ます調で回答する
- 専門用語は避け、現場スタッフが理解しやすい言葉を使う
- 手順は箇条書きで明確に示す
- 安全に関する注意事項があれば必ず含める

コンテキスト:
- 以下の「関連ナレッジ情報」を参照して回答してください
- ナレッジ情報にない質問には、「申し訳ございませんが、その情報は現在登録されていません。マネージャーに確認してください。」と答えてください
"""
        else:
            # デフォルトテンプレートを使用
            return DEFAULT_STAFF_PROMPT_TEMPLATE.format(
                company_name=company_name,
                business_unit_name=business_unit_name
            )
    
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

            # テナント設定を取得（SaaS対応: プロンプトをテナントごとにカスタマイズ）
            tenant_settings = None
            company_name = "DXポータル"  # フォールバック
            if user.tenant_id:
                tenant_settings = self._get_tenant_settings(session, user.tenant_id)
                # テナントの表示名を取得
                tenant = session.get(Tenant, user.tenant_id)
                if tenant:
                    company_name = tenant.display_name

            # システムプロンプトを構築（テナント設定を反映）
            system_prompt = self._build_staff_system_prompt(
                business_unit_name=business_unit_name,
                tenant_settings=tenant_settings,
                company_name=company_name
            )

            logger.debug(
                "Building staff QA prompt",
                tenant_id=user.tenant_id,
                has_tenant_settings=tenant_settings is not None,
                company_name=company_name
            )
            
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
            
        except ValueError as e:
            error_msg = str(e)
            logger.error("Staff QA configuration error", error=error_msg, user_id=user.id)

            # 設定エラーの場合は具体的なメッセージを返す
            if "ANTHROPIC_API_KEY" in error_msg:
                raise ValueError(
                    "ai_not_configured:AIサービスの設定が完了していません。"
                    "管理者に ANTHROPIC_API_KEY の設定を依頼してください。"
                )
            elif "model not configured" in error_msg.lower():
                raise ValueError(
                    "ai_not_configured:AIモデルの設定が完了していません。"
                    "管理者に ANTHROPIC_MODEL_* の設定を依頼してください。"
                )
            else:
                raise

        except Exception as e:
            logger.error("Staff QA service error", error=str(e), exc_info=True)
            # エラー時はフォールバック応答
            raise ValueError(
                "ai_error:AIサービスで問題が発生しました。"
                "しばらくしてから再度お試しください。"
            )
    

