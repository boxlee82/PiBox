# -*- coding: utf-8 -*-  

import thread  

# 显示屏
from datetime import *
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont
import os
import unicodedata
import traceback

# 加载库文件
import sys
sys.path.append(os.path.split(os.path.realpath(__file__))[0] + "/Adafruit_BMP085")
# 标准化编码
reload(sys) 
sys.setdefaultencoding("utf-8")

# 温度，气压
from Adafruit_BMP085 import BMP085
# 温度，湿度
import Adafruit_DHT
import Adafruit_DHT.Raspberry_Pi_2 as platform
# PM2.5
import ZhyuIoT_GP2Y10
import ZhyuIoT_GP2Y10.Raspberry_Pi as gp2y10
# 发音单元
sys.path.append(os.path.split(os.path.realpath(__file__))[0] + "/Web_TTS")
from Web_TTS import TTS
# LED 控制单元
sys.path.append(os.path.split(os.path.realpath(__file__))[0] + "/RGB_LED")
from RGB_LED import RGBLED
# 思科 路由器状态
sys.path.append(os.path.split(os.path.realpath(__file__))[0] + "/CISCO_Smart")
from CISCO_Smart import CISCO
# 彩云天气
sys.path.append(os.path.split(os.path.realpath(__file__))[0] + "/Caiyun_APP")
from CAIYUN import CAIYUN

# 按钮操作
import RPi.GPIO as GPIO

# 初始化语音引擎
tts = TTS()
chinese_week = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 初始化 led 控制单元
led = RGBLED(26, 13, 19)

# 初始化思科单元
cicso_smart = CISCO()

# 初始化彩云天气
caiyun = CAIYUN()
lonlat = '116.7261,23.3778' # 地理坐标 '120.1829,30.2435' #
caiyun_text = ''

# 初始化继电器 针脚定义
GPIO_RELAY = 21

# 0.96 oled spi 显示屏 针脚定义
RST = 17
DC = 27
SPI_PORT = 0
SPI_DEVICE = 0

# bmp085 参数定义
bmp = BMP085(0x77)

# AM2302 参数定义
sensor = Adafruit_DHT.DHT22
pin = 4


# 全局变量 传感器参数
humidity = 0.0
density = 0.0
temp = 0.0
pressure = 0.0

attemp_DHT = datetime(1900, 1, 1)
attemp_GP2Y10 = datetime(1900, 1, 1)

# 退出线程标志
thread_run = True

# 整点报时标志
attemp_hour = -1


# 按时间段控制播报音量
# 晚上 10 点 - 早上 8 点前，播报音量 30%；白天音量大
def volume_with_time():
    time_hour = datetime.now().hour
    if ((time_hour < 8) or (time_hour > 22)):
        return -25
    else:
        return 10

def cleanup():
    # 释放资源，不然下次运行是可能会收到警告
    print('clean up')
    GPIO.cleanup()

def load_sensor():
	global attemp_DHT, attemp_GP2Y10
	global humidity, density, temp, pressure

	time_now = datetime.now()

	# 每 2 秒读一次
	# 读取 dht 湿度，温度；bmp085 温度，气压
	if (time_now - attemp_DHT).seconds > 10:
		attemp_DHT = time_now
		# humidity, temperature = Adafruit_DHT.read_retry(sensor, pin) # 时间间隔两秒
		# adafruit dht 库有问题，反复执行 pi_version 函数，open('/proc/cpuinfo', 'r') 会导致出错
		humidity, temperature = Adafruit_DHT.read_retry(sensor, pin, 15, 2, platform)	# 时间间隔两秒
		temp = (bmp.readTemperature() + temperature) / 2
		pressure = bmp.readPressure()
	# 读取 pm2.5浓度，每 5 秒读一次
	if (time_now - attemp_GP2Y10).seconds > 30:
		attemp_GP2Y10 = time_now
		density = ZhyuIoT_GP2Y10.read(ZhyuIoT_GP2Y10.GP2Y1051A, 5, gp2y10)	# if density is None: attemp = 1 ATTEMPS = 5
def start_sensor():
	while thread_run:
		try:
			load_sensor()
		except: 
			print "sensor except: ", traceback.print_exc()

		time.sleep(1)
		
# 读取传感器参数线程
def thread_sensor(): 
    thread.start_new_thread(start_sensor, ())  



# 128x64 display with hardware SPI:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
# Initialize library.
disp.begin()
# Clear display.
disp.clear()

# 显示内容
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load default font.
font = ImageFont.truetype(os.path.split(os.path.realpath(__file__))[0] + "/simsun.ttf", 12)


# OLED 显示
def oled_display():
	global humidity, temperature, density, temp, pressure
	global attemp_hour
	global cisco_text, cisco_time
	global caiyun_text    

	datetime_now = datetime.now()

	padding = 0
	top = 0
	left = 0

	# Clear image buffer by drawing a black filled box.
	draw.rectangle((0,0,width,height), outline=0, fill=0)

	if (datetime_now - cisco_time).seconds < 20:
		# 显示路由器提示信息
		today = cisco_text
		today = unicode(today, 'UTF-8')
	else:
        		# 显示时间
		today = datetime_now.strftime('%m月%d日 %H:%M:%S') + " " + chinese_week[datetime_now.weekday()]
		today = unicode(today, 'UTF-8')
        		# 显示天气
		if len(caiyun_text) > 0:
		  today += " " + unicode(caiyun_text, 'UTF-8') + "\n\n"      

	txt = today 
    
	# 计算文本长度，实现滚动跑马字
	font_width, font_height = font.getsize(txt)
	# 文字小于 128 像素，无需执行跑马灯
	if font_width < width:           
	   draw.text((left, top), txt, font=font, fill=255)
	else:
 	   txt += txt 
 	   text_left = int((time.time() * 35) % font_width)
	   draw.text((-text_left, top), txt, font=font, fill=255)

	top = top + 16
	txt = unicode("温度：%.1f ℃" % temp, "UTF-8")
	draw.text((left, top), txt,  font=font, fill=255)

	top = top + 16
	txt = unicode("湿度：%.1f %%" % humidity, "UTF-8")
	draw.text((left, top), txt,  font=font, fill=255)

	top = top + 16
	txt = unicode("PM2.5：%.1f ug/m³" % density, "UTF-8")
	draw.text((left, top), txt,  font=font, fill=255)

	# Display image.
	disp.image(image)
	disp.display()

	if attemp_hour != datetime_now.hour:
		attemp_hour = datetime_now.hour
		txt = '现在时间 %s %s，%s, 温度%.1f摄氏度，湿度百分之%.1f ，气压%.1f帕，PM2.5浓度%.1f微克每立方米' % (datetime.now().strftime('%H:%M'), 
			chinese_week[datetime.now().weekday()],
			caiyun_text,
			temp,
			humidity,
			(pressure / 100.0),
			density)
	
		print datetime.now().strftime('%H:%M:%S >> ') + txt
		tts.raspberryTalk(txt, volume_with_time())

def start_oled():
	while thread_run:
		try:
			oled_display()
		except:
			print "oled except: ",traceback.print_exc()

		time.sleep(0.1)


# 读取传感器参数线程
def thread_oled(): 
    thread.start_new_thread(start_oled, ())  

		
def start_led():
	while thread_run:
		try:
			#led.test(8, 0.008)
			led.breath(1, 0.012)
		except:
			print "led except: ", traceback.print_exc()

		time.sleep(0.5)


# 读取传感器参数线程
def thread_led(): 
    thread.start_new_thread(start_led, ())  

# 路由状态提示
cisco_text = ""
cisco_time = datetime(1900, 1, 1)

# 处理在线用户状态
def cisco_callback(friendlyName, userDeviceName, new_status):
	global cisco_text, cisco_time

	friendlyName = friendlyName.replace('android-', '').replace('iphone-', '')
	print friendlyName, userDeviceName, new_status

	# 开门，提示灯，声音提示
	if new_status == 1:
		# 执行开门

		if userDeviceName == True:
			# 定制用户，红灯提醒
			led.setLight(0xff0000, 20) 
			txt = "注意：" + friendlyName + " 来了"
		else:
			# 普通用户，蓝灯提醒
			led.setLight(0x0000ff, 20) 
			txt = friendlyName + " 来了"
            
        # 执行开门操作，继电器闭合
		GPIO.setup(GPIO_RELAY, GPIO.OUT)
	elif new_status == 0:
		# 用户走了，绿灯提习惯
		led.setLight(0x00ff00, 20) 
		txt = friendlyName + " 走了"
	
	# 屏幕提示
	cisco_text = txt
	cisco_time = datetime.now()

	# 语音提示
	print datetime.now().strftime('%H:%M:%S >> ') + txt
	tts.raspberryTalk(txt, volume_with_time())
    
    # 继电器停止
	GPIO.setup(GPIO_RELAY, GPIO.IN)    

def start_cisco():
	while thread_run:
		try:
			cicso_smart.online_devices(cisco_callback)
		except:
			print "cisco except: ", traceback.print_exc()

		time.sleep(1)

# 读取路由器在线
def thread_cisco(): 
    thread.start_new_thread(start_cisco, ())  

def get_caiyun():
	global caiyun_text, lonlat

	try:
		caiyun_rain = caiyun.getRain()
		caiyun_text = "" + caiyun.getSummary(lonlat) #.replace('还在加班么？注意休息哦', '').replace('，放心出门吧', '').replace('公里外呢',
                                               #'公里外').replace('。', '')
		# 转换统一格式
		caiyun_text = str(caiyun_text)

		# print caiyun_text
		# 如果天气状态从没雨变成有雨
		if caiyun_rain == False and caiyun.getRain() == True:
			txt = "天气预警：" + caiyun_text
			# print type("天气预警："), len("天气预警："), "天气预警："

			print datetime.now().strftime('%H:%M:%S >> ') + txt
			tts.raspberryTalk(txt, volume_with_time())
	except:
		print "caiyun except: ", traceback.print_exc()

def start_caiyun():
    while thread_run:
		get_caiyun()
		time.sleep(60)

# 读取彩云天气
def thread_caiyun(): 
    thread.start_new_thread(start_caiyun, ())  


def main():
	try:
        # 继电器停止
		GPIO.setup(GPIO_RELAY, GPIO.IN) 

		# 启动 呼吸灯
		thread_led()
        
		# 读取传感器
		load_sensor()
		# 读取天气预报
		get_caiyun()

		# OLED 屏幕显示，附带整点报时
		thread_oled()

		# 启动读取思科路由状态
		thread_cisco()
 		# 启动读取传感器参数线程
		thread_sensor()       
		# 启动读取彩云天气
		thread_caiyun()

		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		thread_run = False
		print('User press Ctrl+c ,exit;')
	finally:
		cleanup()
		pass


if __name__ == "__main__":
    main()
