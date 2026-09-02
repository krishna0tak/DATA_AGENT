from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def pick_llm(level: str):
    """
    Picks the appropriate LLM based on the level of the question.

    Args:
        level (str): The level of the question, can be "low", "medium", or "high".

    Returns:
        ChatOpenAI: The LLM instance to be used.
    """
    level = level.lower()

    if level == "low":
        llm = ChatOpenAI(
            model_name="gpt-5.6-luna",
            temperature=0,
            reasoning_effort="none",
        )
    elif level == "medium":
        llm = ChatOpenAI(
            model_name="gpt-5.6-terra",
            temperature=0,
            reasoning_effort="none",
        )
    elif level == "high":
        llm = ChatOpenAI(
            model_name="gpt-5.6-sol",
            temperature=0,
            reasoning_effort="none",
        )
    elif level == "claude":
        llm = ChatAnthropic(model_name="claude-sonnet-5")
    else:
        raise ValueError(f"Unsupported level: {level}")

    return llm


if __name__ == "__main__":
    llm_obj = pick_llm("low")
    print(llm_obj.invoke("What is the capital of France?"))