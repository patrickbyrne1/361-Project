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


# helper functions
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


# Get Infobox Data
@app.route('/wiki/<title>/infobox')
def wikibox(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
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
    lat = convertCoords(latitude)
    lon = convertCoords(longitude)
    coord_object = {
        "latitude":latitude,
        "longitude":longitude,
        "lat": lat,
        "lon": lon
    }
    return make_response(jsonify(coord_object), 200)
    
# Get Paragraphs for a Title
@app.route('/wiki/<title>')
def wikiparas(title):
    headerText = ""
    sections = {}
    count = 0
    nonAllowed = ["Bibliography", "General references", "Citations", "Contents", "Navigation menu", "Notes", "References", "See also", "External links"]
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
    done = False
    introText = ""
    # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Based on the example shown from user Zroq on May 15, 2017 on how to get next elements
    for divs in soup.find('div', class_="mw-parser-output"):
        if isinstance(divs, Tag):
            print("It's a div!")
            if divs.get('id') == 'toc':
                print("FUDGE THESE TITS")
                done = True
                break
            #divs = soup.find('div', class_="mw-parser-output")
            nextElement = divs
            while True:
                if nextElement.nextSibling != None:
                    nextElement = nextElement.nextSibling
                else:
                    break
                if isinstance(nextElement, Tag):
                    if nextElement.name == "h2":
                        done = True
                        break
                    if nextElement.name == 'p':
                        print(nextElement)
                        introText += nextElement.text
                        introText = introText.strip()       
        if done:
            break
    
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

# Get Paragraphs from a specific section of a Title
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
    introText = ""
    done = False
     # citation: https://stackoverflow.com/questions/42820342/get-text-in-between-two-h2-headers-using-beautifulsoup
    # Based on the example shown from user Zroq on May 15, 2017 on how to get next elements
    if section.lower() == "intro":
        print("In if")
        done = False
        for divs in soup.find('div', class_="mw-parser-output"):
            if isinstance(divs, Tag):
                print("It's a div!")
                if divs.get('id') == 'toc':
                    print("FUDGE THESE TITS")
                    done = True
                    break
                #divs = soup.find('div', class_="mw-parser-output")
                nextElement = divs
                while True:
                    if nextElement.nextSibling != None:
                        nextElement = nextElement.nextSibling
                    else:
                        break
                    if isinstance(nextElement, Tag):
                        if nextElement.name == "h2":
                            done = True
                            break
                        if nextElement.name == 'p':
                            print(nextElement)
                            introText += nextElement.text
                            introText = introText.strip()
                        #for paras in divs.find_all('p', recursive=False):
                        #    introText += paras.text
                        #    introText = introText.strip()
            if done:
                break
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
    soup = BeautifulSoup(site.content, 'html.parser')

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
    soup = BeautifulSoup(site.content, 'html.parser')

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
    soup = BeautifulSoup(site.content, 'html.parser')
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
