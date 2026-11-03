

class TokenBudgetManager:
    """
    Tracks and enforces token and budget ceilings across all triggers (A15):
    - Per-run ceiling: 60,000 tokens.
    - Gracefully halts execution with partial state when ceiling is breached.
    """

    def __init__(self, max_run_tokens: int = 60000, current_run_tokens: int = 0):
        self.max_run_tokens = max_run_tokens
        self.current_run_tokens = current_run_tokens

    def can_proceed(self, estimated_tokens: int = 0) -> bool:
        return (self.current_run_tokens + estimated_tokens) <= self.max_run_tokens

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.current_run_tokens += prompt_tokens + completion_tokens

    def get_stop_reason(self) -> str | None:
        if self.current_run_tokens > self.max_run_tokens:
            return "QUOTA_EXCEEDED"
        return None
