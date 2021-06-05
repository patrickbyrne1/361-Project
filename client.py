# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
import datetime, random, json, time
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re
import unicodedata
import pymongo
from pymongo import MongoClient

from flask_cors import CORS, cross_origin

# mongodb setup
cluster = MongoClient("mongodb+srv://wheatstraw:67!Apollo625@cluster0.s9qh7.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

db=cluster["countries"]
collection=db["all_country_data"]

# create the application object
app = Flask(__name__)
CORS(app, support_credentials=True)

ip_addy = "wiki-text-scraper.herokuapp.com" #"10.200.37.7:4500"


countries = ["Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cape Verde","Cameroon",
             "Central African Republic","Chad","Comoros","Democratic Republic of the Congo","Republic of the Congo","Cote d'Ivoire",
             "Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini","Ethiopia","Gabon","Gambia","Ghana","Guinea","Guinea-Bissau",
             "Kenya","Lesotho","Liberia","Libya","Madagascar","Malawi","Mali","Mauritius","Morocco","Mozambique","Namibia","Niger",
             "Nigeria","Rwanda","Sao Tome and Principe","Senegal","Seychelles","Sierra Leone","Somalia","South Africa","South Sudan",
             "Sudan","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe","Afghanistan","Armenia","Azerbaijan","Bahrain",
             "Bangladesh","Bhutan","Brunei","Cambodia","China","Cyprus","Georgia (country)","India","Indonesia","Iran","Iraq","Israel",
             "Japan","Jordan","Kazakhstan","Kuwait","Kyrgyzstan","Laos","Lebanon","Malaysia","Maldives","Mongolia","Myanmar","Nepal",
             "North Korea","Oman","Pakistan","Philippines","Qatar","Russia","Saudi Arabia","Singapore","South Korea",
             "Sri Lanka","Syria","Taiwan","Tajikistan","Thailand","Timor-Leste","Turkey","Turkmenistan","United Arab Emirates",
             "Uzbekistan","Vietnam","Yemen","Australia","Fiji","Kiribati","Marshall Islands","Federated States of Micronesia","Nauru",
             "New Zealand","Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu","Albania","Andorra","Austria",
             "Belarus","Belgium","Bosnia and Herzegovina","Bulgaria","Croatia","Czechia","Denmark","Estonia","Finland","France",
             "Germany","Greece","Hungary","Iceland","Ireland","Italy","Kosovo","Latvia","Liechtenstein","Lithuania","Luxembourg","Malta",
             "Moldova","Monaco","Montenegro","Netherlands","North Macedonia","Norway","Poland","Portugal","Romania","San Marino",
             "Slovakia","Slovenia","Spain","Sweden","Switzerland","Ukraine","United Kingdom","Vatican City","Antigua and Barbuda",
             "Bahamas","Barbados","Belize","Canada","Costa Rica","Cuba","Dominica","Dominican Republic","El Salvador","Grenada",
             "Guatemala","Haiti","Honduras","Jamaica","Mexico","Nicaragua","Panama","Saint Kitts and Nevis","Saint Vincent and the Grenadines",
             "Trinidad and Tobago","United States","Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador","Guyana","Paraguay","Peru",
             "Suriname","Uruguay","Venezuala"]


# get_coords function scrapes the coordinates
# of a country from wikipedia
def get_coords(country):
    coords = requests.get("http://" + ip_addy + "/wiki/" + country + "/coords")
    geo = json.loads(coords.text)
    coords = ""
    coords += geo["latitude"]
    coords += ", "
    coords += geo["longitude"]
    return coords

# get_population function scrapes the population
# of a country from wikipedia
def get_population(country):
    # get population
    infobox = requests.get("http://" + ip_addy + "/wiki/" + country + "/infobox")
    infoBoxData = json.loads(infobox.text)
    pop = ""
    for x in range(len(infoBoxData)):
        if infoBoxData[x] == "Population":
            pop = infoBoxData[x+1]
            break
    return pop

# get_population_density function scrapes the
# population density of a country from wikipedia
def get_pop_density(country):
    infobox = requests.get("http://" + ip_addy + "/wiki/" + country + "/infobox")
    infoboxText = json.loads(infobox.text)
    grabDensity = ""
    for x in infoboxText:
        if x.find("Density") != -1 or x.find("density") != -1:
            num_pattern = re.search(r'[0-9,]+', x)
            start_index = num_pattern.start()
            end_index = num_pattern.end() 
            grabDensity = x[start_index:end_index]
    return grabDensity


# get_government function scrapes the
# type of government of a country from wikipedia
def get_government(country):
    infobox = requests.get("http://" + ip_addy + "/wiki/" + country + "/infobox")
    infoBoxData = json.loads(infobox.text)
    govt = ""
    for x in range(len(infoBoxData)):
        if infoBoxData[x][:10] == "Government":
            if infoBoxData[x].find("Unitary parliamentaryrepublic") != -1:
                govt = "Government Unitary parliamentary republic"
            else:
                govt = infoBoxData[x][10:]
    return govt


# get_gov_transparency function scrapes the
# government tranparency of a country from wikipedia
def get_gov_tranparency(country):
    gov_trans_results = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_consultation_on_rule-making/tablesNoH")
    gov_trans_results = json.loads(gov_trans_results.text)
    for lists in gov_trans_results[0]:
        country_name = lists[1].replace("_", " ")
        if country_name == country:
            return float(lists[0])
    #govTransList.append(37.0) # list has 36 entries so if not in list getting a score of 37 - assumed to be so bad as not to divulge info
    return 37.0


# get_life_expectancy function scrapes the
# life expectancy at birth and at 60 of a country from wikipedia
def get_life_expectancy(country):
    # get most recent (2019) healthy life expectancy at birth (non-gender specific) - at index 10
    leBirth = 0
    le60 = 0
    lifeExpRequest = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_life_expectancy/tablesh2")
    lifeExp = json.loads(lifeExpRequest.text)
    leCountries = lifeExp["List by the World Health Organization (2019)[edit]"]
    for leCountry in leCountries:
        if leCountry[0].replace("_", " ") == country:
            leBirth = leCountry[11] + "%"
            le60 = leCountry[15] + "%"
    return leBirth, le60


# get_nat_disaster_risk function scrapes the
# natural disaster risk of a country from wikipedia
def get_nat_disaster_risk(country):

    natDisRiskResults = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_natural_disaster_risk/tables")
    natDisRiskResults = json.loads(natDisRiskResults.text)
    disRisk = natDisRiskResults["Rankings by country[edit]"]
    for lists in disRisk:
        if lists[1].replace("_", " ") == country:
            return lists[0]
    return "Not Available"
    

# get_peace_index function scrapes the
# global peace index of a country from wikipedia
def get_peace_index(country):
    peaceIndex = ""
    globPeaceResults = requests.get("http://" + ip_addy + "/wiki/Global_Peace_Index/tablesh2")
    globPeaceResults = json.loads(globPeaceResults.text)
    globPeace = globPeaceResults["Global Peace Index rankings (2008–2019)[edit]"]
    for lists in globPeace:
        countryName = lists[0].replace("_", " ")
        if countryName == country:      
            peaceIndex = lists[1]
            if len(peaceIndex) > 2 and peaceIndex[2] == '=':
                peaceIndex = peaceIndex[:2]
            if len(peaceIndex) > 3 and peaceIndex[3] == '=':
                peaceIndex = peaceIndex[:3]
            return peaceIndex
    return "Country not recognized"


# function to populate MongoDB with relevant country information
# This was added for sprint 5.
@app.route("/countries")
def country_info():
    countryStats = {}
    start = time.time()
    for x in range(len(countries)):
        country = countries[x]
        geo = get_coords(country)
        pop = get_population(country)
        govt = get_government(country)
        gov_transparency = get_gov_tranparency(country)
        pop_density = get_pop_density(country)
        leBirth = get_life_expectancy(country)[0]
        le60 = get_life_expectancy(country)[1]
        natDisRisk = get_nat_disaster_risk(country)
        peaceIndex = get_peace_index(country)

        countryStats.update({"Population":pop})
        countryStats.update({"Coordinates":geo})
        countryStats.update({"Government": govt})
        countryStats.update({"Government Transparency": gov_transparency})
        countryStats.update({"Population Density": pop_density})
        countryStats.update({"Global Peace Index": peaceIndex})
        countryStats.update({"Life Expectancy at Birth": leBirth})
        countryStats.update({"Life Expectancy at 60": le60})
        countryStats.update({"Natural Disaster Risk": natDisRisk})

        countryStats.update({"_id":x})
        countryStats.update({"Name":country})
        # insert into mongodb
        collection.insert_one(countryStats)
    #return countryStats
    return "<h2>Request completed in " + str(time.time()-start) + " seconds.</h2>"




# API for Country Lookup
# citation:https://www.geeksforgeeks.org/python-program-to-extract-string
# citation(cont.): -till-first-non-alphanumeric-character/
@app.route("/cLookup/<country>")
@cross_origin(supports_credentials=True)
def cLookup(country):
    country_results = collection.find()
    all_data = list(country_results)
    countryStats = {}
    for place in all_data:
        if place["Name"] == country:            
            countryStats.update({"Population":place["Population"]})
            countryStats.update({"Coordinates":place["Coordinates"]})
            countryStats.update({"Government":place["Government"]})
            countryStats.update({"Global Peace Index":place["Global Peace Index"]})
            countryStats.update({"Life Expectancy at Birth":place["Life Expectancy at Birth"]})
            countryStats.update({"Life Expectancy at 60":place["Life Expectancy at 60"]})
            countryStats.update({"Natural Disaster Risk":place["Natural Disaster Risk"]})
            countryStats.update({"Name":place["Name"]})
            break
    """
    countryStats = {}
    countryStats.update({"Population":get_population(country)})
    countryStats.update({"Coordinates":get_coords(country)})
    countryStats.update({"Government": get_government(country)})
    countryStats.update({"Global Peace Index": get_peace_index(country)})
    countryStats.update({"Life Expectancy at birth": get_life_expectancy(country)[0]})
    countryStats.update({"Life Expectancy at 60": get_life_expectancy(country)[1]})
    countryStats.update({"Natural Disaster Risk": get_nat_disaster_risk(country)})
    countryStats.update({"Name":country})
    """
    return countryStats



    
# API for Quality of Life
# citation:https://stackoverflow.com/questions/18602276/flask-urls-w-variable-parameters; User: Sean Vieira
# citation:https://www.geeksforgeeks.org/python-program-to-extract-string-till-first-non-alphanumeric-character/
# Notes: pop density is truncated, not rounded to nearest int
@app.route("/top10")
@cross_origin(supports_credentials=True)
def top10():
    temp_countries = countries.copy()

    pop_list = []
    le_birth_list = []
    le_60_list = []
    gov_trans_list = []
    nat_dis_risk_list = []
    peace_index_list = []

    # get all the data from mongodb database
    country_results = collection.find()
    all_data = list(country_results)
    for country in all_data:
        if country["Population Density"] == ' ' or country["Population Density"] == '':
            pop_list.append(500)
        else:    
            pop_list.append(country["Population Density"].replace(',',''))
        if country["Life Expectancy at Birth"] != 0:
            le_birth_list.append(country["Life Expectancy at Birth"][:3])
        else:
            le_birth_list.append(0)
        if country["Life Expectancy at 60"] != 0:
            le_60_list.append(country["Life Expectancy at 60"][:3])
        else:
            le_60_list.append(0)
        
        gov_trans_list.append(country["Government Transparency"])
        if country["Natural Disaster Risk"] == "Not Available":
            nat_dis_risk_list.append(172.0)
        else:
            nat_dis_risk_list.append(country["Natural Disaster Risk"])
        if country["Global Peace Index"] == "Country not recognized":
            peace_index_list.append(164.0)
        else:
            peace_index_list.append(country["Global Peace Index"])

   
    """ 
    The top10 countries algorithm is basically the same as the Quality of Life algorithm.  The only difference is it bases the comparison
    on ALL countries and doesn't remove countries with incomplete information. 
    """
    QoLList = []

    # leBirth and le60 are better if larger which is why I subtract them from 100 (100% being the largest possible).
    # The other criteria are all better if smaller.  I will then go through the QoL and place countries in order from smallest
    # sum to largest sum.  The smaller the sum, the better the QoL.    
    for x in range(len(countries)):
        #if peace_index_list[x] == 164.0:
        #    incomplete.append("Incomplete: " + countries.pop(x))
        #    x -= 1
        QoLList.append(float(pop_list[x]) + (100-float(le_birth_list[x])) + (100-float(le_60_list[x])) + float(gov_trans_list[x]) + float(nat_dis_risk_list[x]) + float(peace_index_list[x]))
        print(x)
 
    print(QoLList)
    sortedQoL = []
    
    numItems = len(temp_countries)
    while numItems > 0:
        minIndex = 0
        for x in range(len(temp_countries)):
            if QoLList[minIndex] > QoLList[x]:
                minIndex = x
        if len(temp_countries) >= 0 and len(QoLList) >= 0 and minIndex >= 0:
            #print(minIndex)
            #print(countries[minIndex])
            sortedQoL.append(temp_countries[minIndex])
            del temp_countries[minIndex]
            del QoLList[minIndex]
        numItems = len(temp_countries)

    bestCountries = []
    for x in range(10):
        bestCountries.append(sortedQoL[x])
    
    return jsonify(bestCountries)


@app.route("/QoL/<path:countryParams>")
@cross_origin(supports_credentials=True)
def QoL(countryParams=None):
    countries_list = countryParams.split("/")
    #temp_countries = countries.copy()

    pop_list = []
    le_birth_list = []
    le_60_list = []
    gov_trans_list = []
    nat_dis_risk_list = []
    peace_index_list = []

    # get all the data from mongodb database
    country_results = collection.find()
    all_data = list(country_results)
    new_countries = []
    for country in all_data:
        if country["Name"] in countries_list:
            new_countries.append(country["Name"])
            if country["Population Density"] == ' ' or country["Population Density"] == '':
                pop_list.append(500)
            else:    
                pop_list.append(country["Population Density"].replace(',',''))
            if country["Life Expectancy at Birth"] != 0:
                le_birth_list.append(country["Life Expectancy at Birth"][:3])
            else:
                le_birth_list.append(0)
            if country["Life Expectancy at 60"] != 0:
                le_60_list.append(country["Life Expectancy at 60"][:3])
            else:
                le_60_list.append(0)
            
            gov_trans_list.append(country["Government Transparency"])
            if country["Natural Disaster Risk"] == "Not Available":
                nat_dis_risk_list.append(172.0)
            else:
                nat_dis_risk_list.append(country["Natural Disaster Risk"])
            if country["Global Peace Index"] == "Country not recognized":
                peace_index_list.append(164.0)
            else:
                peace_index_list.append(country["Global Peace Index"])

    print(new_countries)
    """ 
    The top10 countries algorithm is basically the same as the Quality of Life algorithm.  The only difference is it bases the comparison
    on ALL countries and doesn't remove countries with incomplete information. 
    """
    QoLList = []
    

    # leBirth and le60 are better if larger which is why I subtract them from 100 (100% being the largest possible).
    # The other criteria are all better if smaller.  I will then go through the QoL and place countries in order from smallest
    # sum to largest sum.  The smaller the sum, the better the QoL.    
    for x in range(len(countries_list)):
        incomplete = []
        if peace_index_list[x] == 164.0:
            incomplete.append("Incomplete: " + new_countries[x])
            print(new_countries.pop(x))
            #x -= 1
        QoLList.append(float(pop_list[x]) + (100-float(le_birth_list[x])) + (100-float(le_60_list[x])) + float(gov_trans_list[x]) + float(nat_dis_risk_list[x]) + float(peace_index_list[x]))
        print(x)
    print(countries_list)
    print(incomplete)
    print(new_countries)
    print(QoLList)
    sortedQoL = []
    
    numItems = len(new_countries)
    while numItems > 0:
        minIndex = 0
        for x in range(len(new_countries)):
            if QoLList[minIndex] > QoLList[x]:
                minIndex = x
        print(minIndex)
        if len(new_countries) >= 0 and len(QoLList) >= 0 and minIndex >= 0:
            #print(minIndex)
            #print(countries[minIndex])
            sortedQoL.append(new_countries[minIndex])
            print(sortedQoL)
            del new_countries[minIndex]
            del QoLList[minIndex]
            print(QoLList)
        numItems = len(new_countries)
    for item in incomplete:
        sortedQoL.append(item)
    print(sortedQoL)
    return jsonify(sortedQoL)



@app.route('/map/<country>', methods = ['GET', 'POST'])
@cross_origin(supports_credentials=True)
def mapper(country):
    coords = requests.get("http://" + ip_addy + "/wiki/" + country + "/coords")
    geo = json.loads(coords.text)
    country = country.replace(" ","_")
    #coordDict = {"Lat":geo["lat"], "Lon":geo["lon"]}
    url = "https://easy-map-maker.herokuapp.com"
    mapDict = {"id":"mymap", 
               "key":"EgVzT4mZhG1WviCrcx7d", 
               "tiler":"https://api.maptiler.com/maps/topo/{z}/{x}/{y}.png",
               "100": {
                   "pageid":100,
                   "ns":0,
                   "title":country,
                   "coordinates": {"lat":geo["lat"], "lon":geo["lon"]}
               }
               
    }
    #headers = {'Content-type:':'application/json', 'Accept':'text/plain'}
    x = requests.post(url, json=mapDict)
    
    return x.json()
        

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=7200)

