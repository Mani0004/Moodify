from database import db
print("Connection successful!")
print(f"Database: {db.db.name}")
print(f"Collections: {db.db.list_collection_names()}")