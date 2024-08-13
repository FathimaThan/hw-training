from bson import ObjectId
import datetime

object_id = ObjectId('66baeab34eb1a717db784c6a')
timestamp = object_id.generation_time

print("ObjectId:", object_id)
print("Timestamp:", timestamp)