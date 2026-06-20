db.createCollection("support_db", { collation: { locale: "en" } });
db.createCollection("users");
db.createCollection("complaints");
db.createCollection("complaint_comments");
db.createCollection("audit_logs");

db.complaints.createIndex({ "partner_id": 1, "status": 1 });
db.complaints.createIndex({ "assigned_to": 1 });
db.complaints.createIndex({ "created_at": -1 });
db.complaints.createIndex({ "sla_due_date": 1 });

print("MongoDB initialized with collections and indexes");
