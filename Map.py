import streamlit as st
from neo4j import GraphDatabase
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import random

# Neo4j Memory Agent
class MemoryAgent:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="achu1234"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def store_user_preference(self, user_id, preferences):
        with self.driver.session() as session:
            for key, value in preferences.items():
                session.run(
                    "MERGE (u:User {id: $user_id}) "
                    "SET u[$key] = $value",
                    user_id=user_id,
                    key=key,
                    value=value
                )

    def get_user_preference(self, user_id, key):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {id: $user_id}) RETURN u[$key] AS value",
                user_id=user_id,
                key=key
            )
            return result.single()["value"]

# Itinerary Generator
class ItineraryGenerator:
    def __init__(self):
        self.places_data = {
            "Rome": {
                "Culture": ["Colosseum", "Roman Forum", "Pantheon", "Vatican Museums", "Castel Sant'Angelo"],
                "Food": ["Piazza Navona", "Trastevere", "Campo de' Fiori", "Pizza at Pizzeria da Baffetto", "Gelato at Giolitti"],
                "Shopping": ["Via del Corso", "Spanish Steps", "Via dei Condotti", "Porta Portese Market", "Galleria Alberto Sordi"],
                "Adventure": ["Vatican Gardens", "Appian Way", "Borghese Gallery Gardens", "Tiber River Cruise", "Villa D'Este Gardens"]
            },
            "Paris": {
                "Culture": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Musée d'Orsay", "Montmartre"],
                "Food": ["Le Marais", "Saint-Germain", "Le Procope", "Marché des Enfants Rouges", "Crepes at Breizh Café"],
                "Shopping": ["Champs-Élysées", "Galeries Lafayette", "Le Bon Marché", "Rue Saint-Honoré", "Montmartre Flea Market"],
                "Adventure": ["Seine River Cruise", "Jardin des Tuileries", "Versailles Palace", "Luxembourg Gardens", "Parc des Buttes-Chaumont"]
            },
            "London": {
                "Culture": ["British Museum", "Buckingham Palace", "Tower of London", "Natural History Museum", "Westminster Abbey"],
                "Food": ["Borough Market", "Camden Market", "Chinatown", "Covent Garden", "Duck & Waffle"],
                "Shopping": ["Oxford Street", "Covent Garden", "King's Road", "Carnaby Street", "Liberty"],
                "Adventure": ["London Eye", "Hyde Park", "Greenwich Park", "Richmond Park", "Hampstead Heath"]
            },
            "New York": {
                "Culture": ["Statue of Liberty", "Metropolitan Museum of Art", "Broadway", "The Museum of Modern Art", "The Guggenheim Museum"],
                "Food": ["Chinatown", "Little Italy", "Katz's Delicatessen", "Eataly", "Smorgasburg"],
                "Shopping": ["Fifth Avenue", "Times Square", "SoHo", "Brookfield Place", "Macy's Herald Square"],
                "Adventure": ["Central Park", "Brooklyn Bridge", "High Line", "Coney Island", "Rockefeller Center"]
            },
            "Istanbul":{
                "Culture": ["Petronas Towers", "Batu Caves", "Merdeka Square", "Sultan Abdul Samad Building", "National Mosque"],
                "Food": ["Jalan Alor", "Central Market", "Little India", "Chinatown", "Hawker Stalls"],
                "Shopping": ["Pavilion Mall", "Bukit Bintang", "Suria KLCC", "Central Market", "Times Square"],
                "Adventure": ["Batu Caves", "KL Bird Park", "KL Forest Eco Park", "Sunway Lagoon", "Taman Negara National Park"]
            },
            "Delhi": {
                "Culture": ["Red Fort", "Qutub Minar", "India Gate", "Humayun's Tomb", "Lotus Temple"],
                "Food": ["Chandni Chowk", "Connaught Place", "Karol Bagh", "Paranthe Wali Gali", "Bikanervala"],
                "Shopping": ["Dilli Haat", "Janpath Market", "Chandni Chowk", "Lajpat Nagar", "Khan Market"],
                "Adventure": ["Yamuna River Cruise", "Sanjay Van", "Garden of Five Senses", "Sultanpur Bird Sanctuary", "Ridge Road"]
            },
            "Mumbai": {
                "Culture": ["Gateway of India", "Chhatrapati Shivaji Maharaj Terminus", "Elephanta Caves", "Haji Ali Dargah", "Chor Bazaar"],
                "Food": ["Vada Pav at Ashok Vadapav", "Bhel Puri at Girgaon Chowpatty", "Pav Bhaji at Sardar Pav Bhaji", "Colaba Café", "Theobroma"],
                "Shopping": ["Colaba Causeway", "Zaveri Bazaar", "Fashion Street", "High Street Phoenix", "Linking Road"],
                "Adventure": ["Marine Drive", "Elephanta Island", "Juhu Beach", "Versova Beach", "Worli Sea Face"]
            },
            "Bangalore": {
                "Culture": ["Bangalore Palace", "Cubbon Park", "Tipu Sultan's Summer Palace", "Vidhana Soudha", "St. Mary's Basilica"],
                "Food": ["MTR", "Vidyarthi Bhavan", "Koshy’s", "Shivaji Military Hotel", "Brahmin’s Coffee Bar"],
                "Shopping": ["MG Road", "Commercial Street", "Brigade Road", "UB City Mall", "Chickpet"],
                "Adventure": ["Nandi Hills", "Bannerghatta National Park", "Cubbon Park", "Lalbagh Botanical Garden", "Ramanagaram"]
            },
            "Kochi": {
                "Culture": ["Fort Kochi", "Chinese Fishing Nets", "Mattancherry Palace", "Paradesi Synagogue", "St. Francis Church"],
                "Food": ["Seafood at Mattancherry", "Kochi Kitchen", "Saravana Bhavan", "Sree Krishna Cafe", "Kashi Art Cafe"],
                "Shopping": ["MG Road", "Jew Town", "Broadway", "Lulu Mall", "Kochi Biennale Art Shop"],
                "Adventure": ["Alleppey Backwaters", "Vypin Island", "Munambam Beach", "Athirappilly Waterfalls", "Mangalavanam Bird Sanctuary"]
            },
            "Kolkata": {
                "Culture": ["Victoria Memorial", "Howrah Bridge", "Indian Museum", "Marble Palace", "Kalighat Temple"],
                "Food": ["Kathi Rolls", "Macher Jhol", "Pakhala Bhata", "Rosogolla", "Mishti Doi"],
                "Shopping": ["New Market", "South City Mall", "Park Street", "Gariahat Market", "Forum Mall"],
                "Adventure": ["Sundarbans", "Eco Tourism Park", "Dakshineswar Kali Temple", "Alambazar", "Bengal Safari Park"]
            },
            "Chennai": {
                "Culture": ["Marina Beach", "Kapaleeshwarar Temple", "Fort St. George", "Vivekananda House", "San Thome Basilica"],
                "Food": ["Dosa at Murugan Idli Shop", "Chettinad Cuisine", "Kothu Parotta", "Filter Coffee at Ratna Café", "Biryani at Buhari"],
                "Shopping": ["T Nagar", "Express Avenue Mall", "Pondy Bazaar", "Chennai Citi Centre", "Ranganathan Street"],
                "Adventure": ["Muttukadu Boat House", "Guindy National Park", "Pulicat Lake", "Covelong Beach", "Dakshinachitra"]
            },
            "Beijing": {
    "Culture": ["Great Wall of China", "Forbidden City", "Temple of Heaven", "Tiananmen Square", "Summer Palace"],
    "Food": ["Peking Duck", "Wangfujing Street", "Jianbing", "Baozi", "Hotpot"],
    "Shopping": ["Wangfujing Street", "Silk Market", "Yashow Market", "Lama Temple", "Sanlitun"],
    "Adventure": ["Hiking the Great Wall", "Beijing Olympic Park", "Jingshan Park", "Badaling", "Mutianyu"]
            },
            "Moscow": {
    "Culture": ["Red Square", "Kremlin", "St. Basil's Cathedral", "The Bolshoi Theatre", "Pushkin Museum"],
    "Food": ["Borscht", "Pelmeni", "Blini", "Shashlik", "Kvass"],
    "Shopping": ["GUM", "Arbat Street", "Tsvetnoy Central Market", "Izmailovsky Market", "Moscow Mall"],
    "Adventure": ["Gorky Central Park", "Kolomenskoye", "Sparrow Hills", "Izmailovo Park", "Moscow River Cruise"]
            },
            "Berlin": {
    "Culture": ["Brandenburg Gate", "Berlin Wall", "Museum Island", "Reichstag Building", "Charlottenburg Palace"],
    "Food": ["Currywurst", "Berliner Donut", "Kebab at Mustafa's", "Schnitzel", "German Beer"],
    "Shopping": ["Kurfürstendamm", "Mitte", "KaDeWe", "Hackescher Markt", "East Side Mall"],
    "Adventure": ["Tiergarten", "Tempelhofer Feld", "Berlin Zoo", "Spree River Cruise", "Müggelsee"]
            },
            "Madrid": {
    "Culture": ["Prado Museum", "Royal Palace of Madrid", "Retiro Park", "Puerta del Sol", "Alcázar of Segovia"],
    "Food": ["Tapas", "Paella", "Churros", "Cochinillo", "Patatas Bravas"],
    "Shopping": ["Gran Via", "El Rastro", "Santiago Bernabéu", "Plaza Mayor", "Salamanca District"],
    "Adventure": ["Sierra de Guadarrama", "Retiro Park Boat Ride", "Madrid Rio", "Casa de Campo", "Parque de la Vaguada"]
            },
            "Barcelona": {
    "Culture": ["Sagrada Familia", "Park Güell", "Casa Batlló", "La Rambla", "Gothic Quarter"],
    "Food": ["Paella", "Tapas", "Patatas Bravas", "Crema Catalana", "Churros"],
    "Shopping": ["Passeig de Gràcia", "La Boqueria", "El Raval", "El Born", "Avinguda Diagonal"],
    "Adventure": ["Montjuïc", "Barceloneta Beach", "Bunkers del Carmel", "Tibidabo", "Collserola Park"]
            },
            "Vienna": {
    "Culture": ["Schönbrunn Palace", "Hofburg Palace", "St. Stephen's Cathedral", "Belvedere Palace", "Kunsthistorisches Museum"],
    "Food": ["Wiener Schnitzel", "Sachertorte", "Apfelstrudel", "Kaiserschmarrn", "Strudel"],
    "Shopping": ["Graben", "Mariahilfer Strasse", "Kärntnertorstraße", "Naschmarkt", "Ringstrasse"],
    "Adventure": ["Prater Park", "Donauinsel", "Stephansdom Tower", "Danube River Cruise", "Lainzer Tiergarten"]
            },
            "Los Angeles": {
    "Culture": ["Hollywood Sign", "Getty Museum", "Santa Monica Pier", "Universal Studios", "Griffith Observatory"],
    "Food": ["In-N-Out Burger", "Mexican Tacos", "Korean BBQ", "Pink's Hot Dogs", "Donuts at Randy's"],
    "Shopping": ["Rodeo Drive", "Melrose Avenue", "The Grove", "Venice Beach Boardwalk", "Westfield Century City"],
    "Adventure": ["Runyon Canyon", "Santa Monica Beach", "Venice Beach", "Griffith Park", "Malibu"]
            },
            "Washington": {
    "Culture": ["White House", "Lincoln Memorial", "Washington Monument", "Smithsonian Museums", "U.S. Capitol"],
    "Food": ["Half-Smoke", "Ben's Chili Bowl", "Georgetown Cupcake", "Crab Cakes", "Old Ebbitt Grill"],
    "Shopping": ["Georgetown", "Union Station", "M Street", "Farragut Square", "CityCenterDC"],
    "Adventure": ["National Mall", "Rock Creek Park", "Tidal Basin", "Potomac River Cruise", "Great Falls Park"]
            },
            "Buenos Aires": {
    "Culture": ["La Boca", "Recoleta Cemetery", "Teatro Colón", "Plaza de Mayo", "Palacio Barolo"],
    "Food": ["Asado", "Empanadas", "Milanesa", "Dulce de Leche", "Choripán"],
    "Shopping": ["Florida Street", "Palermo Soho", "Avenida Santa Fe", "San Telmo", "Galerías Pacífico"],
    "Adventure": ["Tigre Delta", "Buenos Aires Zoo", "Reserva Ecológica", "Iguazú Falls", "El Tigre"]
            },
            "Rio de Janeiro": {
    "Culture": ["Christ the Redeemer", "Sugarloaf Mountain", "Selarón Steps", "Copacabana Beach", "Maracanã Stadium"],
    "Food": ["Feijoada", "Pão de queijo", "Coxinha", "Acarajé", "Churrasco"],
    "Shopping": ["Shopping Leblon", "Rua Visconde de Pirajá", "Ipanema", "Barra Shopping", "São Conrado"],
    "Adventure": ["Ipanema Beach", "Tijuca Forest", "Lagoa Rodrigo de Freitas", "Corcovado", "Pedra Bonita"]
            },
            "Milan": {
    "Culture": ["Duomo di Milano", "Galleria Vittorio Emanuele II", "Sforza Castle", "The Last Supper", "Pinacoteca di Brera"],
    "Food": ["Risotto alla Milanese", "Panettone", "Cotoletta", "Milanese Pizza", "Osso Buco"],
    "Shopping": ["Via Montenapoleone", "Galleria Vittorio Emanuele II", "Corso Buenos Aires", "La Rinascente", "Fidenza Village"],
    "Adventure": ["Navigli", "Sempione Park", "Lake Como", "Milan Cathedral Rooftop", "Piazza del Duomo"]
            },
            "Glasgow": {
    "Culture": ["Glasgow Cathedral", "Kelvingrove Art Gallery", "The Lighthouse", "Glasgow Science Centre", "Buchanan Street"],
    "Food": ["Haggis", "Cullen Skink", "Scotch Pie", "Fish and Chips", "Irn-Bru"],
    "Shopping": ["Buchanan Street", "Merchant City", "Argyle Street", "St. Enoch Centre", "Princes Square"],
    "Adventure": ["Loch Lomond", "Glasgow Green", "Kelvingrove Park", "Pollok Country Park", "The Trossachs"]
            },
            "Dublin": {
    "Culture": ["Trinity College Library", "Dublin Castle", "St. Patrick's Cathedral", "The Spire", "Temple Bar"],
    "Food": ["Irish Stew", "Guinness", "Coddle", "Soda Bread", "Seafood Chowder"],
    "Shopping": ["Grafton Street", "St. Stephen's Green Shopping Centre", "Dundrum Town Centre", "Henry Street", "Powerscourt Townhouse Centre"],
    "Adventure": ["Phoenix Park", "Dublin Bay", "Howth Cliff Walk", "Dublin Zoo", "Killiney Hill"]
            },
            "Cairo": {
    "Culture": ["Pyramids of Giza", "Egyptian Museum", "Sphinx", "Khan el-Khalili", "Coptic Cairo"],
    "Food": ["Koshari", "Fattah", "Falafel", "Baklava", "Mahshi"],
    "Shopping": ["Khan el-Khalili", "City Stars Mall", "Mall of Arabia", "Zamalek", "Wekala El-Balah"],
    "Adventure": ["Nile River Cruise", "Mount Sinai", "Desert Safari", "Giza Plateau", "White Desert"]
            },
            "Nairobi": {
    "Culture": ["Nairobi National Park", "Giraffe Centre", "Karen Blixen Museum", "David Sheldrick Wildlife Trust", "National Museum"],
    "Food": ["Nyama Choma", "Sukuma", "Mandazi", "Ugali", "Chapati"],
    "Shopping": ["Maasai Market", "Nairobi Railway Station Market", "Yaya Centre", "Sarit Centre", "Westgate Shopping Mall"],
    "Adventure": ["Giraffe Centre", "Nairobi National Park", "Ngong Hills", "Hell’s Gate", "Lake Naivasha"]
            },
            "Kuala Lumpur":{
                "Culture": ["Petronas Towers", "Batu Caves", "Merdeka Square", "Sultan Abdul Samad Building", "National Mosque"],
                "Food": ["Jalan Alor", "Central Market", "Little India", "Chinatown", "Hawker Stalls"],
                "Shopping": ["Pavilion Mall", "Bukit Bintang", "Suria KLCC", "Central Market", "Times Square"],
                "Adventure": ["Batu Caves", "KL Bird Park", "KL Forest Eco Park", "Sunway Lagoon", "Taman Negara National Park"]
            },
            "Singapore":{
                "Culture": ["Gardens by the Bay", "Chinatown", "Merlion Park", "Little India", "Singapore Zoo"],
                "Food": ["Hawker Centres", "Chinatown Food Street", "Maxwell Food Centre", "Tiong Bahru Market", "Jumbo Seafood"],
                "Shopping": ["Orchard Road", "Marina Bay Sands", "VivoCity", "Bugis Street", "Mustafa Centre"],
                "Adventure": ["Sentosa Island", "Universal Studios Singapore", "Clarke Quay", "East Coast Park", "Singapore Flyer"]
            },
            
            "Tokyo": {
                "Culture": ["Senso-ji Temple", "Meiji Shrine", "Tokyo Skytree", "Shinjuku Gyoen National Garden", "Ueno Park"],
                "Food": ["Tsukiji Fish Market", "Shibuya Crossing", "Ramen Street", "Omoide Yokocho", "Nakamise Street"],
                "Shopping": ["Ginza", "Harajuku", "Shibuya 109", "Omotesando", "Akihabara"],
                "Adventure": ["Mount Fuji", "Shinjuku Gyoen Park", "Odaiba", "Yoyogi Park", "Tokyo Disneyland"]
            }
        }
        self.geolocator = Nominatim(user_agent="tour_planner")

    def generate_itinerary(self, city, interests):
        itinerary = []
        if city in self.places_data:
            for interest in interests:
                itinerary.extend(self.places_data[city].get(interest, []))
        random.shuffle(itinerary)  # Randomize order for variety
        return itinerary[:5]  # Limit to 5 places for simplicity

    def get_location_coordinates(self, place_name):
        # Geocode the place to get coordinates (lat, lon)
        location = self.geolocator.geocode(place_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None

# Optimization Agent
class OptimizationAgent:
    def __init__(self, geolocator):
        self.geolocator = geolocator
        self.transport_modes = ["Walking", "Taxi", "Bus"]

    def optimize_routes(self, itinerary, start_time, end_time, budget):
        optimized_itinerary = []
        total_time = (end_time.hour - start_time.hour) * 60  # Total minutes available
        time_per_place = total_time // len(itinerary)
        budget_left = budget

        # Convert place names to coordinates
        coordinates = [self.get_location_coordinates(place) for place in itinerary]
        coordinates = [coord for coord in coordinates if coord is not None]

        for i in range(len(coordinates) - 1):
            distance = geodesic(coordinates[i], coordinates[i + 1]).km
            if distance < 2 and budget_left >= 0:
                mode = "Walking"
            elif budget_left >= 20:
                mode = "Taxi"
                budget_left -= 20
            else:
                mode = "Bus"
                budget_left -= 10
            optimized_itinerary.append((itinerary[i], itinerary[i + 1], mode, time_per_place))
        return optimized_itinerary

    def get_location_coordinates(self, place_name):
        # Geocode the place to get coordinates (lat, lon)
        location = self.geolocator.geocode(place_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None

# Weather and News Agent
class WeatherNewsAgent:
    def __init__(self, weather_api_key, news_api_key):
        self.weather_api_key = weather_api_key
        self.news_api_key = news_api_key

    def get_weather(self, city):
        url = f"http://api.weatherapi.com/v1/current.json?key={self.weather_api_key}&q={city}"
        response = requests.get(url)
        return response.json()["current"]

    def get_news(self, city):
        url = f"https://newsapi.org/v2/everything?q={city}&apiKey={self.news_api_key}"
        response = requests.get(url)
        return response.json()["articles"][:10]  # Limit to 3 articles

# Main Application
def main():
    st.title("One-Day Tour Planner")
    memory_agent = MemoryAgent()
    itinerary_generator = ItineraryGenerator()
    optimization_agent = OptimizationAgent(itinerary_generator.geolocator)  # Pass geolocator here
    weather_news_agent = WeatherNewsAgent("951d437e88704ac8b4c102525243011", "14b05e12609248aca84ee4db2b3f026d")
    user_id = "12345"

    # Collect user preferences
    city = st.text_input("Enter the city you'd like to visit:", "Rome")
    budget = st.slider("Enter your budget for the day (in $):", 10, 100, 50)
    interests = st.multiselect("What are your interests?", ["Culture", "Adventure", "Food", "Shopping"], default=["Culture"])
    start_time = st.time_input("Enter the time you want to start:", value=None)
    end_time = st.time_input("Enter the time you want to end:", value=None)

    # Store user preferences
    preferences = {
        "city": city,
        "budget": budget,
        "interests": ", ".join(interests),
        "start_time": str(start_time),
        "end_time": str(end_time)
    }
    memory_agent.store_user_preference(user_id, preferences)

    if st.button("Generate Itinerary"):
        # Generate Itinerary
        itinerary = itinerary_generator.generate_itinerary(city, interests)

        # Optimize Routes
        optimized_routes = optimization_agent.optimize_routes(itinerary, start_time, end_time, budget)

        # Display Itinerary
        st.subheader("Your Optimized Itinerary:")
        for route in optimized_routes:
            st.write(f"{route[0]} -> {route[1]} via {route[2]} (Spend {route[3]} mins)")

        # Fetch Weather Information
        weather = weather_news_agent.get_weather(city)
        st.subheader(f"Weather in {city}:")
        st.write(f"Temperature: {weather['temp_c']}°C")
        st.write(f"Condition: {weather['condition']['text']}")

        # Fetch News Articles
        news = weather_news_agent.get_news(city)
        st.subheader(f"Latest News in {city}:")
        for article in news:
            st.write(f"- {article['title']} ({article['publishedAt']})")

if __name__ == "__main__":
    main()
