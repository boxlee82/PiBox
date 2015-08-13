import sys, subprocess
import hashlib
import os
import urllib, urllib2
import hashlib
import socket

class TTS :

	timeout = 10

	def getAppId(self):
		try:
			version = "222083"
			f = urllib2.urlopen("http://www.bing.com/translator/?mkt=zh-CN") 
			t = f.headers["Content-type"]
			if t.startswith("text/html;"):
			    data = f.read() 
			    start = data.find("/static/") + 8 
			    end = data.find("/js/", start) 
			    version = data[start:end]
			print version

			socket.setdefaulttimeout(self.timeout) # 10 秒钟后超时
			f = urllib2.urlopen("http://www.bing.com/translator/dynamic/" + version + "/js/LandingPage.js?loc=zh-CHS&phenabled=&rttenabled=&v=" + version)
			t = f.headers["Content-type"]
			if t.startswith("application/x-javascript"):
				data = f.read() 
				start = data.find('appId:"') + 7 
				end = data.find('",rttAppId:') 
				appid = data[start:end]
				print "bing appId: " + appid
				return appid
		except urllib2.HTTPError, e:
			print 'The server couldn\'t fulfill the request.'
			print 'Error code: ', e.code
			return ""
		except urllib2.URLError, e:
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
			return ""

	def getSpeech(self, phrase):
		#googleAPIurl = "http://tts.baidu.com/text2audio?lan=zh&pid=101&ie=UTF-8&spd=5&"
		#param={'text': phrase}
		googleAPIurl = "http://api.microsofttranslator.com/v2/http.svc/speak?language=zh-TW&format=audio/mp3&options=MinSize|female&"
		param={'text': phrase, 'appId': self.getAppId()}
		data = urllib.urlencode(param)
		googleAPIurl += data
		#Append the parameters
		return googleAPIurl

	def md5(self, str):
		m = hashlib.md5()   
		m.update(str)
		return m.hexdigest()

	def downloadSpeech(self, text, filename):
		url = self.getSpeech(text)  

		#urllib.urlretrieve(url, filename)

		try:
			socket.setdefaulttimeout(self.timeout) # 10 秒钟后超时
			f = urllib2.urlopen(url) 
			t = f.headers["Content-type"]
			if t.startswith("audio/"):
				data = f.read() 
				with open(filename, "wb") as code:     
					code.write(data)
				return filename
		except urllib2.HTTPError, e:
			print 'The server couldn\'t fulfill the request.'
			print 'Error code: ', e.code
			#return
		except urllib2.URLError, e:
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
			#return

		return os.path.split(os.path.realpath(__file__))[0] + "/tts.mp3"
		#return "Web_TTS/tts.mp3"
 
	def raspberryTalk(self, text):
		filename = os.path.split(os.path.realpath(__file__))[0] + "/cache/" + self.md5(text) + ".mp3"
		# filename = "Web_TTS/cache/" + self.md5(text) + ".mp3"

		if not os.path.exists(filename):
			filename = self.downloadSpeech(text, filename)

		# This will call mplayer and will play the sound
		# subprocess.call(["mplayer", getSpeech(text)], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		subprocess.call(["mplayer", filename], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	def alert(self):
		# This will call mplayer and will play the sound
		subprocess.call(["mplayer", os.path.split(os.path.realpath(__file__))[0] + "/alert.mp3"], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#raspberryTalk("现在时间 16 点整，周四。 温度：28℃，湿度：15%，气压：12933PAH，PM2.5：1.4 微克每立方米")
