import pymongo

client = pymongo.MongoClient(host="127.0.0.1", port=27017)

db = client.get_database('crawl_tool')

def save(table, data):
    if not db.get_collection(table):
        db.create_collection(table)
    collection = db.get_collection(table)
    collection.insert_one(data)

