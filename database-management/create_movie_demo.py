from sqlmodel import Session

from database import engine
from models import Genre, Movie


def create_movie_with_genre():
    with Session(engine) as session:
        try:
            genre = Genre(name="Sci-Fi")
            session.add(genre)
            session.flush()


            movie = Movie(
                title="Dune, Part Two",
                in_theaters=False,
                release_year=2024,
                genre_id=genre.id
            )

            session.add(movie)
            session.commit()
        except Exception as error:
            session.rollback()


create_movie_with_genre()