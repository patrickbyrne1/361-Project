# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
import datetime, random, json
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
collection=db["name"]

# create the application object
app = Flask(__name__)
CORS(app, support_credentials=True)

ip_addy = "wiki-text-scraper.herokuapp.com" #"10.200.37.7:4500"

"""
@app.route("/<choice>")
def changeIP(choice):
    global ip_addy
    ip_addy = choice + ":4500"
    return ip_addy
        
"""    
    


# API for Quality of Life
# citation:https://stackoverflow.com/questions/18602276/flask-urls-w-variable-parameters; User: Sean Vieira
# citation:https://www.geeksforgeeks.org/python-program-to-extract-string-till-first-non-alphanumeric-character/
# Notes: pop density is truncated, not rounded to nearest int
@app.route("/QoL/<path:countries>")
@cross_origin(supports_credentials=True)
def QoL(countries=None):
    countries = countries.split("/")
    #countryStats = {}
    popList = []
    leBirthList = []
    le60List = []
    govTransList = []
    natDisRiskList = []
    peaceIndexList = []


    count = 0
    #regex = pattern.compile("")
    # get population densities
    for country in countries:
        infobox = requests.get("http://" + ip_addy + "/wiki/" + country + "/infobox")
        infoboxText = json.loads(infobox.text)
        grabDensity = ""
        for x in infoboxText:
            if x.find("Density") != -1:
                grabDensity += x[9:]
                index = re.search(r'\D+', grabDensity).start()
                grabDensity = grabDensity[:index]
            elif x.find("density") != -1:
                grabDensity += x[12:]
                index = re.search(r'\D+', grabDensity).start()
                grabDensity = grabDensity[:index]
        popList.append(int(grabDensity))
        count += 1
    # get most recent (2019) healthy life expectancy at birth (non-gender specific) - at index 10
    for country in countries:
        found = False
        leBirthResults = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_life_expectancy/tablesh2")
        leBirthResults = json.loads(leBirthResults.text)
        leBirth = leBirthResults["List by the World Health Organization (2019)[edit]"]
        for lists in leBirth:
            try:
                countryName = lists[0].replace("_", " ")
            except Exception:
                print("First one")
                print(lists)
            if countryName == country:
                found = True
                leBirthList.append(float(lists[11]))
                le60List.append(float(lists[15]))
        if not found:
            leBirthList.append(0)
            le60List.append(0)

    # govTransList
    for country in countries:
        found = False
        govTransResults = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_consultation_on_rule-making/tablesNoH")
        govTransResults = json.loads(govTransResults.text)
        for lists in govTransResults:
            try:
                countryName = lists[1].replace("_", " ")
            except Exception:
                print("Second one")
                print(lists)
            if countryName == country:
                found = True
                print(countryName)
                govTransList.append(float(lists[2]))
        if not found:
            govTransList.append(37.0) # list has 36 entries so if not in list getting a score of 37 - assumed to be so bad as not to divulge info
            
                
        #leBirth = leBirthResults["List by the World Health Organization (2019)[edit]"]
        #for lists in leBirth:
    
    # natDisRiskList
    # first percentage is most recent data (2018)
    for country in countries:
        found = False
        natDisRiskResults = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_natural_disaster_risk/tables")
        natDisRiskResults = json.loads(natDisRiskResults.text)
        disRisk = natDisRiskResults["Rankings by country[edit]"]
        print(disRisk)
        for lists in disRisk:
            countryName = lists[1].replace("_", " ")
            if countryName == country:
                found = True
                print(countryName)
                if lists[0] == "-":
                    natDisRiskList.append(172.0)
                else:
                    natDisRiskList.append(int(lists[0]))
        if not found:
            natDisRiskList.append(172.0) # not in list (171 entries) - Samoa put here
    

    # peaceIndexList
    for country in countries:
        found = False
        globPeaceResults = requests.get("http://" + ip_addy + "/wiki/Global_Peace_Index/tablesh2")
        globPeaceResults = json.loads(globPeaceResults.text)
        globPeace = globPeaceResults["Global Peace Index rankings (2008–2019)[edit]"]
        for lists in globPeace:
            countryName = lists[0].replace("_", " ")
            if countryName == country:
                found = True
                print(countryName)
                temp = lists[1]
                if len(temp) > 2 and temp[2] == '=':
                    temp = temp[:2]
                if len(temp) > 3 and temp[3] == '=':
                    temp = temp[:3]
                peaceIndexList.append(int(temp)) # 1st number is most recent ranking
        if not found:
            peaceIndexList.append(164.0) # not in list (163 entries)

    """ 
    Quality of Life algorithm:
    pop density: lower better
    life exp: higher better (100 - percentage to give smaller number)
    govTrans: use rank so lower better
    natRisk: use rank so lower better
    globPeace: use rank so lower better
    
    Add up values for each country.  The country with lowest value will be best QoL.
    Countries are in the countries list already so make new list to place countries in
    based on score.  The lower the score, the earlier you are placed in list so it will
    already be sorted.
    """
    QoLList = []
    print(countries)
    print(popList)
    print(leBirthList)
    print(le60List)
    print(govTransList)
    print(natDisRiskList)
    print(peaceIndexList)
    # leBirth and le60 are better if larger which is why I subtract them from 100 (100% being the largest possible).
    # The other criteria are all better if smaller.  I will then go through the QoL and place countries in order from smallest
    # sum to largest sum.  The smaller the sum, the better the QoL.
    for x in range(len(countries)):
        QoLList.append(popList[x] + (100-leBirthList[x]) + (100-le60List[x]) + govTransList[x] + natDisRiskList[x] + peaceIndexList[x])
        print(x)
    
    
    sortedQoL = []
    numItems = len(countries)
    while numItems > 0:
        minIndex = 0
        change = False
        for x in range(len(countries)):
            if QoLList[minIndex] > QoLList[x]:
                minIndex = x
                
       
        if len(countries) >= 0 and len(QoLList) >= 0 and minIndex >= 0:
            #print(minIndex)
            #print(countries[minIndex])
            sortedQoL.append(countries[minIndex])
            del countries[minIndex]
            del QoLList[minIndex]
        numItems = len(countries)



    return jsonify(sortedQoL)





# API for Country Lookup
# citation:https://www.geeksforgeeks.org/python-program-to-extract-string-till-first-non-alphanumeric-character/
@app.route("/cLookup/<country>")
@cross_origin(supports_credentials=True)
def cLookup(country):
    
    countryStats = {}
    entry = collection.find_one({"name":country})
    if entry != None:
        return entry
    

    infobox = requests.get("http://" + ip_addy + "/wiki/" + country + "/infobox")
    coords = requests.get("http://" + ip_addy + "/wiki/" + country + "/coords")

    # get population
    infoBoxData = json.loads(infobox.text)
    pop = ""
    govt = ""
    for x in range(len(infoBoxData)):
        if infoBoxData[x] == "Population":
            pop = infoBoxData[x+1]
        if infoBoxData[x][:10] == "Government":
            if infoBoxData[x].find("Unitary parliamentaryrepublic") != -1:
                govt = "Government Unitary parliamentary republic"
            else:
                govt = infoBoxData[x]
    
    govt = govt[10:]

    # get coordinates
    print(coords.text)
    geo = json.loads(coords.text)
    coords = ""
    coords += geo["latitude"]
    coords += ", "
    coords += geo["longitude"]
    
    
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
    
    
    found = False
    natDisRisk = ""
    natDisRiskResults = requests.get("http://" + ip_addy + "/wiki/List_of_countries_by_natural_disaster_risk/tables")
    natDisRiskResults = json.loads(natDisRiskResults.text)
    disRisk = natDisRiskResults["Rankings by country[edit]"]
    for lists in disRisk:
        #countryName = lists[1].replace("_", " ")
        if lists[1].replace("_", " ") == country:
            found = True
            natDisRisk = lists[0]
    if not found:
        natDisRisk = "Not Available"
    

    # peaceIndexList
    
    found = False
    globPeaceResults = requests.get("http://" + ip_addy + "/wiki/Global_Peace_Index/tablesh2")
    globPeaceResults = json.loads(globPeaceResults.text)
    globPeace = globPeaceResults["Global Peace Index rankings (2008–2019)[edit]"]
    peaceIndex = ""
    countryName = lists[0].replace("_", " ")
    if countryName == country:
        found = True             
        temp = lists[1]
        if len(temp) > 2 and temp[2] == '=':
            temp = temp[:2]
        if len(temp) > 3 and temp[3] == '=':
            temp = temp[:3]
        peaceIndex = temp 
    if not found:
        peaceIndex = "Not Available"

    countryStats.update({"Population":pop})
    countryStats.update({"Coordinates":coords})
    countryStats.update({"Government": govt})
    countryStats.update({"Global Peace Index": peaceIndex})
    countryStats.update({"Life Expectancy at birth": leBirth})
    countryStats.update({"Life Expectancy at 60": le60})
    countryStats.update({"Natural Disaster Risk": natDisRisk})

    countryStats.update({"_id":0})
    countryStats.update({"name":country})
    # insert into mongodb
    collection.insert_one(countryStats)

    return countryStats

@app.route('/map/<country>', methods = ['GET', 'POST'])
@cross_origin(supports_credentials=True)
def mapper(country):
    coords = requests.get("http://" + ip_addy + "/wiki/" + country + "/coords")
    geo = json.loads(coords.text)
    
    coordDict = {"Lat":geo["lat"], "Lon":geo["lon"]}
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
    headers = {'Content-type:':'application/json', 'Accept':'text/plain'}
    x = requests.post(url, json=mapDict)
    
    return x.json()
        

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=7200)

