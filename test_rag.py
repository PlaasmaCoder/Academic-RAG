from src.rag_chain import answer_question
from src.vector_store import search_chunks


question = "What is retrieval-augmented generation?"
matches = search_chunks(question)
answer = answer_question(question, matches)

print("Answer:")
print(answer)

print("\nSources:")
for match in matches:
    print(f"- {match['source']}, page {match['page']}")
