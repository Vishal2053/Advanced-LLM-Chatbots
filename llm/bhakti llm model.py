from langchain.llms import Ollama
ollama=Ollama(base_url='http://localhost:11434', model="bhakti2.0")
print(ollama("hey how are you"))