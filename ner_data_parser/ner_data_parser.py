import os
import sys
lib_path = os.path.abspath(os.path.join('.'))
sys.path.append(lib_path)

import json
import re
import pickle

import ultis.parameters as p

def hasNumbers(str):
	return any(char.isdigit() for char in str)

def std_v_field(std_dict, str):
	# try:
	return std_dict[str.strip().lower()]
	# except:
	# 	return ''

def acronym_type(acronym_dict, str):
	try:
		return acronym_dict[str.lower()]
	except:
		return ''

def construct_substr(str, real_str, type):
	if str == '':
		return ''
	return '('+str+')#'+'('+real_str+')#'+type#.upper()

def preprocess(addr_set):
	addr_list = []
	raw_addr = addr_set['raw_address']

	others = ['other', 'post_code', 'country']
	for str in others:
		if str in addr_set:
			addr_set[str][0] = addr_set[str][0].strip()

	# print(addr_set)
	for key, value in addr_set.items():
		if isinstance(key, int):
			if key == p.TITLE_ADMIN_LV:
				continue
			elif key != p.NAME_ADMIN_LV:
				if value[0].isdigit():
					add_str = 'Quận '
					if value[1] == 'ward':
						add_str = 'Phường '
					one_addr_list = [[value[3][0], value[4][-1]], (value[2] + value[0]).strip(), add_str + value[5], acronym_type(p.acronym_dict, value[1])]
				else:
					if value[2] != '': # idc
						# try:
						real_entity_type = std_v_field(p.std_dict, value[2])
						# except:
						# 	print(value)
						dis = value[2].strip().lower()
						for x in ['tt.', 'tt', 't.t', 't.t.']:
							if dis == x and key == p.WARD_ADMIN_LV:
								real_entity_type = 'Thị trấn'
								
						one_addr_list = [[value[3][0], value[4][0]], value[2].strip(), \
						real_entity_type, acronym_type(p.acronym_dict, value[1])+'_IDC']
						addr_list.append(one_addr_list)
					try:
						one_addr_list = [[value[3][-1], value[4][-1]], value[0].strip(), value[5], acronym_type(p.acronym_dict, value[1])]
					except IndexError:
						pass
						# print(addr_set)
						# print(value)
						# import sys
						# sys.exit(1)
				if key > p.WARD_ADMIN_LV:
					if len(value[3]) > 2:
						print("Naniiiii")
						print(addr_set)
						print("################################")
					if key <= p.GROUP_ADMIN_LV and not hasNumbers(value[0]):
						one_addr_list[2] = value[0].strip().title()
					else:
						one_addr_list[2] = value[0].strip()
				addr_list.append(one_addr_list)
			else:
				for i, begin_pos in enumerate(value[3]):
					end_pos = value[4][i]
					addr = raw_addr[begin_pos:end_pos].strip()
					one_addr_list = [[begin_pos, end_pos], addr, addr, 'NME']
					addr_list.append(one_addr_list)
		else: # others
			if key == 'country' and value[2] != -1:
				one_addr_list = [[value[2], value[3]], value[0].strip(), value[-1], 'CTR']
				addr_list.append(one_addr_list)
			if key == 'post_code':
				one_addr_list = [[value[2], value[3]], value[0].strip(), value[1].strip(), 'PSC']
				addr_list.append(one_addr_list)
			if key =='other':
				for i, begin_pos in enumerate(value[2]):
					end_pos = value[3][i]
					addr = raw_addr[begin_pos:end_pos].strip()
					one_addr_list = [[begin_pos, end_pos], addr, addr, 'OTH']
					addr_list.append(one_addr_list)

	return addr_list



with open(p._PICKLE_DIR + p.HANDLED_ADDR_LIST_PKL_PATH, 'rb') as f:
	addr_dict_list = pickle.load(f)
ner_addr_list = []
for addr_set in addr_dict_list: # becareful
	raw_address = addr_set['raw_address']
	addr_list = preprocess(addr_set)
	sorted_addr_list = sorted(addr_list, key=lambda x: x[0][1])

	ner_addr = ''
	for i, addr_meta in enumerate(sorted_addr_list):
		punc = ''
		real_punc = ''
		if i != len(sorted_addr_list) - 1 and sorted_addr_list[i + 1][0][0] > addr_meta[0][1]:
			punc = raw_address[addr_meta[0][1]:sorted_addr_list[i + 1][0][0]].strip()
			real_punc = punc.replace('\\', '/')

		ner_addr += construct_substr(addr_meta[1], addr_meta[2], addr_meta[3]) + '\n'
		next_punc = construct_substr(punc, real_punc, 'PUNC')
		if next_punc != '':
			ner_addr += next_punc + '\n'

	ner_addr_list.append((ner_addr, raw_address))

print('len(ner_addr_list) = ', len(ner_addr_list))
print(ner_addr_list[0])
with open(p._CLEAN_DATA_DIR_PATH + p.NER_ADDR_LIST_FILE_PATH, 'w', encoding='utf-8') as f:
	json.dump(ner_addr_list, f, indent=2, ensure_ascii=False)


