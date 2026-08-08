from app.container import ingestion_service


ingestion_service.ingest("data/Company_FAQ.pdf")

print("Ingestion Completed")