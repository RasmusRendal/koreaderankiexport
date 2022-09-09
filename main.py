import sqlite3
import json
import requests
import re
import hashlib
import os
import csv

url = "https://en.wiktionary.org/w/api.php?action=query&prop=revisions&titles=QUERY&rvslots=*&rvprop=content&formatversion=2&format=json"

def raw_query(query):
    """Returns the german wiktionary entry as text"""
    wiktionary = requests.get(url.replace("QUERY", query)).json()
    pages = wiktionary["query"]["pages"]
    if len(pages) < 1:
        return ""
    content = pages[0]["revisions"][0]["slots"]["main"]["content"]
    gstart = content.find("==German==")
    if gstart < 0:
        return ""
    content = content[gstart+12:]
    x = re.search("\n==[A-Z]", content)
    if x != None:
        content = content[:x.start()]
    return content


def get_pronounciation(content):
    x = re.search("{{audio\|de\|(([^\W\d_]|[-.])+)\|Audio}}", content)
    if x == None:
        print("No pronounciation found")
        return ""
    filename = x.group(1)
    digest = hashlib.md5(filename.encode()).hexdigest()
    url = "https://upload.wikimedia.org/wikipedia/commons/" + digest[0] + "/" + digest[0:2] + "/" + filename
    output = "/home/rendal/.local/share/Anki2/User 1/collection.media/" + filename
    if not os.path.exists(output):
        sound = requests.get(url)
        open(output, 'wb').write(sound.content)
        print("Downloaded sound file")
    return "[sound:" + filename + "]"


def get_root(content):
    x = re.search("{{[a-z]+ form of\|de\|([^\W\d_]+)\|", content)
    if x == None:
        return content
    else:
        return raw_query(x.group(1))

def query_wiktionary(word):
    content = raw_query(word)
    pronounciation = get_pronounciation(content)
    return get_root(content), pronounciation


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


if __name__ == "__main__":
    con = sqlite3.connect("/tmp/vocabulary_builder.sqlite3")
    cur = con.cursor()
    output = []
    for word, prev_context, next_context in cur.execute("SELECT word, prev_context, next_context FROM vocabulary;"):
        while ". " in prev_context:
            prev_context = prev_context[prev_context.find(". ")+2:]
        while ". " in next_context:
            next_context = next_context[:next_context.find(". ")+1]

        definition, pronounciation = query_wiktionary(word)
        print(definition)
        print("")

        sentence = prev_context + word + next_context
        print(prev_context + color.BLUE + word + color.END + next_context)
        translation = input("Write translation: ")
        row = (word, sentence, translation, pronounciation)
        output.append(row)

    with open('output.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            for row in output:
                writer.writerow(row)