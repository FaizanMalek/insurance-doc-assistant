"""M1 + M2: read PDFs from data/, chunk, embed, and upload to Azure AI Search.
Run once after you add PDFs:  python ingest/build_index.py
"""
import os, sys, glob, uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pypdf import PdfReader
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField,
    VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration,
)
import config


def read_chunks(path):
    """Yield (text, page) chunks of ~CHUNK_WORDS words with overlap."""
    reader = PdfReader(path)
    for pageno, page in enumerate(reader.pages, start=1):
        words = (page.extract_text() or "").split()
        step = max(1, config.CHUNK_WORDS - config.CHUNK_OVERLAP)
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + config.CHUNK_WORDS]).strip()
            if len(chunk) > 40:
                yield chunk, pageno


def ensure_index(index_client):
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="page", type=SearchFieldDataType.Int32),
        SearchField(name="vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=config.EMBED_DIM,
                    vector_search_profile_name="hnsw-profile"),
    ]
    vs = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")],
    )
    index_client.create_or_update_index(
        SearchIndex(name=config.SEARCH_INDEX, fields=fields, vector_search=vs))
    print(f"index '{config.SEARCH_INDEX}' ready")


def main():
    cred = AzureKeyCredential(config.SEARCH_KEY)
    ensure_index(SearchIndexClient(config.SEARCH_ENDPOINT, cred))
    search = SearchClient(config.SEARCH_ENDPOINT, config.SEARCH_INDEX, cred)

    pdfs = glob.glob("data/*.pdf")
    if not pdfs:
        print("No PDFs in data/. Add some public sample PDFs and rerun.")
        return

    batch, texts, meta = [], [], []
    for path in pdfs:
        name = os.path.basename(path)
        for text, page in read_chunks(path):
            texts.append(text); meta.append((name, page))
    print(f"embedding {len(texts)} chunks from {len(pdfs)} files...")

    for i in range(0, len(texts), 64):  # embed + upload in batches
        vecs = config.embed(texts[i:i + 64])
        for (t, (src, pg)), v in zip(zip(texts[i:i + 64], meta[i:i + 64]), vecs):
            batch.append({"id": str(uuid.uuid4()), "content": t,
                          "source": src, "page": pg, "vector": v})
        search.upload_documents(batch); batch = []
    print("done. index populated.")


if __name__ == "__main__":
    main()
