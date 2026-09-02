import os 
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_core.messages import AIMessage, HumanMessage
from utils.llm_pick import pick_llm
from models.schema import AgentSchema, JudgeSchema  
from utils.database import DatabaseUtil
from langgraph.graph import StateGraph, START , END 
# ---------------------- AI Agent ---------------------- #
def curate_ques(state: AgentSchema) -> AgentSchema:
    user_question = state.user_question #pydantic model obj
    llm = pick_llm("low")  # Pick the appropriate LLM based on the level of the question
    response = llm.invoke(f"Curate the following question: {user_question}").content
    state.curated_ques = response  # Update the state with the curated question
    state.messages = state.messages + [HumanMessage(content=f" {response}")]  # Update the messages with the new question and response
    return state

def prompt_query_context(state: AgentSchema) -> AgentSchema:
    curated_ques = state.curated_ques
    conn_details = {
        "host" : os.environ['host'],
        "port" : os.environ['port'],    
        "user" : os.environ['user'],
        "password" : os.environ['password'],
        "dbname" : os.environ['database'],
    }
    obj = DatabaseUtil(conn_details)
    schema_info = obj.schema_details("public")  # Fetch schema details from the database    
     # Constructing the prompt query for the agent to generate the SQL query
    prompt = f"""
    You are an SQL analyst agent. Your task is to convert the user's natural language 
    query into Postgres SQL query that can be executed on the database. You are provided 
    with the user's original query and the schema details of the database, including
    table names, column names, data types, and sample data for each table so that 
    you can understand the structure of the database and generate an accurate SQL query.
    Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
    Note - Just generate the SQL query without any explanation or additional text because
    this query will be executed directly on the database. So, the output should be SQL
    ready to be executed without any modifications. 

    user's original query: {curated_ques}

    Database schema details: {schema_info}
    """

    state.prompt_query_context = prompt  # Update the state with the constructed prompt query
 


    return state 


#genrate sql function
def generate_sql(state:AgentSchema) -> AgentSchema:
    prompt = state.prompt_query_context
    llm = pick_llm("medium")  # Pick the appropriate LLM based on the level of the question
    generated_sql_query = llm.invoke(prompt).content  # Generate the SQL query using the LLM
    state.generated_sql_query = generated_sql_query  # Update the state with the generated SQL query
    return state




#is safe function
def is_safe_sql(state: AgentSchema) -> AgentSchema:
    sql_query = state.generated_sql_query
    llm = pick_llm("medium")  # Pick the appropriate LLM based on the level of the question

    llm_judge = llm.with_structured_output(JudgeSchema)  # Create a structured output LLM for judging the safety of the SQL query

    

    prompt = f"""
    You are an SQL Judge for data security. Your task is to determine whether the SQL query is 
    safe or not. The SQL query should only be used for data retrieval and should not modify the 
    database in any way. Neither the SQL query nor the prompt should contain any SQL commands that can modify the
    database, such as INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or any other commands that can change
    the structure or content of the database. If the SQL query is safe, respond with 'Yes' otherwise respond with 
    'No'. Additionally, provide comments explaining your decision.
    Here's the SQL query to evaluate:
    {sql_query}"""
    response = llm_judge.invoke(prompt).model_dump() 
    state.is_safe_sql_response = response['answer']  # Update the state with the safety judgment response
    return state



#canceled query function
def canceled_query(state: AgentSchema) -> AgentSchema:
    comments = state.comments

    state.final_answer = "The SQL query was deemed unsafe and has been canceled."
    state.messages = state.messages + [AIMessage(content=f"{state.final_answer}")]  # Append the final answer to the messages list
    return state

#execute sql function
def execute_sql(state: AgentSchema) -> AgentSchema:
    sql_query = state.generated_sql_query
    conn_details = {
        "host": os.environ['host'],
        "port": os.environ['port'],
        "user": os.environ['user'],
        "password": os.environ['password'],
        "dbname": os.environ['database'],
    }
    obj = DatabaseUtil(conn_details)
    execution_result = obj.execute_sql(sql_query)
    state.sql_query_execution_result = execution_result
    return state




# Represent the final answer Node
def represent_final_answer(state: AgentSchema) -> AgentSchema:

    execution_result = state.sql_query_execution_result
    curated_question = state.curated_ques

    llm = pick_llm("low")

    prompt = f"""
    You are an SQL analyst agent. Your task is to provide a final answer to the user based on the
    execution result of the SQL query and the user's original question. The final answer should be
    concise, clear, and directly address the user's query. Avoid including any SQL code or technical
    details in the final answer. The final answer should be in a user-friendly format that is easy to
    understand. If the execution result is empty or does not provide a clear answer to the user's question, explain this in the final answer. \n
    Here is the execution result: {execution_result} \n
    Here is the user's original question: {curated_question}
    """

    llm_response = llm.invoke(prompt).content  # Get the final answer from the LLM

    state.final_answer = llm_response
    state.messages = state.messages + [AIMessage(content=f"{llm_response}")]  # Append the final answer to the messages list

    return state

#---------------------- Graph Construction ---------------------- #
sql_agent_graph = StateGraph(AgentSchema)


#nodes
sql_agent_graph.add_node("curate_ques", curate_ques)
sql_agent_graph.add_node("prompt_query_context", prompt_query_context)
sql_agent_graph.add_node("generate_sql", generate_sql)
sql_agent_graph.add_node("is_safe_sql", is_safe_sql)
sql_agent_graph.add_node("canceled_query", canceled_query)
sql_agent_graph.add_node("execute_sql", execute_sql)
sql_agent_graph.add_node("represent_final_answer", represent_final_answer)

#edges
sql_agent_graph.add_edge(START, "curate_ques")
sql_agent_graph.add_edge("curate_ques", "prompt_query_context")
sql_agent_graph.add_edge("prompt_query_context", "generate_sql")
sql_agent_graph.add_edge("generate_sql", "is_safe_sql")


#Conditional edges based on the safety of the SQL query
def is_safe_sql_edge(state: AgentSchema) -> str:
    is_safe = state.is_safe_sql_response
    if str(is_safe).lower() == "yes":
        return "execute_sql"
    return "canceled_query"

sql_agent_graph.add_conditional_edges("is_safe_sql", is_safe_sql_edge ,
                                       {"execute_sql": "execute_sql", "canceled_query": "canceled_query"}) 
 # Conditional edges based on the safety of the SQL query


#sql_agent_graph.add_edge("is_safe_sql", "canceled_query")  # Edge for unsafe SQL query
#sql_agent_graph.add_edge("is_safe_sql", "execute_sql")  # Edge for safe SQL query

sql_agent_graph.add_edge("canceled_query", END)
sql_agent_graph.add_edge("execute_sql", "represent_final_answer")
sql_agent_graph.add_edge("represent_final_answer", END)

#compile the graph
sql_analyst = sql_agent_graph.compile()

if __name__ == "__main__":  

  # Optional
#from IPython.display import display, Image
#img = Image(sql_analyst.get_graph().draw_mermaid_png())
#with open("sql_analyst_graph.png", "wb") as f:
 #       f.write(img.data)

 input_schema = {
        "messages": [],
        "user_question": "What are the different types of Payment Methods we have in our database",
        "curated_ques": "",
        "prompt_query_context": "",
        "generated_sql_query": "",
        "is_safe": "No",
        "comments": "",
        "sql_query_execution_result": "",
        "final_answer": ""
    }     

 # Execute the Graph
sql_analyst_response = sql_analyst.invoke(input_schema)
print(sql_analyst_response['messages'])  # Print the final response from the SQL analyst agent
print("--------------------------------------------")
print(sql_analyst_response['generated_sql_query'])  
print("--------------------------------------------")
print(sql_analyst_response['sql_query_execution_result'])
print("--------------------------------------------")
print(sql_analyst_response['prompt_query_context'])