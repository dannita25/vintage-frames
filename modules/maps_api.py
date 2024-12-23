# Integrates MapTiler API for location functionalities.
import requests

# API Configuration
API_KEY = "uCDHSx9f8AKzn5Tfdf9F"
BASE_URL = "https://api.maptiler.com/geocoding/{address}.json"

def fetch_coordinates(address):
    """
    Fetch latitude and longitude for a given address using MapTiler API.
    :param address: Address to geocode.
    :return: Dictionary with latitude, longitude, or an error message.
    """
    try:
        # Format the request URL
        url = BASE_URL.format(address=address)
        response = requests.get(url, params={"key": API_KEY})
        data = response.json()
        
        # Check valid results
        if "features" in data and len(data["features"]) > 0:
            # Extract latitude and longitude from first result
            coordinates = data["features"][0]["geometry"]["coordinates"]
            return {
                "latitude": coordinates[1],  # Latitude
                "longitude": coordinates[0]  # Longitude
            }
        else:
            return {"error": "No results found for the given address."}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example for testing
if __name__ == "__main__":
    address = input("Enter an address: ")
    result = fetch_coordinates(address)
    print(result)

