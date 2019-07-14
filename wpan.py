#!/usr/bin/env python3
""" Worskpot PAN User-ID integration """
####################################
# Worskpot PAN User-ID integration #
####################################

import sys, base64, requests, json, asyncio, logging
from aiohttp import ClientSession

# Variable initialization #
URL = "https://api.workspot.com/v1.0/pools"

# Logging setup #

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(sys.argv[0])
logging.getLogger("chardet.charsetprober").disabled = True

############################  

async def workspot(url,headers):
    """ Calling Workspot API `url` with authorization `headers`"""
    async with ClientSession() as session:
        async with session.get(url,headers=headers) as response:
            logger.info("--->Got response [%s] for url: %s", response.status, url)
            response = await response.read()            
            return response

def get_token():
    """ Get authorization token from Workspot API """
    with open("config.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            logger.info(f"--->{config}")
        except yaml.YAMLError as exc:
            logger.err(f"--->{exc}")
    ApiClientPair = config[0]["ApiClientId"] + ':' + config[1]["ApiClientSecret"]
    EncodedApiCreds = base64.b64encode(ApiClientPair.encode('ascii'))
    HeaderAuthValue = b"Basic " + EncodedApiCreds
    Headers = { 'Authorization': '{}'.format(HeaderAuthValue.decode('ascii'))}
    logger.info("-->>Authorization [%s]", Headers["Authorization"])
    url = "https://api.workspot.com/oauth/token" #?grant_type=password
    payload = { # "Content-Type": "x-www-form-urlencoded", grant_type": 'password', "grant_type": 'client_credentials'
        'username': config[2]["WsControlUser"],
        'password': config[3]["WsControlPass"],
        'Content-Type': 'x-www-form-urlencoded',
        'grant_type': 'password'
        }   
    ApiReturn = requests.post(url, data=payload, headers=Headers) #,auth=HTTPBasicAuth(WsControlUser, WsControlPass)
    ApiToken = json.loads(ApiReturn.content)["access_token"]
    logger.info("--->Got token [%s]", ApiToken)
    return { "Authorization": ("Bearer "+ ApiToken), 'Content-Type': 'application/json'}

def get_pools(j):
    """ Parse desktop pools id """
    logger.info("--->desktopPools:")
    id = []
    for i in j["desktopPools"]:
        logger.info(('--->{0:<20} {1:<3} {2:<20} {3:<30}'.format(i["name"],i["usedCount"],i["description"],i["id"])))
        id.append(i["id"])
    return id 

def get_desktops(j):
    """ Parse user email and ip address  """
    logger.debug("--->desktops:")
    userid = []
    for i in j["desktops"]:
        if i["email"]:
            logger.debug(('--->{0:<20} {1:<3} {2:<20} {3:<30}'.format(i["name"],i["email"],i["ipAddress"],i["status"])))
            userid.append(("Workspot_"+i["poolName"]+ "\\" + i["email"], i["ipAddress"]))
    return userid    
    
async def main(url, Headers): 
    #res = await asyncio.gather(workspot(url, Headers))  
    res = await asyncio.gather(*(workspot(url, Headers) for url in urls))
    return res 
    
if __name__ == "__main__":
    import time, yaml
    from itertools import chain

    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
    Headers = get_token()
    urls = [URL]
    start = time.perf_counter()
    r = asyncio.run(main(urls, Headers))
    id = list(chain.from_iterable([get_pools(json.loads(j)) for j in r])) # flatten list
    logger.info(f"--->{id}")
    userid = []
    urls.pop(0) 
    #sys.exit(0)
    [urls.append(URL+'/'+i+'/desktops') for i in id]   
    r = asyncio.run(main(urls, Headers))    
        #r = asyncio.run(main(url+'/'+i+'/desktops', Headers))
    userid.append(list(chain.from_iterable([get_desktops(json.loads(j)) for j in r])))    
    logger.info(f"--->{userid}")
    end = time.perf_counter() - start
    logger.info(f"--->finished in {end:0.2f} seconds.")
    
   
                
