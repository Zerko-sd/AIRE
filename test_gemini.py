from agents.investigator.gemini_client import ask_gemini

response = ask_gemini("Why do database timeouts increase API errors?")
print(response)