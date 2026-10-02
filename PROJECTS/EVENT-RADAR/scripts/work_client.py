#!/usr/bin/env python3
"""A thin API client, usable by Work's authorized execution environment or future MCP.
No database copy, cache, chat history or credential output.
"""
import argparse,os,json,urllib.request,urllib.parse
p=argparse.ArgumentParser();p.add_argument('--operator',action='store_true');p.add_argument('--filter',action='append',default=[]);a=p.parse_args()
base=os.environ.get('EVENT_RADAR_API_URL')
if not base:raise SystemExit('STATE NOT LOADED: EVENT_RADAR_API_URL unavailable')
params=dict(item.split('=',1) for item in a.filter)
path='/api/v1/operator/events' if a.operator else '/api/v1/events'
headers={}
if a.operator:
 token=os.environ.get('RADAR_OPERATOR_TOKEN')
 if not token:raise SystemExit('STATE NOT LOADED: operator authorization unavailable')
 headers['Authorization']='Bearer '+token
request=urllib.request.Request(base.rstrip('/')+path+'?'+urllib.parse.urlencode(params),headers=headers)
try:
 with urllib.request.urlopen(request,timeout=15) as response:print(json.dumps(json.load(response),ensure_ascii=False))
except Exception as e:raise SystemExit('STATE NOT LOADED: Event Radar API request failed ('+type(e).__name__+')')
