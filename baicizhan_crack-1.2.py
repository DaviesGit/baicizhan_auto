import sys
import os
import re
import pyscreenshot as ImageGrab
from PIL import Image
import pytesseract
from fuzzywuzzy import fuzz
import sqlite3
import threading
import time
from pymouse import PyMouse
from aip import AipOcr


def main():
	os.environ['TESSDATA_PREFIX'] = 'E:\\Program Files\\Tesseract-OCR\\tessdata'

	class Option:
		def __init__(self, positionX1, positionY1, positionX2, positionY2, id):
			self.positionX1 = positionX1
			self.positionY1 = positionY1
			self.positionX2 = positionX2
			self.positionY2 = positionY2
			self.id = id

		def center(self):
			return ((self.positionX1+self.positionX2)/2, (self.positionY1+self.positionY2)/2)

		def centerX(self):
			return (self.positionX1+self.positionX2)/2

		def centerY(self):
			return (self.positionY1+self.positionY2)/2

		def position(self):
			return (self.positionX1, self.positionY1, self.positionX2, self.positionY2)

	xoffset = 0
	yoffset = 0
	word = Option(35+xoffset, 355+yoffset, 431+xoffset, 427+yoffset, '')
	option_A = Option(76+xoffset, 515+yoffset, 393+xoffset, 576+yoffset, 'A')
	option_B = Option(76+xoffset, 597+yoffset, 393+xoffset, 658+yoffset, 'B')
	option_C = Option(76+xoffset, 679+yoffset, 393+xoffset, 740+yoffset, 'C')
	option_D = Option(76+xoffset, 761+yoffset, 393+xoffset, 822+yoffset, 'D')
	dictionary_database = 'stardict.db'
	m = PyMouse()

	def save_option_image(option, file_name):
		image = ImageGrab.grab(bbox=option.position())
		image.save(file_name)

	cursor = None

	def get_translate_result(word):
		nonlocal cursor
		if(None == cursor):
			connect = sqlite3.connect(dictionary_database)
			cursor = connect.cursor()
		cursor.execute(
			"select word, translation from stardict where word='"+word+"'")
		result = cursor.fetchone()
		if None == result:
			# for tesseract
			'''
			if('u' in word):
				print("trying replace u to li")
				return get_translate_result(word.replace('u', 'li'))
			if('n' in word):
				print("trying replace u to il")
				return get_translate_result(word.replace('n', 'il'))
			else:
				return False
			'''
			return False
		else:
			return str(re.findall(u'([\u4e00-\u9fff]+)', result[1]))

	def choose(option):
		print('choosed ' + option.id+'. ratio is '+str(option.ratio))
		m.click(int(option.centerX()), int(option.centerY()))
		print(str(option.centerX())+','+str(option.centerY())+' clicked.')
		m.move(0, 0)

	def calculate_ratio(option, result_translate):
		# Method 1
		'''
		word_array = re.split(
			'\ |\?|\.|\/|\;|\:|′|`|,|，|\"|\'|·|\r|\n|的|地', option.text)
		total_ratio = 0
		count = len(word_array)
		for item in word_array:
			if '' != item:
				ratio = fuzz.partial_ratio(item, result_translate)
				if 100 == ratio:
					option.ratio = 100.0
					return option.ratio
				total_ratio += ratio
			else:
				count -= 1
		if (0 == count):
			option.ratio = 0
		else:
			option.ratio = total_ratio/count
		return option.ratio
		'''

		# Method 2 (from 1.0)
		word_array = re.split('[\x20-\x7E]|\r|\n|′|，|〉|·|的|地|〔|、', option.text)
		word_array_correct = []
		for item in word_array:
			length = len(item)
			if (0 == length):
				'0==length' and None
			elif(3 >= length and 0 < length):
				word_array_correct.append(item)
			elif (4 <= length and 5 >= length):
				word_array_correct.append(item[:2])
				word_array_correct.append(item[2:])
			elif (6 <= length):
				word_array_correct.append(item[:3])
				word_array_correct.append(item[3:])

		total_ratio = 0
		count = len(word_array_correct)
		for item in word_array_correct:
			ratio = fuzz.partial_ratio(item, result_translate)
			if 100 == ratio:
				option.ratio = 100.0
				return option.ratio
			total_ratio += ratio

		if (0 == count):
			option.ratio = 0
		else:
			option.ratio = total_ratio/count
		return option.ratio

		# Method 3
		'''
		option.ratio=fuzz.token_sort_ratio(option.text, result_translate)
		return option.ratio
		'''

	def get_max_ratio(option_A, option_B, option_C, option_D):
		max_option = option_A
		if (option_B.ratio > max_option.ratio):
			max_option = option_B
		if (option_C.ratio > max_option.ratio):
			max_option = option_C
		if (option_D.ratio > max_option.ratio):
			max_option = option_D
		return max_option

	last_word = ''
	last_word_translate = ''

	def auto_choose():

		def save_all_image():
			finished_thread_count = 0
			lock_count = threading.Lock()
			lock_wait = threading.Lock()
			lock_wait.acquire()

			def finsh():
				nonlocal finished_thread_count
				lock_count.acquire()
				finished_thread_count += 1
				# print(str(finished_thread_count), end='')
				if(5 <= finished_thread_count):
					# print(str(finished_thread_count)+'Image saved.')
					lock_wait.release()
				lock_count.release()

			class SaveThread (threading.Thread):
				def __init__(self, option, file_name):
					threading.Thread.__init__(self)
					self.option = option
					self.file_name = file_name

				def run(self):
					save_option_image(self.option, self.file_name)

					# img = cv2.imread(self.file_name)
					# img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

					# threshold all of them
					'''
					hd=230
					if(self.option.id==''):
						hd=200
					ret,img=cv2.threshold(img, hd, 255, cv2.THRESH_BINARY);
					im = Image.fromarray(img)
					im.save(self.file_name)
					'''

					# threshold the word only
					# (better than thresholding all of them)
					'''
					if(self.option.id == ''):
						ret, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)
						im = Image.fromarray(img)
						im.save(self.file_name)
					'''

					# no threshold
					# i think baidu-ocr will do it

					finsh()

			thread_word = SaveThread(word, 'word.png')
			thread_option_A = SaveThread(option_A, 'option_A.png')
			thread_option_B = SaveThread(option_B, 'option_B.png')
			thread_option_C = SaveThread(option_C, 'option_C.png')
			thread_option_D = SaveThread(option_D, 'option_D.png')

			thread_word.start()
			thread_option_A.start()
			thread_option_B.start()
			thread_option_C.start()
			thread_option_D.start()

			lock_wait.acquire()
			lock_wait.release()

		nonlocal last_word

		def image_to_string_online(filename):
			APP_ID = '23125232'
			API_KEY = 'Vh5i2Ft0RuOARzr6lMEpPGZ3'
			SECRET_KEY = 'Kk2GzHuZzdeuvAIfkAPF5Qg31Hw5eZvs'
			client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
			i = open(filename, 'rb')
			img = i.read()
			img_res = client.basicGeneral(img)
			if(len(img_res['words_result']) > 0):
				return str(img_res['words_result'][0]).replace(r"{'words': '", '').replace(r"'}", '')
			else:
				return ''

		while (True):
			save_all_image()

			# baidu-ocr is better than tesseract
			# word.text = pytesseract.image_to_string(Image.open('word.png'),config='--psm 7',lang='bcz')

			word.text = image_to_string_online('word.png')

			if(last_word == word.text):
				continue
			else:
				last_word = word.text
			print(word.text+' founded.')
			# seemed useless. but i don't know what it exactly means
			# if(word.text!=re.sub(r'[^\x41-\x5A\x61-\x7A]+','',word.text)):
			#	continue

			# for tesseract
			# word.text=re.search('[A-Za-z]*',word.text.replace(' ','').replace('0','o'))[0]
			'''
			t=0
			exit=False
			for i in word.text:
				if('A'<=i<='Z' and t!=0):
					if(i=='O' or i=='Z' or i=='C' or i=='I' or i=='V'):
						#word.text[t]=chr( ord(i)+32)
						l=list(word.text)
						l[t]=chr( ord(i)+32)
						word.text=''.join(l)
					else:
						exit=True
					break
				t=t+1
			if(exit):
				continue
			'''

			if(len(word.text) <= 2):
				continue
			print(word.text+' confirmed.')

			# comfirm twice. but i think it is useless for baidu-ocr
			'''
			if(last_word!=word.text):
				last_word=word.text
				continue
			'''
			result_translate = get_translate_result(word.text)
			if(False == result_translate):
				continue

			print(result_translate+" translated.")
			break

		finished_thread_count = 0
		lock_count = threading.Lock()
		lock_wait = threading.Lock()
		lock_wait.acquire()

		def finsh():
			nonlocal finished_thread_count
			lock_count.acquire()
			finished_thread_count += 1
			# print(str(finished_thread_count), end='')
			if(4 <= finished_thread_count):
				# print(str(finished_thread_count)+'Tesseract done.')
				lock_wait.release()
			lock_count.release()

		class TesseractThread (threading.Thread):
			def __init__(self, option, file_name):
				threading.Thread.__init__(self)
				self.option = option
				self.file_name = file_name

			def run(self):
				self.option.text = pytesseract.image_to_string(
					Image.open(self.file_name), config='--psm 7', lang='chi_sim')
				# multi thread for baidu-ocr needs money(
				# self.option.text=image_to_string_online(self.file_name)
				finsh()

		TesseractThread_A = TesseractThread(option_A, 'option_A.png')
		TesseractThread_B = TesseractThread(option_B, 'option_B.png')
		TesseractThread_C = TesseractThread(option_C, 'option_C.png')
		TesseractThread_D = TesseractThread(option_D, 'option_D.png')

		TesseractThread_A.start()
		TesseractThread_B.start()
		TesseractThread_C.start()
		TesseractThread_D.start()

		lock_wait.acquire()
		lock_wait.release()

		calculate_ratio(option_A, result_translate)
		calculate_ratio(option_B, result_translate)
		calculate_ratio(option_C, result_translate)
		calculate_ratio(option_D, result_translate)
		max_option = get_max_ratio(option_A, option_B, option_C, option_D)
		choose(max_option)
		print('-----------------------')
		print(option_A.text+'  ratio: '+str(option_A.ratio))
		print(option_B.text+'  ratio: '+str(option_B.ratio))
		print(option_C.text+'  ratio: '+str(option_C.ratio))
		print(option_D.text+'  ratio: '+str(option_D.ratio))
		print('-----------------------')
		return True

	while(True):
		auto_choose()


if __name__ == '__main__':
	main()
