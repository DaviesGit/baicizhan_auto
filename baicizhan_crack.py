import sys
import os
import re
import pyscreenshot as ImageGrab
from PIL import Image
import pytesseract
from fuzzywuzzy import fuzz
import win32api, win32gui, win32con
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

	position1=(134,808)
	position2=(258,712)
	word=Option(42,318,463,427)
	option_A=Option(78,555,424,604)
	option_B=Option(78,644,424,692)
	option_C=Option(78,732,424,782)
	option_D=Option(78,822,424,870)
	dictionary_database='stardict.db'


	def click(x,y):
		current_position=win32gui.GetCursorPos()
		win32api.SetCursorPos((x,y))
		win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
		win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
		win32api.SetCursorPos(current_position)


	def save_option_image(option,file_name):
		image=ImageGrab.grab(bbox=option.position())
		image.save(file_name)

	cursor_list={}
	def get_translate_result(word):
		thread_name='thread_id_'+str(threading.get_ident())
		# print(cursor_list)
		if(not thread_name in cursor_list):
			connect =sqlite3.connect(dictionary_database)
			cursor=connect.cursor()
			cursor_list[thread_name]=cursor
		cursor_list[thread_name].execute("select word, translation from stardict where word='"+word+"'")
		result=cursor_list[thread_name].fetchone()
		if None==result:
			return False
		else:
			return result[1]

	def choose(option):
		click(int(option.centerX()),int(option.centerY()))

	def calculate_ratio(option,result_translate):
		word_array=re.split('[\x20-\x7E]|\r|\n|′|，|〉|·|的|地|〔|、', option.text)
		word_array_correct=[]
		for item in word_array:
			length=len(item)
			if (0==length):
				'0==length' and None
			elif(3>=length and 0<length):
				word_array_correct.append(item)
			elif (4<=length and 5>=length):
				word_array_correct.append(item[:2])
				word_array_correct.append(item[2:])
			elif (6<=length):
				word_array_correct.append(item[:3])
				word_array_correct.append(item[3:])	


		total_ratio=0
		count=len(word_array_correct)
		for item in word_array_correct:
			ratio=fuzz.partial_ratio(item,result_translate)
			if 100==ratio:
				option.ratio=100.0
				return option.ratio
			total_ratio+=ratio

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


	class WordRecognize:
		last_next_word=None
		last_last_word=None

		next_word=None
		last_word=None
		last_recognize=None
		is_stoped=False #be stoped
		is_started=False #is called start()
		get_last_word_lock=threading.Lock()
		get_next_word_lock=threading.Lock()


		@staticmethod
		def start():
			class RecognizeThread (threading.Thread):
				def __init__(self,option,file_name):
					threading.Thread.__init__(self)
					self.option=option
					self.file_name=file_name
				def run(self):
					while(not WordRecognize.is_stoped):
						save_option_image(self.option,self.file_name)
						WordRecognize.last_recognize = pytesseract.image_to_string(Image.open(self.file_name),config='--psm 13 --oem 0',lang='eng')
						# print ('WordRecognize.last_recognize: '+WordRecognize.last_recognize)
						if(WordRecognize.last_recognize!=re.sub(r'[^\x41-\x5A\x61-\x7A]+','',WordRecognize.last_recognize)):
							continue
						if(3>len(WordRecognize.last_recognize)):
							continue
						if(not get_translate_result(WordRecognize.last_recognize)):
							continue
						self.option.text=WordRecognize.last_word=WordRecognize.last_recognize
						# print ('WordRecognize.last_word: '+WordRecognize.last_word)
						if(WordRecognize.get_last_word_lock.locked()):
							WordRecognize.get_last_word_lock.release()
						if(WordRecognize.last_last_word==WordRecognize.last_word):
							if(WordRecognize.last_next_word!=WordRecognize.last_word):
								WordRecognize.next_word=WordRecognize.last_word
								WordRecognize.last_next_word=WordRecognize.next_word
								# print ('WordRecognize.next_word: '+WordRecognize.next_word)
								if(WordRecognize.get_next_word_lock.locked()):
									WordRecognize.get_next_word_lock.release()
						else:
							WordRecognize.last_last_word=WordRecognize.last_word


			WordRecognize.is_started=True
			WordRecognize.get_last_word_lock.acquire()
			WordRecognize.get_next_word_lock.acquire()
			recognize_thread=RecognizeThread(word,'word.png')
			recognize_thread.start()
		@staticmethod
		def stop():
			WordRecognize.is_stoped=True
		@staticmethod
		def get_last_word():
			if (WordRecognize.get_last_word_lock.locked()):
				WordRecognize.get_last_word_lock.acquire()
				WordRecognize.get_last_word_lock.release()
			return WordRecognize.last_word
		@staticmethod
		def get_last_recognize():
			return WordRecognize.last_recognize
		@staticmethod
		def get_next_word():
			if (WordRecognize.get_next_word_lock.locked()):
				WordRecognize.get_next_word_lock.acquire()
				WordRecognize.get_next_word_lock.release()
			value=WordRecognize.next_word
			WordRecognize.next_word=None
			WordRecognize.get_next_word_lock.acquire()
			return value


	def auto_choose():

		lock_count=threading.Lock()
		lock_wait=threading.Lock()
		def recognize_all_option():
			lock_wait.acquire()
			finished_thread_count=0
			def finsh():
				nonlocal finished_thread_count
				lock_count.acquire()
				finished_thread_count+=1
				# print(str(finished_thread_count))
				if(4<=finished_thread_count):
					lock_wait.release()
				lock_count.release()


			class RecognizeThread (threading.Thread):
				def __init__(self,option,file_name):
					threading.Thread.__init__(self)
					self.option=option
					self.file_name=file_name
				def run(self):
					save_option_image(self.option,self.file_name)
					self.option.text = pytesseract.image_to_string(Image.open(self.file_name),config='--psm 13 --oem 0',lang='chi_sim')
					finsh()

			thread_option_A=RecognizeThread(option_A,'option_A.png')
			thread_option_B=RecognizeThread(option_B,'option_B.png')
			thread_option_C=RecognizeThread(option_C,'option_C.png')
			thread_option_D=RecognizeThread(option_D,'option_D.png')

			thread_option_A.start()
			thread_option_B.start()
			thread_option_C.start()
			thread_option_D.start()

			lock_wait.acquire()
			lock_wait.release()

		if(not WordRecognize.is_started):
			WordRecognize.start()
		word_text=WordRecognize.get_next_word()
		print('the word is: >>>>'+word_text+'<<<<')
		result_translate=get_translate_result(word_text)
		print('------------')
		print(result_translate)
		print('------time used:------')
		
		begain_time=time.time()
		recognize_all_option()
		end_time=time.time()
		print(str(end_time-begain_time))

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
		if(word_text!=WordRecognize.get_last_recognize()):
			return False
		choose(max_option)

		print('-----------------------')
		print(option_A.text+'  ratio: '+str(option_A.ratio))
		print(option_B.text+'  ratio: '+str(option_B.ratio))
		print(option_C.text+'  ratio: '+str(option_C.ratio))
		print(option_D.text+'  ratio: '+str(option_D.ratio))
		print('')
		print('answer:  '+max_option.text+'  ratio: '+str(max_option.ratio))
		print('--------------------------------------------')
		return True

	count=0
	while(True):
		count+=1
		if(7>=count):
			auto_choose()
		else:
			time.sleep(10)
			click(position1[0],position1[1])
			time.sleep(2)
			click(position2[0],position2[1])
			count=0




if __name__ == "__main__":
	main()

