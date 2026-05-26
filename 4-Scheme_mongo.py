import random
from pymongo import MongoClient


#1.connection
client = MongoClient("mongodb://localhost:27017/")
db = client["mobility_platform"]

#2. Writing query
def add_battery_value():
    # 1.finding the documents/collections which do not have field"battery_value
    query = {"battery_value": {"$exists": False}}
    
    #2.get id of enets table which it is in the query, means not False
    events_to_fix = db.events.find(query, {"_id": 1})  

    updates = []
    count = 0
    for event in events_to_fix:
        #3.Greating the random value for input in the battery_value field.
         new_value = random.randint(0, 100)  
         db.events.update_one({"_id": event["_id"]}, {"$set": {"battery_value": new_value}})
         count += 1
    if count % 1000 == 0:
        print(f"so far{count} is updated..")

add_battery_value()
        
   