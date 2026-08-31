import os 
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.llm_pick import pick_llm
from models.schema import agents_schema 

# ---------------------- AI Agent ---------------------- #
def curate_ques(state: AgentSchema) -> Agent_Schema:
    user_question = state.user_question #pydantic model obj
    llm = pick_llm("low")  # Pick the appropriate LLM based on the level of the question
    response = llm.invoke(f"Curate the following question: {user_question}")
    state.curated_ques = response  # Update the state with the curated question
    return state

def prompt_query_context(state: AgentSchema) -> AgentSchema:
    curated_ques = state.curated_ques
    llm = pick_llm("medium")  # Pick the appropriate LLM based on the level of the question
    response = llm.invoke(f"Generate a detailed prompt with SQL DB context for the following curated question: {curated_ques}")
    state.prompt_query_context = response  # Update the state with the prompt query context
    return state