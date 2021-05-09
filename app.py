# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, make_response
import datetime, random, json
from bs4 import BeautifulSoup
import requests
import re
import unicodedata

from flask_cors import CORS



# create the application object
app = Flask(__name__)
CORS(app)



#app.config['SERVER_NAME'] = 'http://dogwater.org:5000'


# UPDATE: changed parser from lxml to html.parser

# Get coordinates for a place
@app.route('/wiki/<title>/coords')
def coords(title):
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    
    latitude = soup.find('span', class_='latitude').text
    longitude = soup.find('span', class_='longitude').
    if latitude is None or longitude is None:
        return make_response(jsonify(Error="No coordinates found."), 404)

    coord_object = {
        "latitude":latitude,
        "longitude":longitude
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
    for header in soup.find_all('h2'):
        paras = ""
        hName = header.text
        if header.text.find("edit") != -1:
                end = header.text.find('[')
                hName = header.text[:end]
        if hName not in nonAllowed:
            nextNode = header
            while True:
                nextNode = nextNode.nextSibling
                if nextNode is None:
                    break
                if isinstance(nextNode, NavigableString):
                    paras += nextNode.strip()
                if isinstance(nextNode, Tag):
                    if nextNode.name == 'h2':
                        break
                    paras += nextNode.get_text(strip=True).strip()
                sections.update({hName:paras})
                count += 1
    return sections


# Get all in-page tables for a title
@app.route('/wiki/<title>/tables')
def wikitables(title):
    tableDict = {}

    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'lxml')
    for header in soup.find_all('h3'):
            
        nextNode = header
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                break
            if isinstance(nextNode, Tag):
                if nextNode.name == "h3":
                    break
                if nextNode.name == 'table':
                    tableRows = []
                    
                    t_headers = nextNode.find_all('th')
                    if t_headers is not None:
                        row = []
                        for th in t_headers:
                            
                            txt = unicodedata.normalize('NFC', th.get_text())
                            txt = txt.replace('\xa0', '')
                            txt = txt.replace(u'\u2013', u'-')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row:
                            tableRows.append(row)
                    t_rows = nextNode.find_all('tr')
                    
                    for tr in t_rows:
                        td = tr.find_all('td')
                        row = []
                        for i in td: 
                            txt = unicodedata.normalize('NFC', i.text)
                            txt = txt.replace('\xa0', '')
                            txt = txt.strip()
                            if len(txt) > 0 and len(txt) < 100:
                                row.append(txt)
                        if row:
                            tableRows.append(row)
                    tableDict.update({header.text:tableRows})
                    break
    return tableDict


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



#if __name__ == "__main__":
#    app.run(host="0.0.0.0")