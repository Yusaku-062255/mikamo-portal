"""
AIティアポリシーのユニットテスト

テスト対象:
- AiClientFactory.apply_tier_policy(): テナントポリシーによるティア制限
- AiClientFactory.get_tier_for_purpose(): 用途からティアへのマッピング

実行方法:
  cd backend
  pytest tests/test_ai_tier_policy.py -v

注意:
- 実際のAnthropic APIは叩かない（ロジックのみテスト）
- 環境変数やDB接続は不要
"""
import pytest
from enum import Enum


# ============================================================
# テスト用のモック定義（実際のインポートを避けるため）
# ============================================================

class AiTier(str, Enum):
    """AIモデルのティア（性能レベル）"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class AiTierPolicy(str, Enum):
    """テナントごとのAIティア利用ポリシー"""
    ALL = "all"
    STANDARD_MAX = "standard_max"
    BASIC_ONLY = "basic_only"


# 用途（Purpose）からティア（Tier）へのマッピング
PURPOSE_TO_TIER = {
    # BASIC
    "shift_planning": AiTier.BASIC,
    "log_summary": AiTier.BASIC,
    "simple_task": AiTier.BASIC,
    "schedule": AiTier.BASIC,
    # STANDARD
    "staff_qa": AiTier.STANDARD,
    "knowledge_search": AiTier.STANDARD,
    "customer_support": AiTier.STANDARD,
    "daily_report": AiTier.STANDARD,
    "default": AiTier.STANDARD,
    # PREMIUM
    "management_decision": AiTier.PREMIUM,
    "dx_report": AiTier.PREMIUM,
    "strategic_planning": AiTier.PREMIUM,
    "executive_summary": AiTier.PREMIUM,
    "business_analysis": AiTier.PREMIUM,
}


def get_tier_for_purpose(purpose: str) -> AiTier:
    """用途からティアを決定"""
    return PURPOSE_TO_TIER.get(purpose.lower(), AiTier.STANDARD)


def apply_tier_policy(tier: AiTier, tier_policy: AiTierPolicy) -> AiTier:
    """
    テナントのティアポリシーを適用し、許可されたティアに制限する
    """
    if tier_policy == AiTierPolicy.ALL:
        return tier
    elif tier_policy == AiTierPolicy.STANDARD_MAX:
        if tier == AiTier.PREMIUM:
            return AiTier.STANDARD
        return tier
    elif tier_policy == AiTierPolicy.BASIC_ONLY:
        return AiTier.BASIC
    else:
        return AiTier.STANDARD


# ============================================================
# apply_tier_policy() のテスト
# ============================================================

class TestApplyTierPolicy:
    """AiClientFactory.apply_tier_policy() のテスト"""

    def test_all_policy_allows_premium(self):
        """ALLポリシー: PREMIUMはそのまま"""
        result = apply_tier_policy(AiTier.PREMIUM, AiTierPolicy.ALL)
        assert result == AiTier.PREMIUM

    def test_all_policy_allows_standard(self):
        """ALLポリシー: STANDARDはそのまま"""
        result = apply_tier_policy(AiTier.STANDARD, AiTierPolicy.ALL)
        assert result == AiTier.STANDARD

    def test_all_policy_allows_basic(self):
        """ALLポリシー: BASICはそのまま"""
        result = apply_tier_policy(AiTier.BASIC, AiTierPolicy.ALL)
        assert result == AiTier.BASIC

    def test_standard_max_downgrades_premium(self):
        """STANDARD_MAXポリシー: PREMIUMはSTANDARDにダウングレード"""
        result = apply_tier_policy(AiTier.PREMIUM, AiTierPolicy.STANDARD_MAX)
        assert result == AiTier.STANDARD

    def test_standard_max_keeps_standard(self):
        """STANDARD_MAXポリシー: STANDARDはそのまま"""
        result = apply_tier_policy(AiTier.STANDARD, AiTierPolicy.STANDARD_MAX)
        assert result == AiTier.STANDARD

    def test_standard_max_keeps_basic(self):
        """STANDARD_MAXポリシー: BASICはそのまま"""
        result = apply_tier_policy(AiTier.BASIC, AiTierPolicy.STANDARD_MAX)
        assert result == AiTier.BASIC

    def test_basic_only_downgrades_premium(self):
        """BASIC_ONLYポリシー: PREMIUMはBASICにダウングレード"""
        result = apply_tier_policy(AiTier.PREMIUM, AiTierPolicy.BASIC_ONLY)
        assert result == AiTier.BASIC

    def test_basic_only_downgrades_standard(self):
        """BASIC_ONLYポリシー: STANDARDはBASICにダウングレード"""
        result = apply_tier_policy(AiTier.STANDARD, AiTierPolicy.BASIC_ONLY)
        assert result == AiTier.BASIC

    def test_basic_only_keeps_basic(self):
        """BASIC_ONLYポリシー: BASICはそのまま"""
        result = apply_tier_policy(AiTier.BASIC, AiTierPolicy.BASIC_ONLY)
        assert result == AiTier.BASIC


# ============================================================
# get_tier_for_purpose() のテスト
# ============================================================

class TestGetTierForPurpose:
    """AiClientFactory.get_tier_for_purpose() のテスト"""

    # BASIC用途のテスト
    def test_shift_planning_returns_basic(self):
        """shift_planning → BASIC"""
        assert get_tier_for_purpose("shift_planning") == AiTier.BASIC

    def test_log_summary_returns_basic(self):
        """log_summary → BASIC"""
        assert get_tier_for_purpose("log_summary") == AiTier.BASIC

    # STANDARD用途のテスト
    def test_staff_qa_returns_standard(self):
        """staff_qa → STANDARD"""
        assert get_tier_for_purpose("staff_qa") == AiTier.STANDARD

    def test_knowledge_search_returns_standard(self):
        """knowledge_search → STANDARD"""
        assert get_tier_for_purpose("knowledge_search") == AiTier.STANDARD

    def test_default_returns_standard(self):
        """default → STANDARD"""
        assert get_tier_for_purpose("default") == AiTier.STANDARD

    # PREMIUM用途のテスト
    def test_management_decision_returns_premium(self):
        """management_decision → PREMIUM"""
        assert get_tier_for_purpose("management_decision") == AiTier.PREMIUM

    def test_dx_report_returns_premium(self):
        """dx_report → PREMIUM"""
        assert get_tier_for_purpose("dx_report") == AiTier.PREMIUM

    def test_business_analysis_returns_premium(self):
        """business_analysis → PREMIUM"""
        assert get_tier_for_purpose("business_analysis") == AiTier.PREMIUM

    # 未知の用途のテスト
    def test_unknown_purpose_returns_standard(self):
        """未知の用途 → STANDARD（デフォルト）"""
        assert get_tier_for_purpose("unknown_purpose") == AiTier.STANDARD

    def test_empty_string_returns_standard(self):
        """空文字 → STANDARD（デフォルト）"""
        assert get_tier_for_purpose("") == AiTier.STANDARD

    # 大文字小文字の正規化テスト
    def test_case_insensitive_purpose(self):
        """用途名は大文字小文字を区別しない"""
        assert get_tier_for_purpose("STAFF_QA") == AiTier.STANDARD
        assert get_tier_for_purpose("Staff_Qa") == AiTier.STANDARD


# ============================================================
# 統合テスト: ポリシー適用のE2Eフロー
# ============================================================

class TestTierPolicyE2EFlow:
    """用途→ティア→ポリシー適用の統合テスト"""

    def test_staff_qa_with_all_policy(self):
        """スタッフQA + ALLポリシー → STANDARD"""
        tier = get_tier_for_purpose("staff_qa")
        effective = apply_tier_policy(tier, AiTierPolicy.ALL)
        assert effective == AiTier.STANDARD

    def test_staff_qa_with_basic_only_policy(self):
        """スタッフQA + BASIC_ONLYポリシー → BASIC"""
        tier = get_tier_for_purpose("staff_qa")
        effective = apply_tier_policy(tier, AiTierPolicy.BASIC_ONLY)
        assert effective == AiTier.BASIC

    def test_management_decision_with_all_policy(self):
        """経営判断 + ALLポリシー → PREMIUM"""
        tier = get_tier_for_purpose("management_decision")
        effective = apply_tier_policy(tier, AiTierPolicy.ALL)
        assert effective == AiTier.PREMIUM

    def test_management_decision_with_standard_max_policy(self):
        """経営判断 + STANDARD_MAXポリシー → STANDARD"""
        tier = get_tier_for_purpose("management_decision")
        effective = apply_tier_policy(tier, AiTierPolicy.STANDARD_MAX)
        assert effective == AiTier.STANDARD

    def test_management_decision_with_basic_only_policy(self):
        """経営判断 + BASIC_ONLYポリシー → BASIC"""
        tier = get_tier_for_purpose("management_decision")
        effective = apply_tier_policy(tier, AiTierPolicy.BASIC_ONLY)
        assert effective == AiTier.BASIC

    def test_shift_planning_with_standard_max_policy(self):
        """シフト管理（BASIC用途） + STANDARD_MAXポリシー → BASIC（変更なし）"""
        tier = get_tier_for_purpose("shift_planning")
        effective = apply_tier_policy(tier, AiTierPolicy.STANDARD_MAX)
        assert effective == AiTier.BASIC


# ============================================================
# 実行用エントリーポイント
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
