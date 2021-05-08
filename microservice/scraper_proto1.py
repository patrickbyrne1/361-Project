from bs4 import BeautifulSoup
from flask import Flask
import requests, re
import pandas as pd



def menu():
    choice = input("""
1. Get the entire article
2. Get the intro text to an article
3. Get the contents of a table (such as infobox)
4. Get the contents of a list
5. Get the coordinates to a place
6. Get the population of a place
""")
    return choice


place = input("Enter a place")
wiki = "https://en.wikipedia.org/wiki/"


res = requests.get(wiki + place)
#print(res)
resText = res.text

soup = BeautifulSoup(resText, 'lxml')
#output = soup.get_text()
#for row in output.splitlines():
    #if row.find("toc")



choice = menu()



# class is a special keyword in python so you
# need to put an underscore after the name here



match = set()

# To find all elements on the page
#for text in soup.find_all(text=True):
#    match.add(text.parent.name)
#print(match)

# Find paragraph info
text = ''
count=0
content = ''
#for tags in soup.find_all('div', {"class":"mw-parser-output"}):
#    content += tags.text
#    print(tags.text)

if choice == '1':
    for paras in soup.find_all('p'): #, id_='See-also')
        print(paras.text)

elif choice == '2':
    divs = soup.find('div', class_="mw-parser-output")
    divs = str(divs)
    #print(divs)
    # count intro paragraph divs.  They do not have any class or id.
    count = 0
    pastTable = False
    
    startIndex = divs.find('</table>\n<p>') + 8
    endIndex = divs.find(r'id="toc"')
    newText = divs[startIndex:endIndex]
    #print(newText)
    soup2 = BeautifulSoup(newText, 'lxml')
    print(soup2.text)
    

    """
    for ch in range(len(divs)):
        #newChar = divs[ch] + divs[ch+1] + divs[ch+2]
        #print(newChar)
        
        if divs[ch:ch+8]== r'</table>':
            print("POOP")
            pastTable = True
        if divs[ch] + divs[ch+1] + divs[ch+2] == '<p>' and pastTable:
            count +=1
            print(count)
        if divs[ch] + divs[ch+1] + divs[ch+2] + divs[ch+3] + divs[ch+4] + divs[ch+5] + divs[ch+6]== r'id="toc':
            print("****************************")
            break
    print(count)
    for paras in soup.find_all('p', limit=count+1): #, limit=count):
        print(paras.get_text())
    """

elif choice == '3':
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
        #text += "\n"
    print(items)
    

elif choice == '4':
    stuff = soup.find('table', {'class':'toccolours'})
    #dataf = pd.read_html(str(stuff))
    #dataf=pd.DataFrame(dataf[0])
    #print(dataf.head())
    print(stuff.text)
    

elif choice == '5':
    latitude = soup.find('span', class_='latitude').text
    longitude = soup.find('span', class_='longitude').text
    print()
    print(f"GPS Coordinates of {place}\nLatitude: {latitude} Longitude: {longitude}")
    print()



elif choice == '6':
    # grab information from page infobox
    text = ''
    regex = re.compile('infobox.*')
    for info in soup.find('table', {"class":regex}):
        text += info.text
        #print(info.text)
        #print("\n\nNext Line\n\n")

    popText = ''
    pop = text.find("Population")
    #print(pop)
    if pop != -1:
        pattern = re.compile(r'\d{0,3},*\d{0,3},*\d{0,3},\d{1,3}')
        matches = pattern.finditer(text[pop+12:])
        print(f"Population: {matches.__next__().group()}")



elif choice == '7':
    tableStuff = ""
    for stuff in soup.find_all('table', {"class":"toccolours"}):
        tableStuff += stuff.get_text()
    print(tableStuff)
#coords = ''
#for match in matches:
#    print(f"Population: {match.group()}")
#print(type(matches))
#for match in matches:
    #print(match)
#print(matches[0].group())

#if pop != -1:
#    esti = text.find("estimate", pop)
#    endPop = text.find("[", esti)
    #endPop = text.find(, pop)  
#    popText = text[(esti + 9):endPop]
#print("Population is: ", popText)
#print("Population: ", popText)
#infoList = text.split('\n')
#print(len(infoList))
#for line in infoList:
#    print(line)



#print(soup.prettify())

#paraList = soup.select('p')

#listList = soup.select('li')

#for x in listList:
    
#    print(x.getText())

print("Done!")
