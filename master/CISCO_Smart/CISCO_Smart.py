# coding: utf-8

import httplib, urllib
import urllib2
import time
import json

# 思科无线路由，判断在线的移动设备
# 已实测 EA4200, EA4500, EA6500, EA6700

# 需要监控的 mac 地址列表
mac_list = [ ] # ['蔡总','CC:FA:00:F7:52:69',true,0], ['iphone','F0:CB:A1:00:77:EE',true,0] 

class CISCO :

	# 回调在线设备
	def online_devices(self, func):
		global mac_list

		# 判断指定编号的 MAC 是否在线
		params = "[{\"action\":\"http://linksys.com/jnap/devicelist/GetDevices\",\"request\":{\"sinceRevision\":23}},{\"action\":\"http://linksys.com/jnap/networkconnections/GetNetworkConnections\",\"request\":{}}]"
		request = urllib2.Request(url='http://192.168.1.1/JNAP/', data=params, headers={ "Content-type": "application/json; charset=UTF-8", "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction" })
	
		try:
			f = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			print 'The server couldn\'t fulfill the request.'
			print 'Error code: ', e.code
			return
		except urllib2.URLError, e:
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
			return
		else:
			# 如果没有引发异常
			t = f.headers["Content-type"]

			# 如果返回的是 json 文件证明是对的
			if t.startswith("application/json;"):
				data = f.read()

			# 解析返回的内容 思科路由器专用部分
			json_list = json.loads(data)
			if json_list["result"] == "OK":
				# 初始化列表
				# if len(mac_list) == 0:
				devices = [x for x in json_list["responses"][0]["output"]["devices"] if x["model"]["deviceType"] == "Mobile" or x["model"]["deviceType"] == "Phone"]
				for device in devices:
					knownMACAddresses = device["knownMACAddresses"][0]
					# 如果列表中存在记录
					in_list = [x for x in mac_list if x[1] == knownMACAddresses]
					if len(in_list) > 0:
						continue

					# 获取设备名称
					userDeviceName = False
					friendlyName = device["friendlyName"]		
					# 如果是存在别名的设备，到来的时候要拉响警报
					item = [x for x in device["properties"] if x["name"] == "userDeviceName"]
					if len(item) > 0:
						friendlyName = item[0]["value"]		
						userDeviceName = True		
					# 保存到设备列表
					# print friendlyName, device["knownMACAddresses"][0]
					mac_item = [ friendlyName, device["knownMACAddresses"][0], userDeviceName, -1 ] 
					mac_list.append(mac_item)

				# 查询 mac 列表里的在线状态
				for element in mac_list:
					mac = element[1]			# mac 地址
					old_status = element[3]		# 在线状态
					new_status = 0

					# 匹配在线列表 
					# 4200
					# connection = [x for x in json_list["responses"][0]["output"]["devices"] if x["knownMACAddresses"][0] == mac and len(x["connections"]) > 0]
					# 6500
					connection = [x for x in json_list["responses"][1]["output"]["connections"] if x["macAddress"] == mac]
					if len(connection) > 0:
						new_status = 1	# 在线

					# 如果在线状态发生变化
					if old_status != new_status:
						element[3] = new_status
						# print (old_status, new_status)
						if old_status == 0 and new_status == 1:
							# print element[0].encode("utf-8") + ' 来了。'
							# 刚上线，则开门，亮提示灯，语音提示
							func(element[0].encode("utf-8"), element[2], new_status)
						elif old_status == 1 and new_status == 0:
							# print element[0].encode("utf-8") + ' 走了。'
							# 提示离线
							func(element[0].encode("utf-8"), element[2], new_status)

					# print element, len(connection)

	def main():
		try:
			while True:   
				is_online()

				time.sleep(1)
		except KeyboardInterrupt:
			print('User press Ctrl+c ,exit;')
		finally:
			pass

	#if __name__ == "__main__":
	#	main()