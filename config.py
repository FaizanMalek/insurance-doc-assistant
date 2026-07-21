"""Central config + a tiny provider adapter.

PROVIDER=azure  -> Microsoft Foundry (new v1 endpoint). Uses the OpenAI client
                   pointed at your project's base_url, exactly like the
                   "Call this model" snippet in the Foundry portal.
PROVIDER=openai -> plain OpenAI API fallback (same code, different base_url).
"""
import os
from dotenv import load_dotenv
load_dotenv()

PROVIDER = os.getenv("PROVIDER", "azure").lower()
TOP_K = int(os.getenv("TOP_K", "5"))
CHUNK_WORDS = int(os.getenv("CHUNK_WORDS", "400"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "60"))
EMBED_DIM = int(os.getenv("EMBED_DIM", "1536"))

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "policies")


def _clients():
    """Return (client, chat_model, embed_model)."""
    from openai import OpenAI
    if PROVIDER == "azure":
        # AZURE_OPENAI_ENDPOINT = the base_url from Foundry's "Call this model"
        # snippet, e.g. https://faizan-foundry.services.ai.azure.com/openai/v1
        client = OpenAI(
            base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
        )
        return client, os.getenv("AZURE_CHAT_DEPLOYMENT"), os.getenv("AZURE_EMBED_DEPLOYMENT")
    else:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        return client, os.getenv("OPENAI_CHAT_MODEL"), os.getenv("OPENAI_EMBED_MODEL")


_client, CHAT_MODEL, EMBED_MODEL = _clients()


def embed(texts):
    resp = _client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def chat(system, user, temperature=1):
    # NOTE: gpt-5 family only accepts the default temperature (1). If you switch
    # to a model that allows it, you can lower this for more deterministic output.
    resp = _client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=temperature,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content
