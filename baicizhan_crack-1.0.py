import sys
import os
import re
import pyscreenshot as ImageGrab
from PIL import Image
import pytesseract
from fuzzywuzzy import fuzz
import win32api, win32con
import sqlite3
import threading
import time

def main():
	
	class Option:
		def __init__(self,positionX1,positionY1,positionX2,positionY2):
			self.positionX1=positionX1
			self.positionY1=positionY1
			self.positionX2=positionX2
			self.positionY2=positionY2
		def center(self):
			return ((self.positionX1+self.positionX2)/2,(self.positionY1+self.positionY2)/2)
		def centerX(self):
			return (self.positionX1+self.positionX2)/2
		def centerY(self):
			return (self.positionY1+self.positionY2)/2
		def position(self):
			return (self.positionX1,self.positionY1,self.positionX2,self.positionY2)


	word=Option(42,318,463,427)
	option_A=Option(78,555,424,604)
	option_B=Option(78,644,424,692)
	option_C=Option(78,732,424,782)
	option_D=Option(78,822,424,870)
	dictionary_database='stardict.db'


	def click(x,y):
	    win32api.SetCursorPos((x,y))
	    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
	    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)


	def save_option_image(option,file_name):
		image=ImageGrab.grab(bbox=option.position())
		image.save(file_name)

	cursor=None
	def get_translate_result(word):
		nonlocal cursor
		if(None==cursor):
			connect =sqlite3.connect(dictionary_database)
			cursor=connect.cursor()
		cursor.execute("select word, translation from stardict where word='"+word+"'")
		result=cursor.fetchone()
		if None==result:
			return False
		else:
			return result[1]

	def choose(option):
		click(int(option.centerX()),int(option.centerY()))
		win32api.SetCursorPos((0,0))

	def calculate_ratio(option,result_translate):
		word_array=re.split('\ |\?|\.|\/|\;|\:|′|`|,|，|\"|\'|·|\r|\n|的|地', option.text)
		total_ratio=0
		count=len(word_array)
		for item in word_array:
			if ''!=item:
				ratio=fuzz.partial_ratio(item,result_translate)
				if 100==ratio:
					option.ratio=100.0
					return option.ratio
				total_ratio+=ratio
			else:
				count-=1
		if (0==count):
			option.ratio=0
		else:
			option.ratio=total_ratio/count
		return option.ratio

	def get_max_ratio(option_A,option_B,option_C,option_D):
		max_option=option_A
		if (option_B.ratio>max_option.ratio):
			max_option=option_B
		if (option_C.ratio>max_option.ratio):
			max_option=option_C
		if (option_D.ratio>max_option.ratio):
			max_option=option_D
		return max_option

	last_word=''
	last_word_translate=''
	def auto_choose():

		def save_all_image():
			finished_thread_count=0
			lock_count=threading.Lock()
			lock_wait=threading.Lock()
			lock_wait.acquire()
			def finsh():
				nonlocal finished_thread_count
				lock_count.acquire()
				finished_thread_count+=1
				print(str(finished_thread_count))
				if(5<=finished_thread_count):
					print(str(finished_thread_count))
					lock_wait.release()
				lock_count.release()


			class SaveThread (threading.Thread):
				def __init__(self,option,file_name):
					threading.Thread.__init__(self)
					self.option=option
					self.file_name=file_name
				def run(self):
					save_option_image(self.option,self.file_name)
					finsh()

			thread_word=SaveThread(word,'word.png')
			thread_option_A=SaveThread(option_A,'option_A.png')
			thread_option_B=SaveThread(option_B,'option_B.png')
			thread_option_C=SaveThread(option_C,'option_C.png')
			thread_option_D=SaveThread(option_D,'option_D.png')

			thread_word.start()
			thread_option_A.start()
			thread_option_B.start()
			thread_option_C.start()
			thread_option_D.start()

			lock_wait.acquire()
			lock_wait.release()

		nonlocal last_word
		nonlocal last_word_translate
		while (True):

			save_all_image()
			word.text = pytesseract.image_to_string(Image.open('word.png'),config='--psm 13 --oem 0',lang='eng')
			


			print(word.text)
			if(word.text!=re.sub(r'[^\x41-\x5A\x61-\x7A]+','',word.text)):
				continue
			if(3>len(word.text)):
				continue
			print (word.text)
			if(last_word!=word.text):
				last_word=word.text
				continue
			
			result_translate=get_translate_result(word.text)
			print(result_translate)
			if(False==result_translate):
				continue
			if(last_word_translate!=result_translate):
				last_word_translate=result_translate
				break






		option_A.text = pytesseract.image_to_string(Image.open('option_A.png'),config='--psm 13 --oem 0',lang='chi_sim')
		option_B.text = pytesseract.image_to_string(Image.open('option_B.png'),config='--psm 13 --oem 0',lang='chi_sim')
		option_C.text = pytesseract.image_to_string(Image.open('option_C.png'),config='--psm 13 --oem 0',lang='chi_sim')
		option_D.text = pytesseract.image_to_string(Image.open('option_D.png'),config='--psm 13 --oem 0',lang='chi_sim')

		# os.remove('word.png')
		# os.remove('option_A.png')
		# os.remove('option_B.png')
		# os.remove('option_C.png')
		# os.remove('option_D.png')

		calculate_ratio(option_A, result_translate)
		calculate_ratio(option_B, result_translate)
		calculate_ratio(option_C, result_translate)
		calculate_ratio(option_D, result_translate)
		max_option=get_max_ratio(option_A,option_B,option_C,option_D);
		choose(max_option)
		print('-----------------------')
		print(option_A.text+'  ratio: '+str(option_A.ratio))
		print(option_B.text+'  ratio: '+str(option_B.ratio))
		print(option_C.text+'  ratio: '+str(option_C.ratio))
		print(option_D.text+'  ratio: '+str(option_D.ratio))

		print('answer:  '+max_option.text+'  ratio: '+str(max_option.ratio))
		print('--------------------------------------------')
		return True


	while(True):
		auto_choose()



if __name__ == "__main__":
	main()

