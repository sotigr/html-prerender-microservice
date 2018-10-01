#python -m flask run

#pip install pymongo
#pip install Flask
#pip install selenium
 
from flask import Flask, request
from selenium import webdriver  
from bson import json_util
import sys, os, time, json
import datetime

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

pathname = os.path.dirname(sys.argv[0])
fullpath = os.path.abspath(pathname)
 
driver = webdriver.Chrome(fullpath + "/chromedriver", chrome_options=chrome_options)

app = Flask(__name__)
cache_file = "cache.json" 


def SaveCache(cache): 
    if not os.path.exists("cache"):
        os.makedirs("cache")

    if os.path.isfile(cache_file):
        os.remove(cache_file)

    with open(cache_file, 'a') as out:
        out.write(json.dumps(cache, default=json_util.default))

def InitCache():
    print("init cache")
    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as cache_string:
            return json.loads(cache_string.read(), object_hook=json_util.object_hook)
    else:
        SaveCache({})
        return {}
 
cache = InitCache()
 

    

def CreateFileSavePath(location):

    return "cache/" + location.replace("/", "").replace(":", "") + ".html"


def RefreshCache(location, request_timeout):

    save_path = CreateFileSavePath(location)
    cache[location] = {
        "path": save_path,
        "timeout": datetime.datetime.now() + datetime.timedelta(days=3),
        "request_timeout": request_timeout
    }
    
    
    driver.get(location)

    time.sleep(request_timeout)
	
    data = driver.page_source.encode('utf-8-sig')

    if os.path.isfile(save_path):
        os.remove(save_path)

    with open(save_path, 'bw') as out:
        out.write(data)

    SaveCache(cache)
    
    return data
    
def GetFromCache(location):

    cache_entry = cache[location]

    with open(cache_entry["path"], 'r') as cache_html:
        html = cache_html.read()
    
    return html

def HasTimedOut(cacheItem):  
    return cacheItem["timeout"].replace(tzinfo=None) < datetime.datetime.now()

def HandleLocation(location, timeout):
    
    if location in cache:
        if HasTimedOut(cache[location]):
            html = RefreshCache(location, timeout)
        else:
            html = GetFromCache(location)
    else: 
        html = RefreshCache(location, timeout)

    return html

@app.route("/render",  methods=['GET'])
def render():
    try:
        location_path = request.args.get('page')
    except Exception as e:
        return "specify page: example: ?page=http://...&timeout=5"

    try:
        timeout = int(request.args.get('timeout'))
    except Exception as e:
        return "specify timeout: example: ?page=http://...&timeout=5"

    return HandleLocation(location_path, timeout)
  
if __name__ == "__main__":
    
    app.run(host="127.0.0.1", port=5123, debug=False)
