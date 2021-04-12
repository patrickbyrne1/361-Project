from bs4 import BeautifulSoup
import requests


def main():
    place = input("Enter a place to get the coordinates from. Press 'q' to quit.")

    while place.lower() != 'q':
        coordinates(place)
        place = input("Enter a place to get the coordinates from. Press 'q' to quit.")



def coordinates(place):
    
        url = "https://en.wikipedia.org/wiki/" + place
        source = requests.get(url).text
        soup = BeautifulSoup(source, 'lxml')
        latitude = soup.find('span', class_='latitude').text
        longitude = soup.find('span', class_='longitude').text
        print()
        print(f"GPS Coordinates of {place}\nLatitude: {latitude} Longitude: {longitude}")
        print()





if __name__ == "__main__":
    main()
