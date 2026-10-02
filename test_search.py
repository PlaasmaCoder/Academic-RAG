from src.vector_store import search_chunks

for match in search_chunks("What is retrieval-augmented generation?"):
    print(f"Source: {match['source']}, page {match['page']}")
    print(match["text"][:300])
    print()