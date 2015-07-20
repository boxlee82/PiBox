#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
from datetime import datetime
from datetime import timedelta

class RGBLED :

	# colors = [0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0xFF00FF, 0x00FFFF, 0xFFFFFF, 0x9400D3]
	# physical
	# pins = {'pin_R':26, 'pin_G':13, 'pin_B':19}  # pins is a dict
	pins = { }

	# Constructor
	def __init__(self, pinR = 26, pin_G = 13, pin_B = 19): 
		global p_R, p_G, p_B

		self.pins = {'pin_R': pinR, 'pin_G': pin_G, 'pin_B': pin_B}

		# Numbers GPIOs by physical location
		# GPIO.setmode(GPIO.BOARD)       
		GPIO.setmode(GPIO.BCM)  

		for i in self.pins:
			GPIO.setup(self.pins[i], GPIO.OUT)   # Set pins' mode is output
			GPIO.output(self.pins[i], GPIO.HIGH) # Set pins to high(+3.3V) to off led

		p_R = GPIO.PWM(self.pins['pin_R'], 2000)  # set Frequece to 2KHz
		p_G = GPIO.PWM(self.pins['pin_G'], 2000)
		p_B = GPIO.PWM(self.pins['pin_B'], 5000)

		p_R.start(100)      # Initial duty Cycle = 100(leds off)
		p_G.start(100)
		p_B.start(100)

	# 将一个数从一个区间线性映射到另一个区间，比如将0~100之间的一个数映射到0~255之间
	def map(self, x, in_min, in_max, out_min, out_max):   
		return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

	# For example : col = 0x112233
	def setColor(self, col):   
		R_val = (col & 0xFF0000) >> 16
		G_val = (col & 0x00FF00) >> 8
		B_val = (col & 0x0000FF) >> 0
	
		R_val = self.map(R_val, 0, 255, 0, 100)   # change a num(0~255) to 0~100.
		G_val = self.map(G_val, 0, 255, 0, 100)
		B_val = self.map(B_val, 0, 255, 0, 100)
	
		p_R.ChangeDutyCycle(R_val)     # Change duty cycle
		p_G.ChangeDutyCycle(G_val)
		p_B.ChangeDutyCycle(B_val)

	# 生成 rgb 颜色
	def rgbColor(self, r, g, b):   	
		return (r << 16) + (g << 8) + (b << 0)

	# 渐变色测试
	def test(self, scan = 5, seconds = 0.01):   	
			for dc in range(0, 255, scan):
				self.setColor(self.rgbColor(255, 0, dc))            
				time.sleep(seconds)
			for dc in range(255, 0, -scan):
				self.setColor(self.rgbColor(dc, 0, 255))            
				time.sleep(seconds)
			for dc in range(0, 255, scan):
				self.setColor(self.rgbColor(0, dc, 255))            
				time.sleep(seconds)
			for dc in range(255, 0, -scan):
				self.setColor(self.rgbColor(0, 255, dc))            
				time.sleep(seconds)
			for dc in range(0, 255, scan):
				self.setColor(self.rgbColor(dc, 255, 0))            
				time.sleep(seconds)
			for dc in range(255, 0, -scan):
				self.setColor(self.rgbColor(255, dc, 0))            
				time.sleep(seconds)
		
	flag_color = 0xffffff
	flag_timeout = datetime(1900, 1, 1)

	# 提示灯
	def setLight(self, col = 0xffffff, seconds = 5): 
		self.flag_color = col 
		self.flag_timeout = datetime.now() + timedelta(seconds =+ seconds)

	# 呼吸灯函数	
	def breath(self, scan = 5, seconds = 0.01):   
		for dc in range(255, 2, -scan):
			if (self.flag_timeout < datetime.now()):
				self.setColor(self.rgbColor(dc, dc, dc)) 
			else:
				self.setColor(self.flag_color)            
         
			time.sleep(seconds)
	
		for dc in range(2, 255, scan):
			if (self.flag_timeout < datetime.now()):
				self.setColor(self.rgbColor(dc, dc, dc))    
			else:
				self.setColor(self.flag_color)            
 
			time.sleep(seconds)


	# 关闭前，必须停止 gpio
	def cleanup(self):
		p_R.stop()
		p_G.stop()
		p_B.stop()
		for i in self.pins:
			GPIO.output(self.pins[i], GPIO.HIGH)    # Turn off all leds
		GPIO.cleanup()