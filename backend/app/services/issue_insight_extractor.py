"""
Issue/Insight抽出サービス

AIレスポンスからIssue/Insightを自動抽出する
"""
import json
import re
from typing import Optional, Dict, Any
from app.models.issue import IssueTopic
from app.models.insight import InsightType
import structlog

logger = structlog.get_logger()


def extract_issue_insight_from_ai_response(
    ai_response: str,
    user_question: str
) -> Dict[str, Any]:
    """
    AIレスポンスからIssue/Insight情報を抽出
    
    Args:
        ai_response: AIからの応答テキスト
        user_question: ユーザーの質問
    
    Returns:
        {
            "issue": {
                "title": str,
                "description": str,
                "topic": IssueTopic
            } or None,
            "insight": {
                "title": str,
                "content": str,
                "type": InsightType,
                "score": int
            } or None
        }
    """
    result = {
        "issue": None,
        "insight": None
    }
    
    # JSON形式で返されている場合を検出
    json_pattern = r'\{[^{}]*"issue_[^{}]*\{[^{}]*\}[^{}]*\}|"insight_[^{}]*\{[^{}]*\}[^{}]*\}'
    
    # まず、明示的なJSONブロックを探す
    json_block_pattern = r'```json\s*(\{.*?\})\s*```'
    json_match = re.search(json_block_pattern, ai_response, re.DOTALL)
    
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            if "issue_title" in json_data or "issue_description" in json_data:
                result["issue"] = {
                    "title": json_data.get("issue_title", user_question[:100]),
                    "description": json_data.get("issue_description", user_question),
                    "topic": _infer_issue_topic(user_question, json_data.get("issue_topic"))
                }
            if "insight_title" in json_data or "insight_content" in json_data:
                result["insight"] = {
                    "title": json_data.get("insight_title", ""),
                    "content": json_data.get("insight_content", ""),
                    "type": _infer_insight_type(json_data.get("insight_type")),
                    "score": min(100, max(0, json_data.get("insight_score", 0)))
                }
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from AI response")
    
    # JSONが見つからない場合、キーワードベースで推測
    # 重要度が高いと判断される場合のみIssue/Insightを作成
    
    # Issueの推測: ユーザーの質問が「困りごと」を示している場合
    if _is_issue_like(user_question):
        result["issue"] = {
            "title": user_question[:100],
            "description": user_question,
            "topic": _infer_issue_topic(user_question)
        }
    
    # Insightの推測: AI応答に「提案」「リスク」「機会」などのキーワードが含まれる場合
    insight_info = _extract_insight_from_text(ai_response)
    if insight_info and insight_info["score"] >= 60:  # 重要度が60以上の場合のみ
        result["insight"] = insight_info
    
    return result


def _is_issue_like(question: str) -> bool:
    """質問が「困りごと」を示しているか判定"""
    issue_keywords = [
        "困", "問題", "できない", "わからない", "どうすれば", "方法",
        "エラー", "失敗", "うまくいかない", "改善", "課題"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in issue_keywords)


def _infer_issue_topic(question: str, explicit_topic: Optional[str] = None) -> IssueTopic:
    """質問からIssueトピックを推測"""
    if explicit_topic:
        try:
            return IssueTopic(explicit_topic.lower())
        except ValueError:
            pass
    
    question_lower = question.lower()
    
    if any(kw in question_lower for kw in ["メニュー", "レシピ", "作り方", "調理"]):
        return IssueTopic.MENU
    elif any(kw in question_lower for kw in ["手順", "オペレーション", "作業", "やり方"]):
        return IssueTopic.OPERATION
    elif any(kw in question_lower for kw in ["クレーム", "苦情", "不満", "文句"]):
        return IssueTopic.CUSTOMER_COMPLAINT
    elif any(kw in question_lower for kw in ["将来", "リスク", "不安", "心配", "EV", "電気自動車"]):
        return IssueTopic.FUTURE_RISK
    elif any(kw in question_lower for kw in ["売上", "売れる", "伸ばす", "増やす", "機会"]):
        return IssueTopic.SALES_OPPORTUNITY
    elif any(kw in question_lower for kw in ["人員", "採用", "スタッフ", "人手"]):
        return IssueTopic.STAFFING
    else:
        return IssueTopic.OTHER


def _infer_insight_type(insight_type_str: Optional[str] = None) -> InsightType:
    """Insightタイプを推測"""
    if insight_type_str:
        try:
            return InsightType(insight_type_str.lower())
        except ValueError:
            pass
    return InsightType.IMPROVEMENT


def _extract_insight_from_text(text: str) -> Optional[Dict[str, Any]]:
    """テキストからInsight情報を抽出"""
    text_lower = text.lower()
    
    # リスクキーワード
    risk_keywords = ["リスク", "危険", "問題", "課題", "懸念", "不安"]
    # 機会キーワード
    opportunity_keywords = ["機会", "チャンス", "伸ばす", "拡大", "成長", "可能性"]
    # 改善キーワード
    improvement_keywords = ["改善", "提案", "推奨", "おすすめ", "試す", "検討"]
    
    insight_type = InsightType.IMPROVEMENT
    score = 50  # デフォルトスコア
    
    if any(kw in text_lower for kw in risk_keywords):
        insight_type = InsightType.RISK
        score = 70
    elif any(kw in text_lower for kw in opportunity_keywords):
        insight_type = InsightType.OPPORTUNITY
        score = 65
    elif any(kw in text_lower for kw in improvement_keywords):
        insight_type = InsightType.IMPROVEMENT
        score = 60
    
    # 重要度を示すキーワードでスコアを調整
    if any(kw in text_lower for kw in ["重要", "緊急", "早急", "すぐ", "今すぐ"]):
        score = min(100, score + 20)
    if any(kw in text_lower for kw in ["軽微", "小さな", "少し"]):
        score = max(0, score - 10)
    
    # スコアが60未満の場合はNoneを返す（重要度が低い）
    if score < 60:
        return None
    
    # タイトルとコンテンツを抽出（簡易版）
    lines = text.split("\n")
    title = lines[0][:100] if lines else "AIによる提案"
    content = text[:500]  # 最初の500文字
    
    return {
        "title": title,
        "content": content,
        "type": insight_type,
        "score": score
    }

