import os
import sys
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from ast_grounding import RepoGroundingIndex

def test_ast_symbol_indexing():
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    indexer = RepoGroundingIndex(sample_dir)
    index = indexer.build_index()

    assert "payment_service.py" in index
    assert "auth_middleware.py" in index
    assert "issue_router.py" in index

    # Verify payment_service functions
    payment_meta = index["payment_service.py"]
    fn_names = [f["name"] for f in payment_meta.get("functions", [])]
    assert "calculate_gst_total" in fn_names
    assert "process_razorpay_webhook" in fn_names

def test_critic_blocks_hallucinated_symbol():
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    indexer = RepoGroundingIndex(sample_dir)
    indexer.build_index()

    # Pass ungrounded symbol
    passed, issues, receipt = indexer.verify_claim_or_patch(
        target_file="payment_service.py",
        proposed_code="def calculate_gst_total(a, b): return a + b\n",
        referenced_symbols=["calculate_gst_total", "auto_magic_refund_sdk()"]
    )

    assert not passed
    assert any("auto_magic_refund_sdk" in issue for issue in issues)
    assert "auto_magic_refund_sdk()" in receipt["missing_symbols"]

def test_critic_approves_grounded_patch():
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    indexer = RepoGroundingIndex(sample_dir)
    indexer.build_index()

    grounded_code = (
        "def calculate_gst_total(subtotal_inr: float, tax_rate: float = 0.18) -> float:\n"
        "    return round(subtotal_inr * (1.0 + tax_rate), 2)\n"
    )

    passed, issues, receipt = indexer.verify_claim_or_patch(
        target_file="payment_service.py",
        proposed_code=grounded_code,
        referenced_symbols=["calculate_gst_total"]
    )

    assert passed
    assert len(issues) == 0
    assert receipt["target_file_exists"] is True
    assert receipt["ast_syntax_valid"] is True
