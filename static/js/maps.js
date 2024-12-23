// Function to show a selected location on the map
// Initialize the map
function initMap(_apiKey) {
    var map = new maplibregl.Map({
        container: 'mapContainer', // ID of the map container
        style: `https://api.maptiler.com/maps/streets-v2/style.json?key=uCDHSx9f8AKzn5Tfdf9F`,
        center: [-3.1883, 55.9533], // Default center: Edinburgh
        zoom: 14
    });

    window.Map = map; // Store map globally for access in other functions

    // Once the map loaded, add cinema markers
    map.on('load', () => {
        addCinemaMarkers();
    });
    console.log("Map initialized.");
}

// Add cinema markers
function addCinemaMarkers() {
    const cinemas = window.cinemas || [];
    cinemas.forEach(cinema => {
        const position = [cinema.longitude, cinema.latitude];

        new maplibregl.Marker({ color: 'red' }) // Red markers for cinemas
            .setLngLat(position)
            .setPopup(new maplibregl.Popup().setText(cinema.name)) // Popup with cinema name
            .addTo(window.Map);
    });

    console.log("Cinema markers added.");
}

function showOnMap(element) {
    var lat = parseFloat(element.getAttribute('data-lat'));
    var lng = parseFloat(element.getAttribute('data-lng'));

    if (isNaN(lat) || isNaN(lng)) {
        throw new Error("Invalid latitude or longitude");
    }

    var position = [lng, lat];

    var popup = new maplibregl.Popup().setText(element.querySelector('h5').textContent); // Add popup

    var marker = new maplibregl.Marker()
        .setLngLat(position)
        .setPopup(popup)
        .addTo(window.Map);
    
    window.Map.flyTo({ center: position, zoom: 16 });

    console.log("Marker and FlyTo executed"); // Debug confirmation
}

// Initialize the map on page load
if (document.getElementById('mapContainer')) {
    initMap("uCDHSx9f8AKzn5Tfdf9F");
}

// Expose showOnMap globally for HTML usage
window.showOnMap = showOnMap;
