"""Terms approval domain module."""
from domain.user.terms_approval.model import TermsApproval
from domain.user.terms_approval.repository import TermsApprovalRepository

__all__ = ["TermsApproval", "TermsApprovalRepository"]
