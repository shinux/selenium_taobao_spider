import pymongo


client = pymongo.MongoClient("localhost", 27017)

# db
db = client.taobao
# collection
shoe_collection = db.shoes
shop_collection = db.shops


account = ''
password = ''
