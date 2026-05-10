from sqlalchemy import create_engine, text
import os

url = (
    f"postgresql+psycopg2://{os.getenv('PG_USER','postgres')}:"
    f"{os.getenv('PG_PASSWORD','kj224')}"
    f"@{os.getenv('PG_HOST','localhost')}:"
    f"{os.getenv('PG_PORT','5432')}/"
    f"{os.getenv('PG_DB','patents')}"
)

engine = create_engine(url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())