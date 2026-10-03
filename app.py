#from agent.agent import llm
#
#response = llm.invoke(
#    "What is DataFed? Answer in one sentence."
#)
#
#print(response.content)


from agent.agent import llm

response = llm.invoke(
    "List all datasets in collection c/525611319."
)

print(response)