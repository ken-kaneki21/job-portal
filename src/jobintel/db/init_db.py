import jobintel.db.models  # noqa: F401
from jobintel.db.base import Base
from jobintel.db.session import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()
