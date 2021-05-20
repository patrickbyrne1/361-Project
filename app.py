# import the Flask class from the flask module
from typing import Text
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
import datetime, random, json
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re
import unicodedata
import codecs


from flask_cors import CORS, cross_origin

# create the application object
app = Flask(__name__)
CORS(app, support_credentials=True)


# Helper Functions
# lat and lon are text string
def convertCoords(aCoord):
    coordsList = re.findall(r'\d+', aCoord)
    print(coordsList)
    #lonCoordsList = re.findall(r'\d+', aCoord)
    degCoord = coordsList[0]
    degCoord = float(degCoord)
    if len(coordsList) >= 2:
        minute = format(int(coordsList[1])/60, '.3f')
        degCoord += float(minute)
    if len(coordsList) >= 3:
        second = format(int(coordsList[2])/3600, '.5f')
        degCoord += float(second)
    # look at last character to determine N, S, E, or W
    direction = aCoord[len(aCoord) - 1]    
    print(type(degCoord))
    if direction.lower() == 's' or direction.lower() == 'w':
        degCoord *= -1
        print("Degree coords", degCoord)
    # convert back to string and return
    return str(format(degCoord, '.4f'))

# find intro paragraph of page
def intro(soup):
    afterInfobox = False
    introText = ""
    #regex = re.compile('infobox.*')
    print(soup.find('table', class_="infobox"))
    
    for divs in soup.find('div', class_="mw-parser-output"):
        if isinstance(divs, Tag):
            if divs.get('id') == 'toc':
                done = True
                break
                
            nextElement = divs
            while True:
                if nextElement.nextSibling != None:
                    nextElement = nextElement.nextSibling
                else:
                    break
                if isinstance(nextElement, Tag):              
                    # citation: https://stackoverflow.com/questions/21592012/extract-class-name-from-tag-beautifulsoup-python/21592363
                    # used ideas on this page to find an element by its class
                    # element attributes contained in dictionary form
                    if nextElement.name == "table" and nextElement.has_attr('class'): #and nextElement.class ==::     
                        print(nextElement["class"][0])      
                        afterInfobox = True
                    if nextElement.name == "h2":
                        done = True
                        break
                    if nextElement.name == 'p' and (afterInfobox or soup.find('table', class_="infobox") == None):
                        introText += nextElement.text
                        introText = introText.strip()
        if done:
            break
    return introText



# Get Paragraphs for a Title
@app.route('/wiki/<title>')
def wikiparas(title):
    headerText = ""
    sections = {}
    count = 0
    nonAllowed = ["Bibliography", "Further reading", "General references", "Citations", "Contents", "Navigation menu", "Notes", "References", "See also", "External links"]
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)

    # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Based on the example shown from user Zroq on May 15, 2017 on how to get next elements
    
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)
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
    return make_response(jsonify(sections), 200)
    

# Get Paragraphs for a Title
@app.route('/wiki/<title>/<section>')
def wikisection(title, section):

    sections = {}
    #nonAllowed = ["Bibliography", "General references", "Citations", "Contents", "Navigation menu", "Notes", "References", "See also", "External links"]
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    if soup.find('div', class_="mw-parser-output") == None:
        #"Page not found. Please check that the title was entered correctly."
        return make_response(jsonify(Error="No page exists with that title."), 404)
    section = section.lower()
    done = False
     # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Based on the example shown from user Zroq on May 15, 2017 on how to get next elements
    if section == "intro":     
        introText = intro(soup)
        if len(introText) == 0:
            # Multiple options found (ambiguity).  Please enter a more specific title.
            return make_response(jsonify(Error="More than one page exists with that title."), 300)
        sections.update({"Intro":introText})
    else:
        isFound = False
        hName = ""
        for header in soup.find_all('h2'):   
            paras = ""
            hName = header.text
            print("hName: ", hName)
            print("section: ", section)
            if header.text.find("edit") != -1:
                    end = header.text.find('[')
                    hName = header.text[:end]
                    print("New name: " , hName)
            if hName.lower() == section:
                isFound = True
                nextElement = header
                while True:
                    nextElement = nextElement.nextSibling
                    if nextElement is None:
                         break
                    if isinstance(nextElement, Tag):
                        if nextElement.name == 'h2':
                            done = True
                            break
                        if nextElement.name == 'p':
                            paras +=nextElement.text #get_text(strip=True).strip()
                            paras = paras.strip()
            #else:
            #    return make_response(jsonify(Error="No section exists on this page."), 404)
            if done:
                break    
        if not isFound:
            return make_response(jsonify(Error="No section with that name exists on this page."), 400)
        sections.update({hName:paras})
    return make_response(jsonify(sections), 200)


# Get coordinates for a place
@app.route('/wiki/<title>/coords')
def coords(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    # check if page exists
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)
    
    # check for ambiguity
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)

    # check if it contains latitude/longitude
    latitude = soup.find('span', class_='latitude')
    longitude = soup.find('span', class_='longitude')
    if latitude is None or longitude is None:
        return make_response(jsonify(Error="This page does not contain coordinates."), 400)
    latitude = latitude.text   
    longitude = longitude.text
    latitude = unicodedata.normalize('NFC', latitude)
    longitude = unicodedata.normalize('NFC', longitude)
    lat = convertCoords(latitude)
    lon = convertCoords(longitude)
    coord_object = {
        "latitude":latitude,
        "longitude":longitude,
        "lat": lat,
        "lon": lon
    }
    return make_response(jsonify(coord_object), 200)
    

# Get Infobox Data
@app.route('/wiki/<title>/infobox')
def wikibox(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    # check if page exists
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)
    
    # check for ambiguity
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)
    
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
    if len(items) == 0:
        return make_response(jsonify(Error="This page does not contain an infobox."), 400)
    return make_response(jsonify(items), 200)



# Get h3 in-page tables for a title 
@app.route('/wiki/<title>/tables')
def wikitables(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    # check if page exists
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)
    
    # check for ambiguity
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)

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
    if len(tableDict) == 0:
        return make_response(jsonify(Error="This page does not contain tables under h3 headers."), 400)
    return make_response(jsonify(tableDict), 200)

# Get all in-page tables without headers for a given title
@app.route('/wiki/<title>/tablesNoH')
def wikitablesNoH(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)
    
    # check for ambiguity
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)

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
    if len(tableRows) == 0: 
        return make_response(jsonify(Error="This page does not contain tables without h3 or h2 headers."), 400)
    return make_response(jsonify(tableRows, 200))


# Get h2 in-page tables for a title
@app.route('/wiki/<title>/tablesh2')
def wikitablesh2(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    if soup.find('div', class_="mw-parser-output") == None:
        return make_response(jsonify(Error="No page exists with that title."), 404)
    
    # check for ambiguity
    introText = intro(soup)
    if len(introText) == 0:
        return make_response(jsonify(Error="More than one page exists with that title."), 300)

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
    if len(tableDict) == 0: 
        return make_response(jsonify(Error="This page does not contain tables under h2 headers."), 400)
    return make_response(jsonify(tableDict), 200)




#if __name__ == "__main__":
#    app.run(debug=True, host="0.0.0.0", port=4500)


