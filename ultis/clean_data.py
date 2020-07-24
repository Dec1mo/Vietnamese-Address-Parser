import os
import sys
lib_path = os.path.abspath(os.path.join('.'))
sys.path.append(lib_path)
sys.path.append(os.path.abspath(os.path.join('./address_graph')))

import json
import pickle
import unicodedata
import re

import ultis.parameters as p

all_addreses = dict()
with open(p._PICKLE_DIR + p.CITY_SET_PKL_PATH, 'rb') as f:
	city_list = list(pickle.load(f))
# with open(p._PICKLE_DIR + p.NON_ACCENT_STD_FIELD_DICT_PKL_PATH, 'rb') as f:
# 	non_accent_dict = pickle.load(f)

def handle_dup_substr(str):
	for i in range(len(str)//2, 0, -1):
		idx = str[i:].find(str[:i])
		if idx != -1 and len(str[:i]) > 1 and idx < 3:
			return str[i:]
	for i in range(len(str)//2, int(len(str)*0.8)):
		idx = str[:i].find(str[i:])
		if idx != -1 and len(str[i:]) > 1 and idx < 3:
			return str[:i]
	return str

def remove_redunts(str):
	str_list = [x for x in str.split(',') if x != '' and x != ' ']
	str_list[0] = str_list[0].strip()
	str =''
	for i in range(len(str_list) - 1):
		str += str_list[i] + ','
	str += str_list[len(str_list) - 1]
	return str

def main():
	for i in range (p.FIRST_AREA, p.LAST_AREA+1):
		with open((p._RAW_DATA_DIR_PATH + p.RAW_DATA_JSON_PATH).format(i), 'r', encoding='utf-8') as f:
			res_dict = json.loads(f.read())
		for hash_key, meta_address in res_dict.items():
			one_record = dict()
			address = meta_address['address']
			address = remove_redunts(handle_dup_substr(address))
			# max_idx = -1
			# new_address = address
			# for city in city_list:
			# 	idx = address.lower().rfind(city.lower())
			# 	if idx > max_idx:
			# 		new_address = address[:(idx + len(city))]
			# if new_address == None:
			# 	# Logging uncleaned addresses
			# 	with open(p._LOG_DIR + p.NOT_CLEAN_LOG_PATH, 'a', encoding='utf-8') as f:
			# 		f.write('{}: {}\n'.format(hash_key, address))
			# else:
			one_record['address'] = address
			one_record['title'] = meta_address['title']
			one_record['gps'] = meta_address['gps']
			all_addreses[hash_key] = one_record
			
	print('len all_addreses = ', len(all_addreses))
	with open(p._CLEAN_DATA_DIR_PATH + p.CLEAN_DATA_FILE_PATH, 'w', encoding='utf-8') as f:
		json.dump(all_addreses, f, indent=2, ensure_ascii=False)

	# #####################
	# address = norm('44, Ngõ Thọ Xương, Q. Hoàn Kiếm, Tp. Hà Nội')
	# print(address)	
if __name__ == '__main__':
	main()

