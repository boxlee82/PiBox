# -*- coding: utf-8 -*-  

import sys, subprocess, urllib
import hashlib
import os
import urllib2

import json

from datetime import *  
import time  

# 标准化编码
reload(sys) 
sys.setdefaultencoding("utf-8")

class CAIYUN :

    # 是否有雨
    caiyun_rain = False
    # 是否有雨
    def getRain(self):
    	return self.caiyun_rain

    def getToken(self):
    	try:
    		req = urllib2.Request("http://caiyunapp.com/js/map.min.js");
    		req.add_header('Accept', 'application/javascript, */*;q=0.8');
    		req.add_header('Referer', 'http://caiyunapp.com/');
    		f = urllib2.urlopen(req);    
    
    		t = f.headers["Content-type"]
    		if t.startswith("application/javascript"):
    			data = f.read() 
    			start = data.find('&token=') + 7 
    			end = data.find('&random', start) 
    			token = data[start:end]
    			# print token
    			return token
    	except urllib2.HTTPError, e:
    		print 'The server couldn\'t fulfill the request.'
    		print 'Error code: ', e.code
    		return "12"
    	except urllib2.URLError, e:
    		print 'We failed to reach a server.'
    		print 'Reason: ', e.reason
    		return "12"
    	
    def getCaiyun(self, lonlat = '116.7261,23.3778'):
    	googleAPIurl = "http://caiyunapp.com/fcgi-bin/v1/api.py?format=json&product=minutes_prec&"
    	param = {'lonlat': lonlat, 'token': self.getToken()}
    	data = urllib.urlencode(param)
    	googleAPIurl += data
    	return googleAPIurl
    
    def getSummary(self, lonlat):
    	url = self.getCaiyun(lonlat)  
    
    	try:
    		f = urllib2.urlopen(url) 
    		t = f.headers["Content-type"]
    		if t.startswith("application/javascript;"):
    			data = f.read() 
    			json_list = json.loads(data)
    			
    			if json_list["status"] == "ok":
    			 summary = json_list["summary"].replace('还在加班么？注意休息哦', '').replace('，放心出门吧', '').replace('公里外呢', '公里外').replace('。', '')
			# 未来一小时每分钟的降雨量，0.05-0.15是小雨，0.15-0.35是中雨, 0.35以上是大雨，根据不同地区情况可以有所调整。
    			 dataseries = [x for x in json_list["dataseries"] if x > 0.05]
			# 判断是否有雨
    			 #  print (dataseries)
    			 if len(dataseries) == 0:
    			 	self.caiyun_rain = False
    			 else:
    			 	self.caiyun_rain = True
    			 #print json_list
    			 return summary 

    	except urllib2.HTTPError, e:
    		print 'The server couldn\'t fulfill the request.'
    		print 'Error code: ', e.code
    		#return
    	except urllib2.URLError, e:
    		print 'We failed to reach a server.'
    		print 'Reason: ', e.reason
    		#return
    
    	return ""