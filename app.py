# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
import datetime, random, json
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re
import unicodedata


from flask_cors import CORS, cross_origin

# create the application object
app = Flask(__name__)
CORS(app, support_credentials=True)



# Get Infobox Data
@app.route('/wiki/<title>/infobox')
def wikibox(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
    text = ''
    items = []
    regex = re.compile('infobox.*')
    for info in soup.find('table', {"class":regex}):

        for data in info.find_all('tr'):

            #text += info.text
            #text += "\n"
            dataStr = data.text.replace('\xa0', ' ')
            dataStr = dataStr.replace('\n',' ')
            dataStr = dataStr.replace('\ufeff',' ')
            
            items.append(dataStr)
            text += dataStr
        #text += "\n"
    return jsonify(items)


# Get coordinates for a place
@app.route('/wiki/<title>/coords')
def coords(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    
    latitude = soup.find('span', class_='latitude').text
    longitude = soup.find('span', class_='longitude').text
    if latitude is None or longitude is None:
        return make_response(jsonify(Error="No coordinates found."), 404)
    latitude = unicodedata.normalize('NFC', latitude)
    longitude = unicodedata.normalize('NFC', longitude)
    coord_object = {
        "latitude":latitude,
        "longitude":longitude
    }
    return make_response(jsonify(coord_object), 200)

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
        infobox = requests.get("http://192.168.0.192:3600/wiki/" + country + "/infobox")
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
        leBirthResults = requests.get("http://192.168.0.192:3600/wiki/List_of_countries_by_life_expectancy/tablesh2")
        leBirthResults = json.loads(leBirthResults.text)
        leBirth = leBirthResults["List by the World Health Organization (2019)[edit]"]
        for lists in leBirth:
            countryName = lists[0].replace("_", " ")
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
        govTransResults = requests.get("http://192.168.0.192:3600/wiki/List_of_countries_by_consultation_on_rule-making/tablesNoH")
        govTransResults = json.loads(govTransResults.text)
        for lists in govTransResults:
            countryName = lists[1].replace("_", " ")
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
        natDisRiskResults = requests.get("http://192.168.0.192:3600/wiki/List_of_countries_by_natural_disaster_risk/tables")
        natDisRiskResults = json.loads(natDisRiskResults.text)
        disRisk = natDisRiskResults["Rankings by country[edit]"]
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
        globPeaceResults = requests.get("http://192.168.0.192:3600/wiki/Global_Peace_Index/tablesh2")
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
    
    infobox = requests.get("http://192.168.0.192:3600/wiki/" + country + "/infobox")
    coords = requests.get("http://192.168.0.192:3600/wiki/" + country + "/coords")

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
    lifeExpRequest = requests.get("http://192.168.0.192:3600/wiki/List_of_countries_by_life_expectancy/tablesh2")
    lifeExp = json.loads(lifeExpRequest.text)
    leCountries = lifeExp["List by the World Health Organization (2019)[edit]"]
    for leCountry in leCountries:
        if leCountry[0].replace("_", " ") == country:
            leBirth = leCountry[11] + "%"
            le60 = leCountry[15] + "%"
    
    
    found = False
    natDisRisk = ""
    natDisRiskResults = requests.get("http://192.168.0.192:3600/wiki/List_of_countries_by_natural_disaster_risk/tables")
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
    globPeaceResults = requests.get("http://192.168.0.192:3600/wiki/Global_Peace_Index/tablesh2")
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

    return countryStats


# Get Paragraphs for a Title
@app.route('/wiki/<title>')
def wikiparas(title):
    headerText = ""
    sections = {}
    count = 0
    nonAllowed = ["Bibliography", "General references", "Citations", "Contents", "Navigation menu", "Notes", "References", "See also", "External links"]
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
    divs = soup.find('div', class_="mw-parser-output")
    divs = str(divs)

    pastTable = False
    
    startIndex = divs.find('</table>\n<p>') + 8
    endIndex = divs.find(r'<div aria-')
    newText = divs[startIndex:endIndex]
    regex = re.compile('[.\d*.]')
    soup2 = BeautifulSoup(newText, 'html.parser')
    introText = soup2.text
    introText = introText.strip()
    #introText = introText.replace(regex.pattern, '')

    sections.update({"Intro":introText})

    # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Comment from user Zroq on May 15, 2017 on how to get next elements
    for header in soup.find_all('h2'):
        paras = ""
        hName = header.text
        if header.text.find("edit") != -1:
                end = header.text.find('[')
                hName = header.text[:end]
        if hName not in nonAllowed:
            nextElement = header
            while True:
                nextElement = nextElement.nextSibling
                if nextElement is None:
                    break
                if isinstance(nextElement, NavigableString):
                    paras += nextElement.strip()
                if isinstance(nextElement, Tag):
                    if nextElement.name == 'h2':
                        break
                    paras +=nextElement.get_text(strip=True).strip()
                sections.update({hName:paras})
                count += 1
    return sections

# Get Paragraphs for a Title
@app.route('/wiki/<title>/<section>')
def wikisection(title, section):
    headerText = ""
    sections = {}
    count = 0
    #nonAllowed = ["Bibliography", "General references", "Citations", "Contents", "Navigation menu", "Notes", "References", "See also", "External links"]
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
    section = section.lower()
    print(section)
    if section == "intro":
        divs = soup.find('div', class_="mw-parser-output")
        divs = str(divs)

        pastTable = False
        
        
        startIndex = divs.find('</table>\n<p>') + 8
        endIndex = divs.find(r'<div aria-')
        newText = divs[startIndex:endIndex]
        regex = re.compile('[.\d*.]')
        soup2 = BeautifulSoup(newText, 'html.parser')
        introText = soup2.text
        introText = introText.strip()
        #introText = introText.replace(regex.pattern, '')

        sections.update({"Intro":introText})
    else:
        print("In else")
        done = False
        for header in soup.find_all('h2'):
            
            paras = ""
            hName = header.text.lower()
            print(hName)
            print("Section: ", section)
            if hName == section:
                if header.text.find("edit") != -1:
                        end = header.text.find('[')
                        hName = header.text[:end]
                
                nextElement = header
                while True:
                    nextElement = nextElement.nextSibling
                    if nextElement is None:
                         break
                    #if isinstance(nextElement, NavigableString):
                        
                    #     paras += nextElement.strip()
                    if isinstance(nextElement, Tag):
                        if nextElement.name == 'h2':
                            done = True
                            print("Next element: ", nextElement.name)
                            break
                        paras +=nextElement.get_text(strip=True).strip()
            if done:
                break    
        sections.update({header.text:paras})
        count += 1
               
    return sections


# Get all in-page tables for a title
@app.route('/wiki/<title>/tables')
def wikitables(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')

     # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Comment from user Zroq on May 15, 2017 on how to get next elements
    for header in soup.find_all('h3'):            
        nextElement = header
        while True:
            nextElement = nextElement.nextSibling
            if nextElement is None:
                break
            if isinstance(nextElement, Tag):
                if nextElement.name == "h3":
                    break
                if nextElement.name == 'table':
                    tableRows = []
                    
                    t_headers = nextElement.find_all('th')
                    if t_headers is not None:
                        row = []
                        for th in t_headers:
                            
                            txt = unicodedata.normalize('NFC', th.get_text())
                            txt = txt.replace('\xa0', '')
                            txt = txt.replace(u'\u2013', u'-')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row and len(row) < 100:
                            tableRows.append(row)
                    t_rows = nextElement.find_all('tr')
                    
                    for tr in t_rows:
                        td = tr.find_all('td')
                        row = []
                        for i in td: 
                            txt = unicodedata.normalize('NFC', i.text)
                            txt = txt.replace('\xa0', '')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row and len(row) < 100:
                            tableRows.append(row)
                    tableDict.update({header.text:tableRows})
                    break
    return tableDict
# Get all in-page tables for a title
@app.route('/wiki/<title>/tablesNoH')
def wikitablesNoH(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')

    tableRows = []
    table = soup.find('table')               
    t_headers = table.find_all('th')
    if t_headers is not None:
        row = []
        for th in t_headers:            
            txt = unicodedata.normalize('NFC', th.get_text())
            txt = txt.replace('\xa0', '')
            txt = txt.replace(u'\u2013', u'-')
            txt = txt.strip()
            if len(txt) > 0 and len(txt) < 100:
                row.append(txt)
        if row and len(row) < 100:
            tableRows.append(row)
    t_rows = table.find_all('tr')
                    
    for tr in t_rows:
        td = tr.find_all('td')
        row = []
        for i in td: 
            txt = unicodedata.normalize('NFC', i.text)
            txt = txt.replace('\xa0', '')
            txt = txt.strip()
            if len(txt) > 0 and len(txt) < 100:
                row.append(txt)
        if row and len(row) < 100:
            tableRows.append(row)
    #tableDict.update({:tableRows})

    return jsonify(tableRows)

# Get all in-page tables for a title
@app.route('/wiki/<title>/tablesh2')
def wikitablesh2(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
     # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Comment from user Zroq on May 15, 2017 on how to get next elements
    for header in soup.find_all('h2'):
        nextElement = header
        while True:
            nextElement = nextElement.nextSibling
            if nextElement is None:
                break
            if isinstance(nextElement, Tag):
                if nextElement.name == "h2":
                    break
                if nextElement.name == 'table':
                    tableRows = []
                    
                    t_headers = nextElement.find_all('th')
                    if t_headers is not None:
                        row = []
                        for th in t_headers:
                            
                            txt = unicodedata.normalize('NFC', th.get_text())
                            txt = txt.replace('\xa0', '')
                            txt = txt.replace(u'\u2013', u'-')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row and len(row) < 100:
                            tableRows.append(row)
                    t_rows = nextElement.find_all('tr')
                    
                    for tr in t_rows:
                        td = tr.find_all('td')
                        row = []
                        for i in td: 
                            txt = unicodedata.normalize('NFC', i.text)
                            txt = txt.replace('\xa0', '')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row and len(row) < 100:
                            tableRows.append(row)
                    tableDict.update({header.text:tableRows})
                    break
    return tableDict

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3600)


