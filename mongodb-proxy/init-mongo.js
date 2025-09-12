// MongoDB initialization script for Ansible Discovery
// Creates the ansible database and cache collection with proper indexes

// Switch to the ansible database
db = db.getSiblingDB('ansible');

// Create the cache collection (if it doesn't exist)
db.createCollection('cache');

// Create indexes for better performance
db.cache.createIndex({ "_id": 1 });
db.cache.createIndex({ "date": 1 });

// Create a sample document to test the collection
db.cache.insertOne({
    "_id": "ansible_facts_sample.example.com",
    "data": {
        "ansible_hostname": "sample",
        "ansible_fqdn": "sample.example.com",
        "java_processes": [],
        "apache_processes": [],
        "nginx_processes": []
    },
    "date": new Date()
});

print("Ansible Discovery MongoDB initialized successfully!");
print("- Database: ansible");
print("- Collection: cache");
print("- Indexes created on _id and date");
print("- Sample document inserted");
