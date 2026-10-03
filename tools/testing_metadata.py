#from tools.datafed_tool import DataFedTool

#df = DataFedTool()
#metadata = df.get_metadata("d/525688177")
#print(metadata)


from tools.langchain_tools import search_collection

result = search_collection.invoke(
    {"collection_id": "c/525611319"})
print(result)