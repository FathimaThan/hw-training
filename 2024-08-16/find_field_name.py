from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.practice_database
collection = db.fressnapf

# Get unique field names
fields = set()
for doc in collection.find({}):
    fields.update(doc.keys())

# Print field names
print(list(fields))
