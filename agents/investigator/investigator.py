from agents.investigator.gemini_client import ask_gemini
from tools.prometheus_tool import query_prometheus
from tools.log_tool import search_logs
from agents.investigator.tool_registry import (TOOLS, TOOL_DESCRIPTIONS)
import re

logs = search_logs("database")

metrics = query_prometheus("login_errors_total")

incident = """
High login error rate detected.
Users experiencing DB timeout failures.
"""
conversation = f"""
    You are an autonomous SRE investigator.

    {TOOL_DESCRIPTIONS}

    Incident:
    {incident}
    Think step-by-step.
    If you need a tool,
    respond ONLY in this format:
    TOOL: tool_name("argument")
    When you know the answer,
    respond with:
    FINAL: your conclusion
"""

while True:
    response = ask_gemini(conversation)
    print("Gemini response:\n", response)

    #Tool Call
    if response.startswith("TOOL:"):
        tool_call = response.replace("TOOL:", "").strip()
        match = re.match(
        r'(\w+)\("(.*)"\)',
        tool_call
)

        tool_name = match.group(1) if match else ""
        argument = match.group(2) if match else ""

        tool = TOOLS[tool_name]
        result = tool(argument)
        print("\n Tool result:\n", result)
        conversation += f"""
        Gemini requested tool: {tool_call}
        Tool Results: {result}
        """
    elif response.startswith("FINAL:"):
        print("\nINVESTIGATION COMPLETE")
        break

print(response)