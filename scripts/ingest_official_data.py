from src.core.seed import seed_data


def ingest():
    print("Ingesting official data and initializing baseline seed...")
    seed_data(reset=True)
    print("Ingestion completed successfully.")


if __name__ == "__main__":
    ingest()

