"""
Grafana Data Source for Ansible Discovery
"""
import json
import os
from datetime import datetime
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.response import json as sanic_json
from motor.motor_asyncio import AsyncIOMotorClient

app = Sanic("mongodb-proxy")

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
ANSIBLE_DB = os.getenv('ANSIBLE_DB', 'ansible')
CACHE_COLLECTION = os.getenv('CACHE_COLLECTION', 'cache')
WORKERS = int(os.getenv('WORKERS', '4'))

mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client[ANSIBLE_DB]
cache_collection = mongo_db[CACHE_COLLECTION]


@app.post('/search')
async def search(request) -> HTTPResponse:
    """Return list of server hostnames from cache collection"""
    data = request.json or {}
    collection_name = data.get('collection', CACHE_COLLECTION)

    # Get the specified collection
    collection = mongo_db[collection_name]
    cursor = collection.find({}, {"_id": 1})
    hostnames = [
        doc["_id"].replace("ansible_facts", "")
        async for doc in cursor
    ]
    return sanic_json(hostnames)


@app.get('/annotations')
async def annotations(request) -> HTTPResponse:
    return sanic_json([])


@app.get('/healthz')
async def healthz(request) -> HTTPResponse:
    """Health check endpoint for Kubernetes/container orchestration"""
    try:
        # Test MongoDB connection
        await cache_collection.find_one({}, {"_id": 1})
        return sanic_json({
            "status": "healthy",
            "service": "mongodb-proxy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return sanic_json({
            "status": "unhealthy",
            "service": "mongodb-proxy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=503)


@app.post('/query')
async def query(request: Request) -> HTTPResponse:
    """Query MongoDB cache collection with aggregation pipeline for Grafana"""
    data = request.json
    pipeline = data.get('pipeline', [])
    time_range = data.get('range', {})
    collection_name = data.get('collection', CACHE_COLLECTION)

    # Get the specified collection
    collection = mongo_db[collection_name]

    # Add time range filter if provided
    if time_range.get('from') and time_range.get('to'):
        _from = datetime.fromtimestamp(int(time_range['from']) / 1000)
        _to = datetime.fromtimestamp(int(time_range['to']) / 1000)

        match_filter = {"date": {"$gte": _from, "$lt": _to}}

        # Add or merge with existing $match stage
        if pipeline and '$match' in pipeline[0]:
            pipeline[0]['$match'].update(match_filter)
        else:
            pipeline.insert(0, {"$match": match_filter})

    # Execute aggregation pipeline
    cursor = collection.aggregate(pipeline)

    # Custom JSON encoder for datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super(DateTimeEncoder, self).default(obj)

    # Collect results
    response = [doc async for doc in cursor]

    return sanic_json(
        response,
        dumps=lambda obj: json.dumps(obj, cls=DateTimeEncoder)
    )


@app.post('/host')
async def host(request: Request) -> HTTPResponse:
    """Query single document and return pretty formatted JSON"""
    data = request.json
    host_id = data.get('host_id', '')
    collection_name = data.get('collection', CACHE_COLLECTION)

    # Get the specified collection
    collection = mongo_db[collection_name]

    if not host_id:
        return HTTPResponse('{"error": "host_id required"}', content_type="application/json")

    # Find specific document
    document = await collection.find_one({"_id": host_id})

    if not document:
        return HTTPResponse('{"error": "Host not found"}', content_type="application/json")

    # Custom JSON encoder for datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super(DateTimeEncoder, self).default(obj)

    # Pretty print JSON with indentation
    pretty_json = json.dumps(document, cls=DateTimeEncoder, indent=2, ensure_ascii=False)

    return HTTPResponse(pretty_json, content_type="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, workers=WORKERS)
