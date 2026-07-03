_AI_SIGNALS = (
    "gpt",
    "oai",
    "openai",
    "claude",
    "anthropic",
    "perplexity",
    "cohere",
    "ai2",
    "gemini",
    "bytespider",
    "ccbot",
    "diffbot",
    "youbot",
    "timpi",
    "omgili",
    "imagesift",
    "google-extended",
    "externalagent",
)


def _product_tokens(user_agent: str):
    text = user_agent.replace("(", " ").replace(")", " ").replace(";", " ")
    for token in text.split():
        yield token.split("/", 1)[0]


def ai_bot_name(user_agent: str) -> str | None:
    """Product name of AI/LLM crawler via keyword heuristic, else None"""
    for name in _product_tokens(user_agent):
        low = name.lower()
        if any(signal in low for signal in _AI_SIGNALS):
            return name
    return None


def is_ai_bot(user_agent: str) -> bool:
    """User agent belongs to an AI/LLM crawler"""
    return ai_bot_name(user_agent) is not None
