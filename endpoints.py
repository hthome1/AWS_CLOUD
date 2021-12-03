
import requests
import json
import datetime
import sys
from client import Client


nome_LB = "LBApplication"

clienteDNS = Client("us-east-1")
resp = clienteDNS.clientLB.describe_load_balancers(Names=[nome_LB])
DNS = resp['LoadBalancers'][0]['DNSName']




urlLB ="http://" + DNS +"/tasks/"


data = str(datetime.datetime.now())


#print(sys.argv)

line = sys.argv



if(len(line) == 2):
    comand = line[1]
else:
    comand = line[1]
    title = line[2]
    description = line[3] 


if comand == "GET" :
    r = requests.get(urlLB + "allTasks")
    print(r.text)

if comand == "DELETE" :
    r = requests.delete(urlLB + "delete")
    print(r.text)


if comand == "POST":
    payload = {
        "title":title,
        "pub_date":data,
        "description":description
    }
    r = requests.post(urlLB + "add", data=json.dumps(payload))
    print(r.text)

