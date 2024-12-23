# Fetches movie data (titles, posters, details) from OMDB API.
import requests

API_KEY = "c925d41e"
BASE_URL = "http://www.omdbapi.com/"

def fetch_movie_data(title):
    """
    Fetch movie details from the OMDb API based on the title.
    :param title: Movie title to search for.
    :return: Dictionary with movie data or an error message.
    """
    try:
        response = requests.get(BASE_URL, params={"apikey": API_KEY, "t": title})
        data = response.json()
        
        if data.get("Response") == "True":
            return {
                "title": data.get("Title"),
                "year": data.get("Year"),
                "genre": data.get("Genre"),
                "director": data.get("Director"),
                "actors": data.get("Actors"),
                "plot": data.get("Plot"),
                "poster": data.get("Poster"),
                "imdb_rating": data.get("imdbRating")
            }
        else:
            return {"error": data.get("Error")}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example (to test):
if __name__ == "__main__":
    movie = input("Enter a movie title: ")
    result = fetch_movie_data(movie)
    print(result)
