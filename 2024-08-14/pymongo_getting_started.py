from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access a database
db = client['customerapp']
collection = db['users']

# Insert a document
collection.insert_one({'first_name': 'Alice', 'email': 'alice53@gmail.com'})

# Query the document
person = collection.find_one({'first_name': 'Alice'})
print(person)

# Close the connection
client.close()