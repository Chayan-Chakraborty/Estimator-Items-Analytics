from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.constants import APP_ENVIRONMENT
from resources.search_fuzz import search_fuzz as search_fuzz_fuzzy
from services.itemService import (
    fetch_estimator_items,
    fetch_items_from_qdrant_by_identifiers,
    extract_item_name_from_query,
    extract_items_with_identifiers_from_query,
    extract_items_with_identifiers_from_query_fuzzy,
    search_items_by_query,
    add_item_to_items_with_identifiers,
    fetch_estimator_items_vishanti,
    fetch_items_view,
)
from services.ingestVishantiDump import ingest_to_qdrant_vishanti
from services.authService import get_auth_token as auth_get_auth_token
from services.ingestService import ingest_data_to_qdrant, add_items_to_qdrant
app = FastAPI()

# Allow the static frontend (different port) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    query: str


class EstimatorItemBody(BaseModel):
    """Request body for adding an item to Qdrant (matches EstimatorItemDTO)."""
    name: str = ""
    typeIdentifier: str = ""
    identifier: str = ""
    image: str = ""


@app.get("/search-fuzz")
def search_fuzz_endpoint(query: str = ""):
    return search_fuzz_fuzzy(query)

@app.post("/search")
def search(q: Query):
    """
    Legacy search endpoint (deprecated).

    This endpoint is kept for backward compatibility but does not perform actual search.
    Use GET /search-items instead.

    Args:
        q: Query object with query string.

    Returns:
        dict: {"received": "<query>"} - just echoes the query.
    """
    return {"received": q.query}


@app.get("/config")
def get_config():
    """
    Return app configuration including current environment (single source of truth).
    Used by frontend and scripts to read APP_ENVIRONMENT.
    """
    return {"environment": APP_ENVIRONMENT}


@app.get("/fetch-items")
def fetch_items(environment_name: str | None = None):
    """
    Fetch estimator items from external API.

    Uses APP_ENVIRONMENT from constants when environment_name is not provided.

    Example:
        GET /fetch-items
        GET /fetch-items?environment_name=uat
    """
    env = environment_name or APP_ENVIRONMENT
    return fetch_estimator_items(env)


@app.post("/ingest")
async def ingest(environment_name: str | None = None):
    """
    Ingest estimator items from external API into Qdrant database.

    Uses APP_ENVIRONMENT from constants when environment_name is not provided.

    Example:
        POST /ingest
        POST /ingest?environment_name=uat
    """
    env = environment_name or APP_ENVIRONMENT
    ingest_data_to_qdrant(env)
    return await ingest_to_qdrant_vishanti(env)
 

@app.get("/vishanti-items")
def fetch_vishanti_items_from_qdrant():
    """
    Fetch all items from the VISHANTI Qdrant collection.

    Returns:
        list[VishantiItemDTO]: One DTO per point stored in the "vishanti_items" collection.
    """
    return fetch_estimator_items_vishanti()


@app.get("/vishanti-items-view")
def fetch_vishanti_items_view(itemIdentifier: str | None = None):
    """
    Aggregated view of Vishanti items with per-sqft or per-unit price statistics.

    Automatically calculates:
    - Per sqft pricing for WD items (with Measurement)
    - Per unit pricing for LF items (with Quantity)

    Args:
        itemIdentifier: Optional item identifier to filter by. If omitted, aggregates all items.

    Returns:
        list[VishantiAggregatedItemDTO]: One entry per item, each containing:
            - itemName, itemIdentifier, itemTypeIdentifier, image, attributes
            - areaStats: list of { area, priceType, minPrice, maxPrice, avgPrice }
              priceType: "Per Sqft" | "Per Unit" | "Total"
    """
    return fetch_items_view(item_identifier=itemIdentifier)


@app.post("/add-items-to-qdrant")
def add_items_to_qdrant_endpoint(items: list[EstimatorItemBody] | None = None):
    """
    Add one or more estimator items directly to Qdrant collection.

    Unlike /ingest, this endpoint accepts items directly in the request body
    rather than fetching from an external API. Useful for adding custom items
    or updating the database programmatically.

    Args:
        items: List of EstimatorItemBody objects (optional, defaults to empty list).
            Each item should have:
            - name (str): Item name
            - typeIdentifier (str): Type identifier (e.g., "ACS", "FUR")
            - identifier (str): Unique identifier (e.g., "BED_ITM_NW")
            - image (str): Image URL or JSON string

    Returns:
        AddToQdrantResponseDTO: Response with:
            - result.response: ApiResponseMetaDTO (status="SUCCESS", statusCode=200)
            - result.data: List of EstimatorItemDTO that were inserted

    Raises:
        HTTPException: If Qdrant operations fail or collection cannot be created.

    Example:
        POST /add-items-to-qdrant
        Body: [
            {
                "name": "Test Item",
                "typeIdentifier": "TEST",
                "identifier": "TEST_ITM_NW",
                "image": "{}"
            }
        ]
    """
    from utils.dtos import EstimatorItemDTO
    item_list = items if items is not None else []
    dto_list = [
        EstimatorItemDTO(name=i.name, typeIdentifier=i.typeIdentifier,
                         identifier=i.identifier, image=i.image)
        for i in item_list
    ]
    return add_items_to_qdrant(dto_list)


@app.get("/get-auth-token")
def get_auth_token_endpoint(environment_name: str | None = None):
    """
    Fetch authentication token. Uses APP_ENVIRONMENT when environment_name is not provided.
    """
    env = environment_name or APP_ENVIRONMENT
    return {"access_token": auth_get_auth_token(env)}


@app.get("/extract-item")
def extract_item_endpoint(query: str = ""):
    """
    Extract a single canonical item name from a search query.

    Uses multilingual synonym matching to find the canonical English item name
    that matches the query. Supports queries in Hindi, Bengali, Tamil, Telugu,
    Kannada, Malayalam, or English.

    Returns only the first match (single item name), unlike /extract-items-with-identifiers
    which returns all matches.

    Args:
        query: Search query string. Can be in any supported language or English.
            Examples: "bed", "बिस्तर" (Hindi), "বিছানা" (Bengali)

    Returns:
        dict: {"itemName": "<canonical_name>"} if match found, {"itemName": null} if not.

    Example:
        GET /extract-item?query=bed
        Response: {"itemName": "bed"}

        GET /extract-item?query=बिस्तर
        Response: {"itemName": "bed"}

        GET /extract-item?query=xyz123
        Response: {"itemName": null}
    """
    result = extract_item_name_from_query(query)
    return {"itemName": result}


@app.get("/extract-items-with-identifiers")
def extract_items_with_identifiers_endpoint(query: str = ""):
    """
    Extract all matching item names from a query with their identifiers.

    Uses exact matching (no fuzzy matching) to find all items that match the query.
    Supports multilingual queries and returns all matches with their associated
    identifiers from items_with_identifiers.json.

    Matching behavior:
    - Single word (e.g., "table"): Returns all items containing that word
    - Multi-word phrase (e.g., "study table"): Returns only exact phrase match if found
    - Comma-separated (e.g., "bed, cot"): Returns items matching any term

    Args:
        query: Search query string. Can contain multiple terms separated by commas or spaces.
            Examples: "bed", "study table", "bed, cot", "स्टडी टेबल"

    Returns:
        ExtractItemsWithIdentifiersResponseDTO: Response with data list containing:
            - itemName: Canonical item name (e.g., "bed", "study table")
            - identifiers: List of identifier strings (e.g., ["BED_ITM_NW"])

    Example:
        GET /extract-items-with-identifiers?query=table
        Response: {
            "data": [
                {"itemName": "console table", "identifiers": ["COT_ITM_NW"]},
                {"itemName": "centre table", "identifiers": ["CEN_ITM_NW"]},
                {"itemName": "study table", "identifiers": ["STT_ITM_NW"]}
            ]
        }
    """
    return extract_items_with_identifiers_from_query(query)


@app.get("/extract-items-with-identifiers-fuzzy")
def extract_items_with_identifiers_fuzzy_endpoint(query: str = "", fuzzy_cutoff: float = 0.75):
    """
    Extract matching item names with identifiers using fuzzy matching for typos.

    Same as /extract-items-with-identifiers, but adds fuzzy matching using difflib
    to handle typos and similar spellings. For example, "bichana" (typo) will match
    "bichhana" (correct) and return "bed".

    Matching strategy:
    1. First tries exact matching
    2. If no exact match, applies fuzzy matching with the specified cutoff
    3. For multi-word queries: if phrase matches exactly, returns only that phrase
    4. For single-word queries: returns all items containing that word (exact + fuzzy)

    Args:
        query: Search query string (can contain typos).
            Examples: "bed", "bichana" (typo), "study tabel" (typo)
        fuzzy_cutoff: Similarity threshold for fuzzy matching (0.0-1.0, default 0.75).
            - 0.75: Moderate strictness, catches common typos
            - Higher (0.8-0.9): Stricter, fewer false positives
            - Lower (0.6-0.7): More lenient, more matches but more false positives

    Returns:
        ExtractItemsWithIdentifiersResponseDTO: Response with data list containing:
            - itemName: Canonical item name
            - identifiers: List of identifier strings

    Example:
        GET /extract-items-with-identifiers-fuzzy?query=bichana&fuzzy_cutoff=0.75
        Response: {
            "data": [
                {"itemName": "bed", "identifiers": ["BED_ITM_NW"]}
            ]
        }
    """
    return extract_items_with_identifiers_from_query_fuzzy(query, fuzzy_cutoff=fuzzy_cutoff)


@app.get("/items-by-identifiers")
def items_by_identifiers_endpoint(identifiers: str = ""):
    """
    Fetch estimator items from Qdrant database by their identifiers.

    Queries the Qdrant collection to find all items whose "identifier" field
    matches any value in the provided comma-separated list. Returns full item
    details including name, typeIdentifier, identifier, and image.

    Args:
        identifiers: Comma-separated list of identifier strings.
            Examples: "BED_ITM_NW", "BED_ITM_NW,SOF_ITM_NW"
            Empty string returns empty result.

    Returns:
        EstimatorResponseDTO: Response containing:
            - result.response: ApiResponseMetaDTO (status="SUCCESS", statusCode=200, etc.)
            - result.data: List of EstimatorItemDTO (name, typeIdentifier, identifier, image)

    Raises:
        HTTPException: If Qdrant query fails (connection error, collection not found).

    Example:
        GET /items-by-identifiers?identifiers=BED_ITM_NW,SOF_ITM_NW
        Response: {
            "result": {
                "response": {"status": "SUCCESS", "statusCode": 200, ...},
                "data": [
                    {"name": "Bed", "typeIdentifier": "...", "identifier": "BED_ITM_NW", "image": "..."},
                    {"name": "Sofa Set", "typeIdentifier": "...", "identifier": "SOF_ITM_NW", "image": "..."}
                ]
            }
        }
    """
    id_list = [i.strip() for i in identifiers.split(
        ",") if i.strip()] if identifiers else []
    return fetch_items_from_qdrant_by_identifiers(id_list)


@app.get("/search-items")
def search_items_endpoint(query: str = ""):
    """
    Main search endpoint: search for items by query and return from Qdrant.

    Complete search workflow:
    1. Extracts item names and identifiers from query using fuzzy matching
       (handles typos like "bichana" -> "bichhana" -> "bed")
    2. Collects all unique identifiers from matched items
    3. Fetches actual item data from Qdrant by those identifiers
    4. Returns items in EstimatorResponseDTO format

    This is the primary endpoint used by the frontend search UI. It combines
    multilingual query extraction with Qdrant database lookup.

    Args:
        query: Search query string. Can be in any supported language (Hindi, Bengali,
            Tamil, Telugu, Kannada, Malayalam) or English. Supports typos via fuzzy matching.
            Examples: "bed", "sofa set", "bichana" (typo), "स्टडी टेबल"

    Returns:
        EstimatorResponseDTO: Response containing:
            - result.response: ApiResponseMetaDTO (status="SUCCESS", statusCode=200)
            - result.data: List of EstimatorItemDTO matching the query
                Each item has: name, typeIdentifier, identifier, image

    Raises:
        HTTPException: If Qdrant query fails or extraction fails.

    Example:
        GET /search-items?query=bed
        Response: {
            "result": {
                "response": {"status": "SUCCESS", "statusCode": 200, ...},
                "data": [
                    {"name": "Bed", "typeIdentifier": "...", "identifier": "BED_ITM_NW", "image": "..."}
                ]
            }
        }

        GET /search-items?query=bichana  # typo still works
        Response: {
            "result": {
                "response": {"status": "SUCCESS", ...},
                "data": [{"name": "Bed", ...}]  # finds "bed" despite typo
            }
        }
    """
    return search_items_by_query(query)


@app.post("/items-with-identifiers")
def write_item_to_items_with_identifiers_endpoint(body: dict):
    """
    Add or update an item in resources/items_with_identifiers.json.

    Writes a new item entry or updates an existing one in the items_with_identifiers.json
    file. This file is used by the extractor to map queries to item identifiers.
    After writing, invalidates in-memory caches so the next request reloads the file.

    Args:
        body: JSON object containing:
            - itemName (str, required): The canonical item name (used as JSON key)
            - Language entries (optional): hindi, bengali, tamil, telugu, kannada, malayalam
              Each language entry should have: {"native": "...", "roman": "..."}
            - identifiers (list[str], optional): List of identifier strings

    Returns:
        dict: {"ok": True, "itemName": "<item_name>"} on success.

    Raises:
        HTTPException (400): If itemName is missing or empty (ValueError).
        HTTPException (500): If file cannot be read or written (IOError).

    Example:
        POST /items-with-identifiers
        Body: {
            "itemName": "book shelf",
            "hindi": {"native": "बुक शेल्फ", "roman": "buk shelf"},
            "bengali": {"native": "বুক শেল্ফ", "roman": "buk shelph"},
            "tamil": {"native": "புத்தக அலமாரி", "roman": "puththaka alamari"},
            "telugu": {"native": "పుస్తకాల షెల్ఫ్", "roman": "pustakala shelf"},
            "kannada": {"native": "ಪುಸ್ತಕದ ಕಪಾಟು", "roman": "pustakada kapatu"},
            "malayalam": {"native": "പുസ്തക ഷെൽഫ്", "roman": "pustaka shelf"},
            "identifiers": ["BOK_ITM_NW"]
        }
        Response: {"ok": True, "itemName": "book shelf"}
    """
    try:
        return add_item_to_items_with_identifiers(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
