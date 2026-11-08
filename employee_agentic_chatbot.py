import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import json
from typing import *
from dotenv import load_dotenv
from mysql_connectivity import MySQLConnector
from datetime import datetime
import traceback
import pandas as pd
load_dotenv(override=True)

# --------------------------------------------------------------------------- #
# Azure OpenAI configuration.
#
# AzureChatOpenAI reads these from the environment (set them in your .env):
#   AZURE_OPENAI_ENDPOINT   e.g. https://my-resource.openai.azure.com/
#   AZURE_OPENAI_API_KEY    your Azure OpenAI key
#   OPENAI_API_VERSION      e.g. 2024-10-21
#
# On Azure you reference a *deployment name* (what you named the model when you
# deployed it), not the base model name. Set the two below to your deployments.
# --------------------------------------------------------------------------- #


ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL")
SUBAGENT_MODEL = os.environ.get("SUBAGENT_MODEL")

def _subagent_llm(temperature: float) -> AzureChatOpenAI | ChatOpenAI:\
    # low temperature: precise and concise output
    # high temperature: creative varied output
    return ChatOpenAI(model=SUBAGENT_MODEL, temperature=temperature)
    # azure openai deployment
    # return AzureChatOpenAI(azure_deployment=SUBAGENT_MODEL, 
    #                        api_version="2025-04-01-preview", 
    #                        temperature=temperature
    #                        )
    


# --------------------------------------------------------------------------- #
# Sub-agents — each is a focused LLM call exposed to the orchestrator as a tool.
# The docstring is the description the orchestrator uses to route work, so keep
# it informative.
# --------------------------------------------------------------------------- #

@tool
def get_database_schema() -> str:
    '''Gets the database schema (CREATE TABLE DDL for every table) for the employees db.
    ** This agent has to be mandatorily run first before query_runner
    '''
    print("\t[get_database_schema] invoked")
    employees_db = MySQLConnector(database_name="employees")
    try:
        # 1. List all tables in the database
        tables = employees_db.execute_query("SHOW TABLES;")
        # SHOW TABLES returns rows like {"Tables_in_employees": "departments"}

        # 2. Get the full DDL for each table
        schema_parts = []
        if isinstance(tables, pd.DataFrame):
            for index, row in tables.iterrows():
                name = row['Tables_in_employees']
                ddl = employees_db.execute_query(f"SHOW CREATE TABLE `{name}`;")
                # SHOW CREATE TABLE returns {"Table": ..., "Create Table": "CREATE TABLE ..."}
                if isinstance(ddl, pd.DataFrame) and ddl.iloc[0].get("Create Table"):
                    schema_parts.append(ddl.iloc[0]["Create Table"])

        return "\n\n".join(schema_parts)
    finally:
        employees_db.close()

@tool
def query_runner(query:str):
    '''Runs a query in the employees database'''
    print("\t[query_runner] invoked")
    # save the query in file
    with open("employee_agentic_chatbot.sql", "a") as f:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n\n-- {now}\n")
        f.write(query)
    # execute the query
    employees_db = MySQLConnector(database_name="employees")
    try:
        query_result = employees_db.execute_query(query)
        if isinstance(query_result, pd.DataFrame):
            return query_result.astype(str).to_json(orient='records')
    except:
        return f"Error getting schema:\n{traceback.format_exc()}"
    finally:
        employees_db.close()

@tool
def simplify_query(query:str) -> str:
    """This method will simplify a complex query forming multiple joins or timeout is faced"""
    subagent_llm = ChatOpenAI(model=SUBAGENT_MODEL, temperature=0.8)
    query_simplification_system_prompt = (
        "You are an expert sql simplification agent"
        "Simplify the given query into CTEs"
    )
    subagent_messages = [
        SystemMessage(query_simplification_system_prompt),
        HumanMessage(query)
    ]
    message = subagent_llm.invoke(subagent_messages)
    return str(message.content)

def orchestrator(user_task: str, max_steps: int = 8) -> str:
    """Drive the multi-agent workflow until the orchestrator produces a final answer."""
    
    ORCHESTRATOR_SYSTEM_PROMPT = (
        "You are an orchestrator that has access to specialized agents."
        "Any query related to employees table: always use tools."
        "For any other query answer directly from your knowledge"

    )
    SUBAGENTS = [get_database_schema, query_runner, simplify_query]
    TOOLS_BY_NAME = {t.name: t for t in SUBAGENTS}

    
    # orchestrator = AzureChatOpenAI(
    #     azure_deployment=ORCHESTRATOR_MODEL,
    #     api_version="2025-04-01-preview",
    #     temperature=0.2
    # ).bind_tools(SUBAGENTS)

    orchestrator = ChatOpenAI(model=ORCHESTRATOR_MODEL, temperature=0.2).bind_tools(SUBAGENTS)

    messages:List[SystemMessage | HumanMessage | AIMessage | ToolMessage] = [
        SystemMessage(ORCHESTRATOR_SYSTEM_PROMPT),
        HumanMessage(user_task),
    ]

    for step in range(max_steps):
        print(f"\n[orchestrator] planning step {step + 1}...")
        ai_message = orchestrator.invoke(messages)
        messages.append(ai_message)

        # No tool calls => the orchestrator is done and returned the answer.
        if not ai_message.tool_calls:
            # export the messages
            with open("messages.json", "w") as f:
                message_json = [(elem.type, elem.text) for elem in messages]
                json.dump(message_json, f, indent=4)
            return str(ai_message.content)

        # Execute each requested sub-agent and feed results back.
        for call in ai_message.tool_calls:
            agent = TOOLS_BY_NAME.get(call["name"])
            result = (
                agent.invoke(call["args"])
                if agent
                else f"ERROR: unknown sub-agent '{call['name']}'"
            )
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    return (
        "Reached the maximum number of steps without a final answer. "
        "Consider raising `max_steps` or simplifying the task."
    )

if __name__ == '__main__':
    while True:
        print("*"*100)
        query = input("Enter your query. Press CTRL + C to quit: ")
        orchestrator_response = orchestrator(user_task=query)
        print("Agent Response::::\n", orchestrator_response)

