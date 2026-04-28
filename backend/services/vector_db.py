import logging
# Reserved for future semantic layer - DISABLED FOR HYBRID MVP
# from google.cloud import aiplatform
from core.config import settings
import uuid

logger = logging.getLogger(__name__)

_index_endpoint = None

def get_index_endpoint():
    """
    Initializes and returns the Vertex AI MatchingEngineIndexEndpoint client.
    """
    global _index_endpoint
    if _index_endpoint is None:
        try:
            project_id = settings.GCP_PROJECT_ID or settings.GOOGLE_PROJECT_ID
            location = settings.VERTEX_AI_LOCATION
            endpoint_id = settings.VERTEX_AI_INDEX_ENDPOINT_ID
            
            if not project_id or not endpoint_id:
                logger.warning("Vertex AI credentials/config not fully set. Returning None.")
                return None
                
            aiplatform.init(project=project_id, location=location)
            
            _index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=endpoint_id
            )
            logger.info(f"Vertex AI Index Endpoint {endpoint_id} initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {e}")
            raise
    return _index_endpoint

def insert_embedding(vector: list[float], asset_id: str, metadata: dict = None) -> None:
    """
    Inserts a newly generated CLIP embedding into Vertex AI Vector Search.
    
    Args:
        vector: The 512-dimensional embedding
        asset_id: The unique ID linking to Firestore
        metadata: Optional metadata dict to store alongside the vector
    """
    endpoint = get_index_endpoint()
    if endpoint is None:
        return
        
    try:
        # Vertex AI Vector Search allows upserting datapoints
        # Restricts string id to 128 characters
        datapoint_id = str(asset_id)
        
        # Prepare restricts/metadata if supported by your index schema
        # In a generic setup, you might only insert the vector. 
        # Metadata filtering requires specific schema setup in Vertex AI.
        datapoint = aiplatform.matching_engine.matching_engine_index_endpoint.Namespace(
            name="default", allow_tokens=["metadata"]
        )
        
        endpoint.upsert_datapoints(
            deployed_index_id=settings.VERTEX_AI_DEPLOYED_INDEX_ID,
            datapoints=[{
                "datapoint_id": datapoint_id,
                "feature_vector": vector,
            }]
        )
        logger.info(f"Inserted embedding for {asset_id} into Vertex AI Vector Search.")
    except Exception as e:
        logger.error(f"Error inserting embedding for {asset_id}: {e}")
        raise

def query_similar(vector: list[float], top_k: int = 5) -> list[dict]:
    """
    Queries Vertex AI Vector Search for the closest matching vectors.
    
    Args:
        vector: The query embedding to search for
        top_k: The number of closest matches to return
    
    Returns:
        List of matched results with distance scores and metadata
    """
    endpoint = get_index_endpoint()
    if endpoint is None:
        return []
        
    try:
        response = endpoint.match(
            deployed_index_id=settings.VERTEX_AI_DEPLOYED_INDEX_ID,
            queries=[vector],
            num_neighbors=top_k
        )
        
        results = []
        if response and len(response) > 0:
            for neighbor in response[0]:
                results.append({
                    "id": neighbor.id,
                    "score": neighbor.distance,
                    "metadata": {}  # Metadata retrieval depends on Firestore in this architecture
                })
        return results
    except Exception as e:
        logger.error(f"Error querying similar vectors from Vertex AI: {e}")
        raise
