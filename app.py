# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import datetime, random, json
from bs4 import BeautifulSoup
import requests
import re




# create the application object
app = Flask(__name__)




#app.config['SERVER_NAME'] = 'http://dogwater.org:5000'


# UPDATE: changed parser from lxml to html.parser

@app.route('/wiki/<title>/<section>')
def wiki(title, section):
    text = "" + section
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    for para in soup.find_all('p'):
        text += para.text
    #global stud_name
    return text

@app.route('/wiki/<title>/infobox', methods=["GET"])
def wikibox(title):

    
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    text = ''
    #items = []
    regex = re.compile('infobox.*')
    for info in soup.find('table', {"class":regex}):
        for data in info.find_all('tr'):
            #text += info.text
            #text += "\n"
            dataStr = data.text.replace('\xa0', ' ')
            dataStr = dataStr.replace('\n',' ')
            dataStr = dataStr.replace('\ufeff',' ')
            #items.append(dataStr)
            text += dataStr
        #text += "\n"
    response = jsonify(text)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return text
    #return json.dumps(items)

@app.route('/wiki/<title>/table/<identifier>')
def wikitable(title, identifier):
    tableStuff = ""
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    
    for stuff in soup.find_all('table', {"class":identifier}):
        tableStuff += stuff.get_text()
    

    return tableStuff

@app.route('/wiki/<title>/table')
def wikitable2(title):
    tableStuff = ""
    site = requests.get('https://en.wikipedia.org/wiki/' + title)
    soup = BeautifulSoup(site.content, 'html.parser')
    tableList = []
 
    for stuff in soup.find_all('table'):
        #tableStuff += stuff.get_text()
        tableList.append(stuff.get_text())
    return json.dumps(tableList)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
