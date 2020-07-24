import os
import sys
lib_path = os.path.abspath(os.path.join('.'))
sys.path.append(lib_path)
sys.path.append(os.path.abspath(os.path.join('./address_graph')))

import json
import re
import pickle
import xlrd 
import pprint 

import ultis.parameters as p
from address_graph.addr_graph import AddressGraph

pp = pprint.PrettyPrinter(indent=4)
spec_input_dict = {}
unhandled_input_dict = {}
split_pattern = '∉'

def hasNumbers(str):
	return any(char.isdigit() for char in str)

def hasWords(str):
	return any(word.isalpha() and len(word) > 2 for word in str.split())

def handle_dup_substr(str):
	try:
		for i in range(len(str)//2, -1, -1):
			idx = str[i:].find(str[:i])
			if idx != -1 and idx < 5 and str[i] == ',':
				return str[i+idx:]
		return str
	except IndexError:
		return str

def remove_redunts(str):
	str_list = [x for x in str.split(',') if x.strip() != '']
	str = ''
	for sub_str in str_list:
		str += sub_str + ','
	return str[:-1].strip()

def handle_dash(str):
	if '-' not in str:
		return str
	else:
		sub_str_list = str.split('-')
		new_str = ''
		for i, sub_str in enumerate(sub_str_list):
			if i != len(sub_str_list) - 1:
				try:
					substr_before_dash = sub_str.strip().split(' ')[-1]
					substr_before_dash = ''.join(e for e in substr_before_dash if e.isalnum())
					# before_dash = substr_before_dash[-1]

					substr_after_dash = sub_str_list[i+1].strip().split(' ')[0]
					substr_after_dash = ''.join(e for e in substr_after_dash if e.isalnum())
					# after_dash = substr_after_dash[0]
				except IndexError:
					# spec_input_dict[hash_key] = address
					return ''
				# if (before_dash.isdigit() and after_dash.isdigit()) or \
				# Becareful
				if (hasNumbers(substr_before_dash) and hasNumbers(substr_after_dash)) or \
				(len(substr_after_dash) <= 2 and substr_after_dash.lower() not in p.BUILDING_PREFIXES) or \
				('bà rịa' in sub_str.lower() and 'vũng tàu' in sub_str_list[i+1].lower()) or \
				('ba ria' in sub_str.lower() and 'vung tau' in sub_str_list[i+1].lower()) or \
				('sao bọng' in sub_str.lower() and 'đăng hà' in sub_str_list[i+1].lower()) or \
				('sao bong' in sub_str.lower() and 'dang ha' in sub_str_list[i+1].lower()) or \
				('phan rang' in sub_str.lower() and 'tháp chàm' in sub_str_list[i+1].lower()) or \
				('phan rang' in sub_str.lower() and 'thap cham' in sub_str_list[i+1].lower()):
				# (len(substr_after_dash) < 3 and hasNumbers(substr_after_dash)) or \
					new_str += sub_str + '-'
				else:
					new_str += sub_str + ','
			else:
				new_str += sub_str
		return new_str

def norm(str):
	def sub_norm(str, key, replacement):
		str_list = str.split(key)
		new_str = ''
		for i, sub_str in enumerate(str_list):
			if i != len(str_list) - 1:
				new_str += sub_str
				try:
					cmp_str = str_list[i+1][0]
				except IndexError:
					cmp_str = ''
				if not cmp_str.isalpha():
					new_str += replacement
				else:
					new_str += key
			else:
				new_str += sub_str
		return new_str

	# str = unicodedata.normalize('NFC', str)
	str = sub_norm(str, 'oà', 'òa')
	str = sub_norm(str, 'oá', 'óa')
	str = sub_norm(str, 'uỷ', 'ủy')
	return str 

def clean_address(address, hash_key, non_accent_dict):
	address_ = address

	if '(' in address_ and ')' in address_:
		# print('aaa')
		# specfical input address logging
		spec_input_dict[hash_key] = address
		return ''

	lowered_address = address_.lower()
	if 'ward' in lowered_address or \
	'street' in lowered_address or \
	'city' in lowered_address or \
	'country' in lowered_address or \
	'province' in lowered_address or \
	'district' in lowered_address or \
	'commune' in lowered_address or \
	'town' in lowered_address or \
	'alley' in lowered_address or \
	'municipality' in lowered_address or \
	'room' in lowered_address or \
	'floor' in lowered_address or \
	'road' in lowered_address: # group
		# need unhandled logging
		spec_input_dict[hash_key] = address
		return ''

	address_ = address_.replace('–', '-')
	address_ = norm(handle_dash(address_))
	
	for non_accent, accent in non_accent_dict.items():
		# address_ = re.compile(re.escape(non_accent), re.IGNORECASE).sub(accent, address_)
		address_ = address_.replace(non_accent, accent)
	return address_

def raw_split_str_by_keyword(str, keyword, start_pos=0):
	# Find a keyword in a string
	# Need something to get raw addr
	# For example, str can be ' 295 Đ. Nguyễn Trãi '
	idx = str.lower().find(keyword.lower())
	if idx != -1:
		subfix_str = str[(idx + len(keyword)):]
		return subfix_str, str[:idx], str[idx:(idx + len(keyword))], idx + start_pos
	return str, str, None, 100000

def split_str_to_number_and_alphabet(field_addr):
	# str = rest_part + number_part + alpha_part
	# For example, ' 295B Bach Mai' = ' ' + '295B' + 'Bach Mai'
	numbers = re.findall(r'\d+', field_addr)
	fields = field_addr.split()
	isValid = True
	

	for field in fields:
		if field.isalpha():
			isValid = False
			break
	# Handle case like: 'Hai Chau 2'
	if not isValid and len(numbers) == 1 and field_addr.replace('.', ' ').strip()[-1].isdigit():
		return '', field_addr, ''
	else:
		first_number = numbers[0]
		last_number = numbers[-1]
		try:
			# Becareful
			dash_index = field_addr.rfind('-')
			need_split = True
			if dash_index != -1:
				after_dash_str = field_addr[dash_index + 1:].strip()
				space_idx = after_dash_str.find(' ')
				if space_idx != -1:
					after_dash_str = after_dash_str[:space_idx]
				number_pattern = re.compile(r'^[0-9]{0,3}[A-Za-z]{0,3}[0-9]{0,3}')
				if re.match(number_pattern, after_dash_str):
					need_split = False
			# print('bla = ', field_addr.replace('.', ' ').strip()[-1])
			if int(last_number) < 20 and \
			field_addr.replace('.', ' ').strip()[-1].isdigit() and \
			need_split:
				last_number = numbers[-2]
		except IndexError as ie:
			# print(ie)
			pass	

		split_space = -1
		for i in range(field_addr.rfind(last_number) + len(last_number), len(field_addr)):
			if field_addr[i] == ' ':
				split_space = i
				break
		number_part = None
		alpha_part = ''
		rest_part = field_addr[:field_addr.find(first_number)]
		if split_space != -1:
			number_part = field_addr[field_addr.find(first_number):split_space]
			alpha_part = field_addr[split_space:]
		else:
			number_part = field_addr[field_addr.find(first_number):] 

		for prefix in p.ignored_number_prefixes:
			idx = rest_part.lower().find(prefix)
			if idx != -1 and len(rest_part) - len(prefix) - idx < 5:
				return '', field_addr, ''
		return number_part, alpha_part, rest_part

def number_field_parse(number_list, viet_eng_ref, one_addr_dict, start_pos=0):
	# Parse string like 'number1/number2/number3'
	end_pos = start_pos
	# number_lv = viet_eng_ref['Ngõ'][1]
	for number in number_list:
		if viet_eng_ref['Ngõ'][1] not in one_addr_dict:
			one_addr_dict[viet_eng_ref['Ngõ'][1]] = [number, viet_eng_ref['Ngõ'][0], '',\
			[start_pos], [end_pos + len(number)], 'Ngõ']
		elif viet_eng_ref['Ngách'][1] not in one_addr_dict:
			one_addr_dict[viet_eng_ref['Ngách'][1]] = [number, viet_eng_ref['Ngách'][0], '', \
			[start_pos], [end_pos + len(number)], 'Ngách']
		elif viet_eng_ref['Hẻm'][1] not in one_addr_dict:
			one_addr_dict[viet_eng_ref['Hẻm'][1]] = [number, viet_eng_ref['Hẻm'][0], '', \
			[start_pos], [end_pos + len(number)], 'Hẻm']
		end_pos += len(number) + 1
		start_pos = end_pos
		# number_lv += 1
	return start_pos - 1 

def handle_number_alphabet_str(old_addr, hash_key, field_addr, viet_eng_ref, one_addr_dict, fields=None, start_pos=0, flag=True):
	# if a string = number_part + alpha_part as '295 Bach Mai'
	# '295' should be house_number,... and 'Bach Mai' should be street
	if flag:
		try:
			number_part, alpha_part, rest_part = split_str_to_number_and_alphabet(field_addr)
			# print('number_part = ', number_part)
			# print('alpha_part = ', alpha_part)
			# print('rest_part = ', rest_part)
		except IndexError:
			print('IndexError with field_addr = ', field_addr)
			spec_input_dict[hash_key] = old_addr
			return True
	else:
		[rest_part, number_part] = field_addr.split(split_pattern)
		# print('rest_part = ', rest_part)
		# print('number_part = ', number_part)
		alpha_part = ''

	# print('number_part = ', number_part)
	# print('alpha_part = ', alpha_part)
	# print('rest_part = ', rest_part)
	numbers = number_part.split()
	isValid = True
	for number in numbers:
		if number.isalpha() and len(number) > 2:
			isValid = False
			break

	if len(rest_part) > 2 or not isValid:
		# Special input logging
		# spec_input_dict[hash_key] = old_addr
		if p.NAME_ADMIN_LV not in one_addr_dict:
			one_addr_dict[p.NAME_ADMIN_LV] = [field_addr, 'name', '', \
			[fields[5]], [fields[5] + len(field_addr)], 'Tên']
		else:
			one_addr_dict[p.NAME_ADMIN_LV] = [field_addr + one_addr_dict[p.NAME_ADMIN_LV][0], \
			'name', '', [fields[5]] + one_addr_dict[p.NAME_ADMIN_LV][3], \
			[fields[5] + len(field_addr)] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']
		# return True
	# elif 
	else: # len(rest_part) <= 4, something like ' CT ', 'A', 'P', ' số'
		if '/' in rest_part or '\\' in rest_part: # Becareful
			number_part = rest_part + number_part
			rest_part = ''
		number_list = ['']
		split_mark = '/'
		if '\\' in number_part and '/' in number_part:
			# specfical input address logging
			spec_input_dict[hash_key] = old_addr
			return True

		elif '\\' in number_part:
			number_list = number_part.split('\\')
			split_mark = '\\'
		elif '/' in number_part:
			number_list = number_part.split('/')

		if len(number_list) > 3:
			return True
		# print('rest_part = ', rest_part)

		# Becareful
		if len(number_list) != 1: # Doesnt need???
			copied_number_list = number_list.copy()
			first_empty = 0
			list_to_pop = []
			if copied_number_list[0] == '' or copied_number_list[0] == ' ':
				for i in range(1, len(copied_number_list)):
					if copied_number_list[i] != '' and copied_number_list[i] != ' ':
						break
				number_list[i] = split_mark * i + number_list[i]
				first_empty = i

			for i in range(len(copied_number_list) -1, first_empty - 1, -1):
				if i in list_to_pop:
					continue
				if copied_number_list[i] == '' or copied_number_list[i] == ' ':
					empty_count = 1
					list_to_pop.append(i)

					while (copied_number_list[i-1] == '' or copied_number_list[i-1] == ' '):
						empty_count += 1
						list_to_pop.append(i-1)
						i -= 1
					number_list[i-1] += split_mark * empty_count
			for i in sorted(list_to_pop, reverse=True):
				number_list.pop(i)
			# Becareful
			for i in range(first_empty-1,-1,-1):
				number_list.pop(i)
		# print('then number list = ', number_list)

		number_list[0] = rest_part + number_list[0]
		if fields[0] != None:
			v_field = fields[0]
			e_field = fields[1]

			if len(number_list) != 1:
				if e_field[1] == viet_eng_ref['Số '][1]:
					if viet_eng_ref['Số '][1] not in one_addr_dict:
						# Becareful
						old_start_pos = fields[5]
						start_pos = 1 + number_field_parse(number_list[:-1], viet_eng_ref, one_addr_dict, start_pos=fields[5]+ len(fields[4]))
						one_addr_dict[e_field[1]] = [number_list[-1], e_field[0], fields[4], \
						[old_start_pos, start_pos], [old_start_pos + len(fields[4]), start_pos + len(number_list[-1])], \
						'Số']
					else:
						# Special input logging
						spec_input_dict[hash_key] = old_addr
						# number_field_parse(number_list, viet_eng_ref, one_addr_dict, fields=fields)
				else:
					# Becareful with this: 'Hẻm 19/5'
					if e_field[1] == viet_eng_ref['Hẻm'][1]:
						# Becareful
						one_addr_dict[e_field[1]] = [number_list[-1], e_field[0], fields[4], \
						[fields[5], fields[6] - len(number_list[-1])], [fields[5] + len(fields[4]), fields[6]], 'Hẻm']
						number_list.pop()
						number_field_parse(number_list, viet_eng_ref, one_addr_dict, start_pos=fields[5] + len(fields[4]))
					# Becareful
					elif e_field[1] == viet_eng_ref['Ngách'][1]:
						isOk = False
						if viet_eng_ref['Số '][1] not in one_addr_dict and len(number_list) == 3:
							one_addr_dict[viet_eng_ref['Số '][1]] = [number_list[-1], e_field[0], '', \
							[fields[6] - len(number_list[-1])], [fields[6]], 'Số']

							fields[6] -= (len(number_list[-1]) + 1)
							number_list.pop()
							isOk = True
						if len(number_list) == 2:
							isOk = True
						if isOk:
							one_addr_dict[viet_eng_ref['Ngách'][1]] = [number_list[-1], viet_eng_ref['Ngách'][0], fields[4], \
								[fields[5], fields[6] - len(number_list[-1])], \
								[fields[5] + len(fields[4]), fields[6]], 'Ngách']
							number_list.pop()
							number_field_parse(number_list, viet_eng_ref, one_addr_dict, start_pos=fields[5] + len(fields[4]))
						else:
							# logging
							return True
					elif e_field[1] == viet_eng_ref['Ngõ'][1]:
						one_addr_dict[viet_eng_ref['Ngõ'][1]] = [number_list[0], viet_eng_ref['Ngõ'][0], fields[4], \
							[fields[5], fields[5] + len(fields[4])], \
							[fields[5] + len(fields[4]), fields[5] + len(fields[4]) + len(number_list[0])], 'Ngõ']
						# number_list.pop(0)
						number_field_parse(number_list[1:], viet_eng_ref, one_addr_dict, \
							start_pos=fields[5] + len(fields[4]) + len(number_list[0]) + 1)
						# print('new one_addr_dict = ', one_addr_dict)
			else:
				if e_field[1] not in one_addr_dict:
					one_addr_dict[e_field[1]] = [rest_part + number_part, e_field[0], fields[4], \
					[fields[5], fields[5] + len(fields[4])], \
					[fields[5] + len(fields[4]), fields[5] + len(fields[4]) + len(rest_part + number_part)], std_v_field(p.std_dict, v_field)]
				else:
					#special input logging
					spec_input_dict[hash_key] = old_addr
					return True
					pass
		elif fields[0] == None:
			if len(number_list) != 1:
				if viet_eng_ref['Số '][1] not in one_addr_dict:
					start_pos = 1 + number_field_parse(number_list[:-1], viet_eng_ref, one_addr_dict, start_pos=fields[5])
					one_addr_dict[viet_eng_ref['Số '][1]] = [number_list[-1], 'house_number', '', \
					[start_pos], [start_pos + len(number_list[-1])], 'Số']
				else:
					number_field_parse(number_list, viet_eng_ref, one_addr_dict, start_pos=fields[5])
			else:
				# number_part = number_list[0] # Becareful
				# print('rest_part = ', rest_part)
				# print('number_part = ', number_part)
				if rest_part + number_part == '':
					pass
				elif rest_part.strip().lower() in p.BUILDING_PREFIXES or \
				(re.match(p.BUILDING_PATTERN, rest_part.strip() + number_part.strip()) and \
				viet_eng_ref['Tòa nhà'][1] not in one_addr_dict):
					one_addr_dict[viet_eng_ref['Tòa nhà'][1]] = [(rest_part + number_part), viet_eng_ref['Tòa nhà'][0], '', \
					[fields[5]], [fields[5] + len(rest_part + number_part)], 'Tòa nhà']
				elif viet_eng_ref['Số nhà'][1] not in one_addr_dict:
					# print('bleu bleu')
					one_addr_dict[viet_eng_ref['Số nhà'][1]] = [(rest_part + number_part), viet_eng_ref['Số nhà'][0], '', \
					[fields[5]], [fields[5] + len(rest_part + number_part)], 'Số']
				elif p.NAME_ADMIN_LV not in one_addr_dict:
					one_addr_dict[p.NAME_ADMIN_LV] = [(rest_part + number_part), 'name', '', \
					[fields[5]], [fields[5] + len((rest_part + number_part))], 'Tên']
				else:
					one_addr_dict[p.NAME_ADMIN_LV] = [(rest_part + number_part) + one_addr_dict[p.NAME_ADMIN_LV][0], \
					'name', '', [fields[5]] + one_addr_dict[p.NAME_ADMIN_LV][3], \
					[fields[5] + len(rest_part + number_part)] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']

		start_pos = fields[5] + len(rest_part + number_part)
		if re.match(p.BUILDING_PATTERN, alpha_part.strip()):
			if viet_eng_ref['Tòa nhà'][1] not in one_addr_dict:
				one_addr_dict[viet_eng_ref['Tòa nhà'][1]] = [alpha_part, viet_eng_ref['Tòa nhà'][0], '', \
				[start_pos], [start_pos + len(alpha_part)], 'Tòa nhà']
			elif p.NAME_ADMIN_LV not in one_addr_dict:
				one_addr_dict[p.NAME_ADMIN_LV] = [alpha_part, 'name', '', [start_pos], [start_pos + len(alpha_part)], 'Tên']
			else:
				one_addr_dict[p.NAME_ADMIN_LV] = [alpha_part + one_addr_dict[p.NAME_ADMIN_LV][0], \
				'name', '', [start_pos] + one_addr_dict[p.NAME_ADMIN_LV][3], \
				[start_pos + len(alpha_part)] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']
		elif alpha_part != '' and alpha_part != ' ': 
			# print('alpha_part = ', alpha_part)
			canBeStreet = True
			for prefix in p.ignored_number_prefixes:
				idx = alpha_part.strip().lower().find(prefix)
				if idx != -1 and idx < 2:
					canBeStreet = False
					break
			# print('canBeStreet = ', canBeStreet)
			# print('alpha_part = ', alpha_part)
			# print('433 one_addr_dict = ', one_addr_dict)
			if viet_eng_ref['Đường'][1] not in one_addr_dict and canBeStreet:
				one_addr_dict[viet_eng_ref['Đường'][1]] = [alpha_part, viet_eng_ref['Đường'][0], '', \
				[start_pos], [start_pos + len(alpha_part)], 'Đường']
			elif p.NAME_ADMIN_LV not in one_addr_dict:
				one_addr_dict[p.NAME_ADMIN_LV] = [alpha_part, 'name', '', \
				[start_pos], [start_pos + len(alpha_part)], 'Tên']
			else:
				one_addr_dict[p.NAME_ADMIN_LV] = [alpha_part + one_addr_dict[p.NAME_ADMIN_LV][0], \
				'name', '', [start_pos] + one_addr_dict[p.NAME_ADMIN_LV][3], \
				[start_pos + len(alpha_part)] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']
	
	# print('after number_part, alpha_part, rest_part = ', number_part, alpha_part, rest_part)
	# return number_part, alpha_part, rest_part
	return False

def use_std_graph(old_addr, graph, address, hash_key, city_list):
	def pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, i):
		raw_field_addr_list.pop(i)
		field_addr_list.pop(i)
		pos_list.pop(i)

	def add_pid(graph, pid, one_addr_dict):
		try:
			one_addr_dict['pid'] = pid
			if len(pid) == 2:
				if p.PROVINCE_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.PROVINCE_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.PROVINCE_ADMIN_LV][1] = graph.nodes[pid].label
			elif len(pid) == 3:
				if p.COUNTY_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.COUNTY_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.COUNTY_ADMIN_LV][1] = graph.nodes[pid].label
					pid = graph.nodes[pid].pid
				if p.PROVINCE_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.PROVINCE_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.PROVINCE_ADMIN_LV][1] = graph.nodes[pid].label
			elif len(pid) == 5:
				if p.WARD_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.WARD_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.WARD_ADMIN_LV][1] = graph.nodes[pid].label
					pid = graph.nodes[pid].pid
				if p.COUNTY_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.COUNTY_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.COUNTY_ADMIN_LV][1] = graph.nodes[pid].label
					pid = graph.nodes[pid].pid
				if p.PROVINCE_ADMIN_LV in one_addr_dict:
					one_addr_dict[p.PROVINCE_ADMIN_LV].append(graph.nodes[pid].address)
					one_addr_dict[p.PROVINCE_ADMIN_LV][1] = graph.nodes[pid].label
		except KeyError:
			print('key_error with one_addr_dict = ', one_addr_dict)
			print('key_error with pid = ', pid)
			print('key_error with graph.nodes[pid].address = ', graph.nodes[pid].address)

	subfix = ''
	try:
		field_addr_list = address.split(',')
	except AttributeError:
		print("old_addr = ", old_addr)
		print("address = ", address)
	raw_field_addr_list = handle_dash(old_addr.replace('–', '-')).split(',')
	# print('len field_addr_list = ', len(field_addr_list))
	# print('len raw_field_addr_list = ', len(raw_field_addr_list))
	# print('len old_addr = ', len(old_addr))
	# print('len address = ', len(address))
	# print('address = ', address)
	# print('old_addr = ', old_addr)
	pos_list = [m.start() + 1 for m in re.finditer(',', address)]
	pos_list.insert(0,0)
	one_addr_dict = {}
	# print('1 field_addr_list = ', field_addr_list)
	hasCity = False
	same_field_addr_list = field_addr_list.copy()
	original_leng = len(field_addr_list)
	# for i in range(len(field_addr_list)-1, -1, -1):
	for i, field_addr in enumerate(reversed(same_field_addr_list)):
		if i >= len(same_field_addr_list)//2:
			break
		idx = original_leng - 1 - i
		field_addr = field_addr_list[idx].lower().replace(' ', '')
		if field_addr == 'vietnam' or \
		field_addr == 'việtnam' or \
		field_addr == 'vn':
			one_addr_dict['country'] = [raw_field_addr_list[idx], field_addr_list[idx], \
			pos_list[idx], pos_list[idx] + len(raw_field_addr_list[idx]), 'Việt Nam']
			pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
		# elif re.match(r'^[0-9\-\+\,\s]{2,25}$', field_addr_list[i].replace(' ', '')):
		else:
			# print('field_addr_list[i] = ', field_addr_list[i])
			m = re.match(r'^[0-9\-\+\,\s]{3,25}', field_addr_list[idx])
			# print('m = ', m)
			if m:
				idxes = m.span()
				matched = field_addr_list[idx][idxes[0]:idxes[1]]
				redunt = field_addr_list[idx][:idxes[0]] + field_addr_list[idx][idxes[1]:]
				if '+' not in matched and \
				'-' not in matched and \
				len(matched.replace(' ','')) > 4 and \
				len(matched.replace(' ','')) < 7:
					if 'post_code' not in one_addr_dict:
						one_addr_dict['post_code'] = [matched, matched, \
						pos_list[idx], pos_list[idx] + len(matched)]
					else:
						#special case logging
						spec_input_dict[hash_key] = old_addr
						return None
				else:
					if 'other' not in one_addr_dict:
						one_addr_dict['other'] = [matched, matched, \
						[pos_list[idx]], [pos_list[idx] + len(matched)]]
					else:
						others = one_addr_dict['other']
						one_addr_dict['other'] = [matched + others[0], matched + others[1], \
						[pos_list[idx]] + others[2], [pos_list[idx] + len(matched)] + others[3]]
				if redunt.replace(' ', '') == '':
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				else:
					raw_field_addr_list[idx] = redunt
					field_addr_list[idx] = redunt
				break
			elif not hasCity:
				for key, replacement in p.repl_ignorecase_municipalities:
					address = re.compile(re.escape(key), re.IGNORECASE).sub(replacement, address)
				for city in city_list:
					if city.lower() in address.lower():
						hasCity = True
						break

	municipalities = {'hà nội', 'hải phòng', 'đà nẵng', 'hồ chí minh', 'cần thơ'}
	# print('2 field_addr_list = ', field_addr_list)
	# print('address = ', address)
	try:
		# 'Phường Thanh Bình TP Điện Biên tỉnh Điện Biên'
		province_prefix_list = p.province_prefix_list

		province = None
		province_label = None

		county = None
		county_label = None

		# print('field_addr_list = ', field_addr_list)
		# last_field = field_addr_list[-1]
		same_field_addr_list = field_addr_list.copy()
		original_leng = len(field_addr_list)
		
		canStop = False
		for i, field_addr in enumerate(reversed(same_field_addr_list)):
			idx = original_leng - 1 - i
			last_field = field_addr
			for key, replacement in p.repl_ignorecase_municipalities:
				last_field = re.compile(re.escape(key), re.IGNORECASE).sub(replacement, last_field)

			for prefix, label in province_prefix_list:
				res, rest, flag, pos = raw_split_str_by_keyword(last_field, prefix, pos_list[idx])
				# print('res = ' + res)
				# print('prefix = ' + prefix)

				if flag != None:
					if res.strip() == '':
						# Special input logging
						spec_input_dict[hash_key] = old_addr
						return None
					last_field = None
					# res = res.strip().lower()
					# print('res = ' + res)
					if label == 'municipality' and res.strip().lower() not in municipalities:
						if graph.search(province=None, county=res, county_type='provincial_city', ward=None)[0] != None:
							canStop = True
							county = res
							county_label = 'provincial_city'
							pre = ''
							if len(rest) < 2:
								pre = rest
							one_addr_dict[p.COUNTY_ADMIN_LV] = [res, county_label, pre+flag, \
							[pos_list[idx], pos_list[idx] + len(pre+flag)], \
							[pos_list[idx] + len(pre+flag), pos_list[idx] + len(raw_field_addr_list[idx])]]
					elif graph.search(province=res, province_type=label, county=None, ward=None)[0] != None:
						canStop = True
						province = res
						province_label = label
						pre = ''
						if len(rest) < 2:
							pre = rest
						one_addr_dict[p.PROVINCE_ADMIN_LV] = [res, province_label, pre+flag, \
						[pos_list[idx], pos_list[idx] + len(pre+flag)], \
						[pos_list[idx] + len(pre+flag), pos_list[idx] + len(raw_field_addr_list[idx])]]
					# Becareful
					else:
						return None

					if len(rest) < 2:
						pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
					else:
						raw_field_addr_list[-i] = rest
						field_addr_list[-i] = rest
					break
			if canStop:
				break

		# Becareful
		last_field = field_addr_list[-1]
		if last_field != None and \
		province == None and \
		graph.search(province=last_field, province_type=None, county=None, ward=None)[0] != None:
			province = last_field.strip()
			one_addr_dict[p.PROVINCE_ADMIN_LV] = [raw_field_addr_list[-1], province_label, '', \
						[pos_list[-1]], [pos_list[-1] + len(raw_field_addr_list[-1])]]
			pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, -1)

		# print('3 field_addr_list = ', field_addr_list)

		county_prefix_list = p.county_prefix_list

		if county == None and county_label == None:
			same_field_addr_list = field_addr_list.copy()
			original_leng = len(field_addr_list)
			
			canStop_1 = False
			for i, field_addr in enumerate(reversed(same_field_addr_list)):
				idx = original_leng - 1 - i
				for prefix, label in county_prefix_list:
					res, rest, flag, _ = raw_split_str_by_keyword(field_addr, prefix, pos_list[idx])
					if flag != None: 
						if res.strip() == '':
							# Special input logging
							spec_input_dict[hash_key] = old_addr
							return None
						res_node = graph.search(province=province, county=res, county_type=label, ward=None)[0]
						if res_node != None and len(res_node[0].id) > 2: 
							county = res
							county_label = label
							pre = ''
							if len(rest) < 2:
								pre = rest
							one_addr_dict[p.COUNTY_ADMIN_LV] = [res, county_label, pre+flag, \
							[pos_list[idx], pos_list[idx] + len(pre+flag)], [pos_list[idx] + len(pre+flag), pos_list[idx] + len(raw_field_addr_list[idx])]]
							canStop_1 = True
						else:
							return None
						if len(rest) < 2:
							pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
						else:
							try:
								raw_field_addr_list[idx] = rest
								field_addr_list[idx] = rest
							except IndexError:
								pass
						break
				if canStop_1:
					break

		# print('4 field_addr_list = ', field_addr_list)

		ward_prefix_list = p.ward_prefix_list

		ward = None
		ward_label = None
		canStop_2 = False
		same_field_addr_list = field_addr_list.copy()
		original_leng = len(field_addr_list)

		for i, field_addr in enumerate(reversed(same_field_addr_list)):
			for prefix, label in ward_prefix_list:
				# sub_field, pre_field, field_type, field_pos = raw_split_str_by_keyword(field_addr, prefix)
				idx = original_leng - 1 - i
				res, rest, flag, _ = raw_split_str_by_keyword(field_addr, prefix, pos_list[idx])
				if flag != None:
					# print('province = ', province)
					# print('county = ', county)
					# print('county_label = ', county_label)
					# print('res = ', res)
					# print('label = ', label)
					if res.strip() == '':
						# Special input logging
						spec_input_dict[hash_key] = old_addr
						return None
					res_node = graph.search(province=province, county=county, county_type=county_label, ward=res, ward_type=label)[0]
					if res_node != None and len(res_node[0].id) > 3:
						ward = res
						ward_label = label
						pre = ''
						if len(rest) < 2:
							pre = rest
						one_addr_dict[p.WARD_ADMIN_LV] = [res, ward_label, pre+flag, \
						[pos_list[idx], pos_list[idx] + len(pre+flag)], [pos_list[idx] + len(pre+flag), pos_list[idx] + len(raw_field_addr_list[idx])]]
						canStop_2 = True
						
					else:
						return None
					if len(rest) < 2:
						pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
					else:
						try:
							raw_field_addr_list[idx] = rest
							field_addr_list[idx] = rest
						except IndexError:
							pass
					break
			if canStop_2:
				break
		# print('after: ', field_addr_list)
		# print('province = ', province)
		# print('county = ', county)
		# print('ward = ', ward)
		
	except TypeError as te:
		return None
	except IndexError as ie:
		print (ie)
		# print('address = ', address)
		# print('hash_key = ', hash_key)
		# print('field_addr_list = ', field_addr_list)
		return None
	# print(field_addr_list)

	if county == None and ward == None:
		try:
			res_nodes = \
			[(graph.search(province=province, county=field_addr_list[-1], ward=field_addr_list[-2]), 0),\
			(graph.search(province=province, county=field_addr_list[-2], ward=field_addr_list[-1]), 1)]
		except:
			try:
				res_nodes = \
				[(graph.search(province=province, county=field_addr_list[-1], ward=None), 2),
				(graph.search(province=province, county=None, ward=field_addr_list[-1]), 3)]
			except:
				return None
		# print(res_nodes)
		# for x in res_nodes[0][0][0]:
		# 	print(x.id)
		if res_nodes[0][0][0] != None and len(res_nodes[0][0][0]) == 1:
			max_id_len = -1
			field_check = 0
			res_node = None
			i = -1
			# print('res_node = ', res_nodes)
			try:
				for (node, check), i in res_nodes:
					if len(node[0].id) > max_id_len:
						# print(node[0].id)
						max_id_len = len(node[0].id)
						res_node = node
						mark = i
						field_check = check
			except TypeError:
				pass
			# one_addr_dict["pid"] = res_node[0].id
			# add_pid(graph, res_node[0].id, one_addr_dict)
			if mark == 0:
				if field_check % 4 == 1:
					# one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], field_addr_list[idx], \
					# county_label, pos_list[idx], pos_list[idx] + len(raw_field_addr_list[idx])]
					idx = -2
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				elif field_check % 4 == 2:
					idx = -1
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				elif field_check % 4 == 3:
					idx = -1
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					idx = -2
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, -1)
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, -1)
			elif mark == 1:
				if field_check % 4 == 1:
					idx = -1
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				elif field_check % 4 == 2:
					idx = -2
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				elif field_check % 4 == 3:
					idx = -2
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					idx = -1
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, -1)
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, -1)
			elif mark == 2:
				if field_check % 4 == 2:
					idx = -1
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
			elif mark == 3:
				if field_check % 2 == 1:
					idx = -1
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
			add_pid(graph, res_node[0].id, one_addr_dict)
		else:
			return None
	elif ward == None and county != None:
		try:
			res_node, field_check = graph.search(province=province, county=county, county_type=county_label, ward=field_addr_list[-1])
			if res_node == None or len(res_node) != 1 or len(res_node[0].id) < 3:
				return None
			else:
				# one_addr_dict["pid"] = res_node[0].id
				# add_pid(graph, res_node[0].id, one_addr_dict)
				if field_check % 2 == 1:
					idx = -1
					ward = raw_field_addr_list[idx]
					one_addr_dict[p.WARD_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				add_pid(graph, res_node[0].id, one_addr_dict)
		except:
			res_node = graph.search(province=province, county=county, county_type=county_label, ward=None)[0]
			if res_node == None or len(res_node) != 1:
				return None
			else:
				# one_addr_dict["pid"] = res_node[0].id
				add_pid(graph, res_node[0].id, one_addr_dict)
	elif ward != None and county == None:
		try:
			res_node, field_check = graph.search(province=province, county=field_addr_list[-1], ward=ward, ward_type=ward_label)
			# print('res_node = {}'.format(res_node))
			if res_node == None or len(res_node) != 1 or len(res_node[0].id) < 5:
				return None
			else:
				# one_addr_dict["pid"] = res_node[0].id
				# add_pid(graph, res_node[0].id, one_addr_dict)
				if field_check % 4 >= 2:
					idx = -1
					county = raw_field_addr_list[idx]
					one_addr_dict[p.COUNTY_ADMIN_LV] = [raw_field_addr_list[idx], None, '', \
					[pos_list[idx]], [pos_list[idx] + len(raw_field_addr_list[idx])]]
					pop_three_lists(raw_field_addr_list, field_addr_list, pos_list, idx)
				add_pid(graph, res_node[0].id, one_addr_dict)
		except:
			res_node = graph.search(province=province, county=None, ward=ward, ward_type=ward_label)[0]
			if res_node == None or len(res_node) != 1:
				return None
			else:
				# one_addr_dict["pid"] = res_node[0].id
				add_pid(graph, res_node[0].id, one_addr_dict)
	else: # ward != None and county != None
		res_node = graph.search(province=province, county=county, county_type=county_label, ward=ward, ward_type=ward_label)[0]
		# print('res_node = {}'.format(res_node))
		if res_node == None or len(res_node) != 1 or len(res_node[0].id) < 5:
			return None
		else:
			# one_addr_dict["pid"] = res_node[0].id
			add_pid(graph, res_node[0].id, one_addr_dict)
			# print('tata')

	# Becareful
	mess_wards = p.mess_wards
	if ward != None:
		for field_addr in field_addr_list:
			for mess_ward in mess_wards:
				if ward.lower().strip() == mess_ward and not field_addr.isdigit():
					res_node = graph.search(ward=field_addr)
					# print('927 ', res_node[0])
					if res_node[0] != None:
						return None

	def last_check(field_addr_list):
		province_prefix_list = [('tp.', 'municipality'), \
								('tp', 'municipality'), \
								('t.p.', 'municipality'), \
								('t.p', 'municipality')]

		county_prefix_list = [('tp.', 'provincial_city'), \
							('tp', 'provincial_city'), \
							('t.p.', 'provincial_city'), \
							('t.p', 'provincial_city'), \
							('h.', 'county'), \
							('q.', 'district'), \
							(' q ', 'district'), \
							('tx.', 'town'), \
							('t.x.', 'town'), \
							('t.x', 'town')]

		ward_prefix_list = [('p.', 'ward'), \
							(' p ', 'ward'), \
							('thị trấn', 'township'), \
							('x.', 'commune')]

		for field_addr in field_addr_list:
			for key, replacement in p.repl_ignorecase_municipalities:
				field_addr = re.compile(re.escape(key), re.IGNORECASE).sub(replacement, field_addr)
			for city in municipalities:
				if city in field_addr.lower():
					return False
			for prefix, label in province_prefix_list:
				res, rest, flag, _ = raw_split_str_by_keyword(field_addr, prefix)
				if flag != None and p.PROVINCE_ADMIN_LV in one_addr_dict: 
					return False
			for prefix, label in county_prefix_list:
				res, rest, flag, _ = raw_split_str_by_keyword(field_addr, prefix)
				if flag != None and p.COUNTY_ADMIN_LV in one_addr_dict: 
					return False
			for prefix, label in ward_prefix_list:
				res, rest, flag, _ = raw_split_str_by_keyword(field_addr, prefix)
				if flag != None and p.WARD_ADMIN_LV in one_addr_dict: 
					return False
		return True

	if not last_check(field_addr_list):
		return None

	next_raw_addr = ''
	for i in range(p.WARD_ADMIN_LV, p.PROVINCE_ADMIN_LV - 1, -1):
		try:
			addr = one_addr_dict[i]
			next_raw_addr += addr[2] + addr[0] + ','
		except KeyError:
			pass

	# print('next_raw_addr = ', next_raw_addr)
	others = ['other', 'post_code', 'country']
	for str in others:
		if str in one_addr_dict:
			next_raw_addr += one_addr_dict[str][0] + ','

	one_addr_dict['next_raw_addr'] = next_raw_addr[:-1].strip()
	# print('first one_addr_dict = ', one_addr_dict)
	return field_addr_list, pos_list, one_addr_dict

def parse_one_field(old_addr, hash_key, address, field_addr, viet_eng_ref, one_addr_dict, start_pos):
	# Parse each field
	small_one_field_list = []
	field_addr_ = field_addr
	first_start_pos = start_pos
	# [[admin_level, sub_field, pre_field, field_type, start_pos, end_type_pos]]
	canContinue2 = True
	while canContinue2:
		isFirst = True
		canContinue2 = False
		canContinue = True
		sub_field = field_addr_
		# print('sub_field = ', sub_field)
		small_start_pos = start_pos
		# print('small_start_pos = ', small_start_pos)
		e_field_set = set()
		while canContinue:
			canContinue = False
			one_small_field = []
			for v_field, e_field in viet_eng_ref.items():
				# if v_field.lower().strip() == field_addr[i:].lower().strip():
				# 	break	

				# if v_field == 'Khu ' and 'quân khu' in sub_field.lower() or \
				# 	(p.GROUP_ADMIN_LV in one_addr_dict and p.BUILDING_NAME_ADMIN_LV in one_addr_dict):
				# 	# Becareful
				# 	continue

				# if v_field == 'Đội' and 'tỉnh đội' in sub_field.lower():
				# 	# Becareful
				# 	continue

				old_sub_field = sub_field
				sub_field, pre_field, field_type, field_pos = raw_split_str_by_keyword(sub_field, v_field, start_pos=small_start_pos)
				isName = False
				for name in p.must_be_name_strings:
					if name in sub_field.lower():
						isName = True
						break
				if isName:
					sub_field = old_sub_field
					continue

				if v_field == 'Số ':
					# Avoid 'Đường số', 'Kiot số',...
					# Becareful
					if small_one_field_list and field_pos >= small_one_field_list[-1][6] and \
					(field_pos - small_one_field_list[-1][6]) < 3:
						# print('small_one_field_list = ', small_one_field_list)
						# print('small_one_field_list[-1][6] = ', small_one_field_list[-1][6])
						# print('field_pos = ', field_pos)
						continue
					shouldContinue = False
					for prefix in p.ignored_number_prefixes:
						idx = pre_field.strip().lower().find(prefix)
						# print('pre_field = ', pre_field)
						# print('prefix = ', prefix)
						if idx != -1 and len(pre_field[idx + len(prefix) + 1:].strip()) < 1:
							shouldContinue = True
							break
					if shouldContinue:
						continue

				if field_type != None and sub_field.replace(' ', '') != '': #sub_field != '' and sub_field != ' ': # and e_field[1] not in one_addr_dict:
					if isFirst:
						# print('pre_field = ', pre_field)
						# print('old_addr = ', old_addr)
						isFirst = False
						# if pre_field.strip() != '':
						if not small_one_field_list or small_one_field_list[0][1] != None:
							first_small_field = []
							first_small_field.append(None)
							first_small_field.append(None)
							first_small_field.append(pre_field)
							first_small_field.append(pre_field)
							first_small_field.append(None)
							first_small_field.append(first_start_pos)
							first_small_field.append(first_start_pos + len(pre_field))
							small_one_field_list.insert(0, first_small_field)
						elif small_one_field_list[0][1] == None:
							small_one_field_list[0][2] = pre_field
							small_one_field_list[0][3] = pre_field
							small_one_field_list[0][5] = first_start_pos
							small_one_field_list[0][6] = first_start_pos + len(pre_field)
					if v_field.lower() not in e_field_set:
						# Becareful
						e_field_set.add(v_field.lower())
						one_small_field.append(v_field)
						one_small_field.append(e_field)
						one_small_field.append(sub_field)
						one_small_field.append(pre_field)
						one_small_field.append(field_type)
						one_small_field.append(field_pos)
						i = field_pos + len(field_type)
						one_small_field.append(i)
						canContinue2 = True
						canContinue = True
						small_start_pos = i
					else:
						continue
					break
			# print('1019 one_small_field = ', one_small_field)		
			if one_small_field:
				small_one_field_list.append(one_small_field)

		try:
			# if small_one_field_list[0][3].strip() != '':
			# print(small_one_field_list[0][3])
			field_addr_ = small_one_field_list[0][3]
		except IndexError:
			canContinue2 = False

	# print('small_one_field_list = ', small_one_field_list)	
	# print('start_pos = ', start_pos)
	if not small_one_field_list:
		sorted_small_field_list = [[None, None, field_addr, field_addr, None, first_start_pos, first_start_pos + len(field_addr)]]
	else:
		sorted_small_field_list = sorted(small_one_field_list, key=lambda x: x[5])
		start_point = 0
		if sorted_small_field_list[0][0] == None:
			start_point = 1
		for i in range(start_point, len(sorted_small_field_list)-1):
			addr = field_addr[sorted_small_field_list[i][6]-start_pos:sorted_small_field_list[i+1][5]-start_pos]
			sorted_small_field_list[i][2] = addr
			sorted_small_field_list[i][6] += len(addr)

		sorted_small_field_list[-1][6] += len(sorted_small_field_list[-1][2])
	if sorted_small_field_list[0][2].strip() == '':
		sorted_small_field_list.pop(0)
	# print('sorted_small_field_list = ', sorted_small_field_list)
	return sorted_small_field_list

def handle_khu_lv(sorted_small_field_list, one_addr_dict):
	for i, small_field in enumerate(sorted_small_field_list):
		if small_field[0] == 'Khu ':
			if p.GROUP_ADMIN_LV in one_addr_dict and p.BUILDING_NAME_ADMIN_LV in one_addr_dict:
				sorted_small_field_list[i][1][1] = p.NAME_ADMIN_LV
				sorted_small_field_list[i][1][0] = 'name'
			elif p.GROUP_ADMIN_LV in one_addr_dict:
				sorted_small_field_list[i][1][1] = p.BUILDING_NAME_ADMIN_LV
				sorted_small_field_list[i][1][0] = 'building_name'
			elif p.BUILDING_NAME_ADMIN_LV in one_addr_dict:
				sorted_small_field_list[i][1][1] = p.GROUP_ADMIN_LV
				sorted_small_field_list[i][1][0] = 'group'
			else:
				prev_small_field = None
				next_small_field = None
				try:
					j = i
					while sorted_small_field_list[j+1][1] == None:
						j += 1
					next_small_field = sorted_small_field_list[j+1]
				except IndexError:
					pass
				try:
					j = i
					while sorted_small_field_list[j-1][1] == None:
						j -= 1
					prev_small_field = sorted_small_field_list[j-1]
				except IndexError:
					pass

				# try:
				if next_small_field != None and prev_small_field != None:
					if (next_small_field[1][1] + prev_small_field[1][1])/2 <= p.viet_eng_ref['Khối'][1]:
						sorted_small_field_list[i][1][1] = p.GROUP_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'group'
					else:
						sorted_small_field_list[i][1][1] = p.BUILDING_NAME_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'building_name'
				elif next_small_field != None:
					if next_small_field[1][1] >= p.viet_eng_ref['Ngõ'][1]:
						sorted_small_field_list[i][1][1] = p.BUILDING_NAME_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'building_name'	
					else:
						sorted_small_field_list[i][1][1] = p.GROUP_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'group'
				elif prev_small_field != None:
					if prev_small_field[1][1] <= p.viet_eng_ref['Đường'][1]:
						sorted_small_field_list[i][1][1] = p.GROUP_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'group'
					else:
						sorted_small_field_list[i][1][1] = p.BUILDING_NAME_ADMIN_LV
						sorted_small_field_list[i][1][0] = 'building_name'	
				else:
					sorted_small_field_list[i][1][1] = p.BUILDING_NAME_ADMIN_LV
					sorted_small_field_list[i][1][0] = 'building_name'
				# except TypeError:
				# 	print('sorted_small_field_list = ', sorted_small_field_list)
			break

def std_v_field(std_dict, str):
	return std_dict[str.lower().strip()]

def parse_fields(small_field_list, old_addr, hash_key, address, viet_eng_ref, one_addr_dict):
	if not small_field_list:
		pass
	else:
		admin_level_set = set([x[1][1] for x in small_field_list if x[1] != None])

		# sorted_small_field_list = sorted(small_field_list, key=lambda x: x[5]) # Becareful: Need to sort or not???
		sorted_small_field_list = small_field_list
		# handle_khu_lv(sorted_small_field_list, admin_level_set) # This will update sorted_small_field_list

		unhandled_field_list = []
		handled_field_list = []
		for i in range(len(sorted_small_field_list)):
			if sorted_small_field_list[i][0] == None:
				unhandled_field_list.append(sorted_small_field_list[i])
			else:
				handled_field_list.append(sorted_small_field_list[i])

		handle_khu_lv(handled_field_list, admin_level_set)
		# Handled one_small_field with v_field != None first
		for one_small_field in sorted(handled_field_list, key=lambda x: x[1][1], reverse=True):
			# print(one_small_field)
			addr = one_small_field[2]
			# print(addr)
			if hasNumbers(addr) and one_small_field[1][1] != p.GROUP_ADMIN_LV and one_small_field[1][1] != viet_eng_ref['Đường'][1]:
				flag = True
				if one_small_field[1][1] != viet_eng_ref['Đường'][1] and \
				viet_eng_ref['Đường'][1] not in one_addr_dict:
				 # and one_small_field[1][1] < p.GROUP_ADMIN_LV:
					try:
						number_part, alpha_part, rest_part = split_str_to_number_and_alphabet(addr)
						# print('here number:', number_part)
						# print('here alpha_part:', alpha_part)
						# print('here rest_part:', rest_part)
					except IndexError:
						print('IndexError with field_addr = ', field_addr)
						spec_input_dict[hash_key] = old_addr
						return True
					if alpha_part.replace(' ', '') != '':
						if not hasWords(number_part):
							addr = rest_part + split_pattern + number_part
							flag = False
						else:
							addr = rest_part + number_part
						new_small_field = [None, None, alpha_part, alpha_part, None, one_small_field[6]-len(alpha_part), one_small_field[6]]
						one_small_field[2] = addr
						one_small_field[6] -= len(alpha_part)
						# print('new_small_field = ', new_small_field)
						unhandled_field_list.append(new_small_field)
						
				if hasWords(addr):
					if one_small_field[1][1] not in one_addr_dict:
						one_addr_dict[one_small_field[1][1]] = [addr, one_small_field[1][0], \
						one_small_field[4], [one_small_field[5], one_small_field[5]+len(one_small_field[4])], \
						[one_small_field[5]+len(one_small_field[4]),one_small_field[6]], std_v_field(p.std_dict, one_small_field[0])]
					else:
						spec_input_dict[hash_key] = old_addr
						return True
				else:
					isSpecial = handle_number_alphabet_str(old_addr, hash_key, addr, viet_eng_ref, one_addr_dict, fields=one_small_field, flag=flag)
					if isSpecial:
						return True
			else:
				if one_small_field[1][1] not in one_addr_dict:
					one_addr_dict[one_small_field[1][1]] = [addr, one_small_field[1][0], \
					one_small_field[4], [one_small_field[5], one_small_field[5]+len(one_small_field[4])], \
					[one_small_field[5]+len(one_small_field[4]),one_small_field[6]], std_v_field(p.std_dict, one_small_field[0])]
				else:
					# Becareful
					# spec input logging
					spec_input_dict[hash_key] = old_addr
					return True

		# Then handled one_small_field with v_field == None 
		# print('unhandled_field_list = ', unhandled_field_list)
		for field in sorted(unhandled_field_list, key=lambda x: x[5], reverse=True):
		# unhandled_field_list.reverse()
		# for field in unhandled_field_list:
			addr = field[2]
			start_pos = field[5]
			end_pos = field[6]
			if re.match(r'^[\+]{1,2}[0-9\s\-]{5,25}$', addr.strip()):
				if '+' in addr or len(addr) > 6:
					# special input logging
					spec_input_dict[hash_key] = old_addr
					if 'other' not in one_addr_dict:
						one_addr_dict['other'] = [addr, addr, \
						[start_pos], [end_pos]]
					else:
						others = one_addr_dict['other']
						one_addr_dict['other'] = [addr + others[0], addr + others[1], \
						[start_pos] + others[2], [end_pos] + others[3]]	
				else:
					return True
					# if 'post_code' not in one_addr_dict:
					# 	one_addr_dict['post_code'] = [addr, addr, start_pos, end_pos]
					# else:
					# 	return True
			
			else:
				str_before_building_prefix = ''
				new_end_pos = end_pos
				for building_prefix in p.BUILDING_PREFIXES:
					# print('addr = ', addr)
					idx = addr.lower().find(building_prefix)
					if idx != -1:
						str_after_building_prefix = addr[idx:]
						if p.BUILDING_NAME_ADMIN_LV not in one_addr_dict:
							str_before_building_prefix = addr[:idx]
							new_end_pos = idx

							one_addr_dict[viet_eng_ref['Tòa nhà'][1]] = \
							[str_after_building_prefix, viet_eng_ref['Tòa nhà'][0], '', \
							[idx], [end_pos], 'Tòa nhà']
						else:
							str_before_building_prefix = addr
						break
				if str_before_building_prefix.strip() != '':
					if p.NAME_ADMIN_LV not in one_addr_dict:
						one_addr_dict[p.NAME_ADMIN_LV] = [str_before_building_prefix, 'name', 'Tên', [start_pos], [new_end_pos], 'Tên']
					else:
						one_addr_dict[p.NAME_ADMIN_LV] = [str_before_building_prefix + one_addr_dict[p.NAME_ADMIN_LV][0], \
						'name', 'Tên', [start_pos] + one_addr_dict[p.NAME_ADMIN_LV][3], \
						[new_end_pos] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']
				# Becareful
				elif hasNumbers(addr):
					isSpecial = handle_number_alphabet_str(old_addr, hash_key, addr, viet_eng_ref, one_addr_dict, fields=field)
					if isSpecial:
						return True
				else:
					canBeStreet = True
					for prefix in p.ignored_number_prefixes:
						idx = addr.strip().lower().find(prefix)
						if idx != -1 and idx < 2:
							canBeStreet = False
							break
					if viet_eng_ref['Đường'][1] not in one_addr_dict and canBeStreet:
						one_addr_dict[viet_eng_ref['Đường'][1]] = \
						[addr, viet_eng_ref['Đường'][0], '', \
						[start_pos], [end_pos], 'Đường']
					elif p.NAME_ADMIN_LV not in one_addr_dict:
						one_addr_dict[p.NAME_ADMIN_LV] = [addr, 'name', 'Tên', [start_pos], [end_pos], 'Tên']
					else:
						one_addr_dict[p.NAME_ADMIN_LV] = [addr + one_addr_dict[p.NAME_ADMIN_LV][0], \
						'name', 'Tên', [start_pos] + one_addr_dict[p.NAME_ADMIN_LV][3], \
						[end_pos] + one_addr_dict[p.NAME_ADMIN_LV][4], 'Tên']

	# print('lasst = ', one_addr_dict)
	return False

def clean_addr_dict(one_addr_dict, viet_eng_ref):
	# Becareful
	others = ['other', 'post_code', 'country']
	for str in others:
		if str in one_addr_dict:
			one_addr_dict[str][0] = one_addr_dict[str][0].strip()
			one_addr_dict[str][1] = one_addr_dict[str][1].strip()
	keys = list(one_addr_dict.keys())
	for key in keys:
		if isinstance(key, int):
			if one_addr_dict[key][0].strip() == '':
				del one_addr_dict[key]
				continue
			#Becareful
			addr_list = [x for x in one_addr_dict[key][-1].replace('–','-').split('-') if x.strip() != '']
			address = ''
			for addr in addr_list:
				address += addr + '-'

			address = remove_redunts(address[:-1])
			if key <= p.GROUP_ADMIN_LV and not hasNumbers(address):
				address = address.title()
			one_addr_dict[key][-1] = address
			one_addr_dict[key][0] = one_addr_dict[key][0].strip()
	return one_addr_dict

def parse_address(old_addr, graph, address, hash_key, viet_eng_ref, city_list):
	# Parse an address by handle one by one field.
	try:
		field_addr_list, pos_list, one_addr_dict = use_std_graph(old_addr, graph, address, hash_key, city_list)
		# print('field_addr_list, pos_list, one_addr_dict = ', field_addr_list, pos_list, one_addr_dict)
	except TypeError as te:
		# print('te = ', te)
		# print('address = ', address)
		return None

	# print('pos list = ', pos_list)
	# print('field_addr_list = ', field_addr_list)
	# for pos in pos_list:
	# 	print(address[pos:])
	small_field_list = []
	for i in range(len(field_addr_list)):
		small_one_field_list = parse_one_field(old_addr, hash_key, address, field_addr_list[i], viet_eng_ref, one_addr_dict, pos_list[i])
		small_field_list += small_one_field_list
		# one_addr_dict[admin_level] = [addr, eng_type, viet_type, [start_pos], [end__pos]]

	isSpecial = parse_fields(small_field_list, old_addr, hash_key, address, viet_eng_ref, one_addr_dict)
	if isSpecial:
		return None
	#Becareful: Tradeoff between size and accuracy
	# if len(one_addr_dict['pid']) == 2:
	# 	return None

	if not field_addr_list:
		return one_addr_dict
	keylist = [x for x in list(one_addr_dict.keys()) if isinstance(x, int)]
	keylist.sort(reverse=True)
	if len(keylist) <= 2 and keylist[0] == p.NAME_ADMIN_LV:
		return None

	# print(keylist)
	try:
		# print('keylist[0] = ', keylist[0])
		one_addr_dict[keylist[0]].append(old_addr)
		# print(one_addr_dict)
	except IndexError:
		return None

	# Becareful
	# try:	
	addr = old_addr
	for j in range(1, len(keylist)):
		prev = one_addr_dict[keylist[j-1]]
		# print('prev = ', prev)
		for i in range(len(prev[3])):
			begin = prev[3][i]
			end = prev[4][i]
			addr = addr[:begin] + 'τ' * (end - begin) + addr[end:] 
			# print('addr = ', addr)
		new_addr = [x for x in re.split('τ+', addr) if x != '']
		try:
			parent_addr = new_addr[0]
		except:
			parent_addr = ''
		if len(new_addr) > 1:
			for a in new_addr[1:]:
				char = ''
				if parent_addr[-1] != ' ' and a[0] != ' ':
					char = ' '
				parent_addr += char + a
		one_addr_dict[keylist[j]].append(remove_redunts(parent_addr))

	# prev = one_addr_dict[keylist[-1]]
	# # print('last prev = ', prev)
	# for i in range(len(prev[3])):
	# 	begin = prev[3][i]
	# 	end = prev[4][i]
	# 	addr = addr[:begin] + 'τ' * (end - begin) + addr[end:] 
	# one_addr_dict['next_raw_addr'] = addr.replace('τ', '')

	# except TypeError as te:
	# 	print('te = ', te)
	# 	# specfical input address logging
	# 	spec_input_dict[hash_key] = old_addr
	# 	# with open(p._LOG_DIR + p.SPEC_INP_LOG_PATH, 'a', encoding='utf-8') as f:
	# 	# 	f.write('{}: {}\n'.format(hash_key, old_addr))
	# 	return None

	try:
		one_addr_dict = clean_addr_dict(one_addr_dict, viet_eng_ref)
	except IndexError:
		# specfical input address logging
		spec_input_dict[hash_key] = old_addr
		return None

	# print('last one_addr_dict = ', one_addr_dict)
	return one_addr_dict

def handle_addr_dict():
	with open(p._PICKLE_DIR + p.CITY_SET_PKL_PATH, 'rb') as f: 
		city_list = list(pickle.load(f))
	with open(p._PICKLE_DIR + p.NON_ACCENT_STD_FIELD_DICT_PKL_PATH, 'rb') as f:
		non_accent_dict = pickle.load(f)
	with open(p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH, 'rb') as f:
		std_add_graph = pickle.load(f)

	regex = re.compile('[@_!#$%^&*()<>?|.}{~:]') 
	addr_dict_list = []

	for i in range (p.FIRST_AREA, p.LAST_AREA+1):
		with open((p._RAW_DATA_DIR_PATH + p.RAW_DATA_JSON_PATH).format(i), 'r', encoding='utf-8') as f:
			res_dict = json.loads(f.read())

		for hash_key, meta_address in res_dict.items():
			# 'Ngách 4/7A, Phương Mai, Q. Đống Đa, Tp. Ha noi' # Ngách abc/xyz => abc = Ngõ, xyz = Ngách
			# 284 Nguyễn Chí Thanh, P. Mường Thanh, Tp. Điện Biên # Wrong addrses, must be: Tp. Điện Biên Phủ
			# A2-P10 quân khu A, Hoàng Diệu, P. Năng Tĩnh, Thành phố Nam Định, T. Nam Định # Quân khu must be a name
			# 2/3 Ngõ Tháp, Đại Mỗ, Nam Từ Liêm, Hà Nội # Tháp = Ngõ, 2 = Ngách, 3 = Số nhà
			# Số 515A Đường Hùng Vương, Quận Hồng Bàng, Ven sông - Sông Cấm/Cảng cũ, Hải Phòng, Việt Nam # Ven sông Sông Cấm/Cảng cũ = name
			# 'Số 123, Hải Châu 2, Phương Mai, Q. Đống Đa, Tp. Hà Nội' # Hai Chau 2 = Duong
			# Đầu Hẻm 186 Trần Phú, Tp. Hội An, Quảng Nam # Đầu = name?
			# 188 A/5 Trần Phú, Phường Minh An, Hội An, Quảng Nam, VN # OK
			# Hẻm 76 Thai Phien 72/4 Thai Phiên, Sơn Phong, Hội An, Quảng Nam, Việt Nam # "76 Thai Phien 72/4" must be hẻm
			# 'Ki ốt 12 CT5 Đơn Nguyên 1 KĐT mới Định Công, Trần Điền, P. Định Công, Q. Hoàng Mai, Tp. Hà Nội' # 'Ki ốt 12 CT5 Đơn Nguyên 1'  = name
			# 33, Ngô Mây, P. Ngô Mây, Thành phố Quy Nhơn, T. Bình Định # OK
			# Quận Cầu Giấy, Hanoi, BTD15 - Đường A2 - Làng Quốc Tế Thăng Long, Vietnam # Useless address
			# Ngã Tư bưu điện huyện Cẩm Khê, Thị trấn Sông Thao, Huyện Sông Thao, Phú Thọ, Việt Nam # 'Huyện Sông Thao' must be 'Huyện Cẩm Khê'
			# Bản Hua Mường, Tt. Sốp Cộp, H. Sốp Cộp, T. Sơn La # Wrong address: 'Tt. Sốp Cộp' must be 'xã Sốp Cộp'
			# Ki ốt 17, Vinh Quang Group, Linh Đàm, P. Hoàng Liệt, Q. Hoàng Mai, Tp. Hà Nội # 'Ki ốt 17 Vinh Quang Group' = name
			# -- Đường/Phố --, Hà Nội, Việt Nam # Useless address
			# số 7, đường Đại Cồ Việt --54 Lương Văn Can, Hanoi, 84, Vietnam # 'Đại Cồ Việt --54 Lương Văn Can' = đường
			# 316 Lê Văn Sỹ, Phường 1, Q.Tân Bình, TP, HCM, Quận Tân Bình, Hồ Chí Minh, VN # Wrong address
			# Tỉnh Lộ 702, Thôn Mỹ Hòa, Xả Vĩnh Hải, Huyện Ninh Hải, Thôn Dư Khánh, Ninh Thuan, Vietnam # Wrong address
			# Lê Thái Tổ, P. Võ Cường, TP, Bắc Ninh, 790000, Vietnam # Wrong address
			# Phường An Bình, Thu Dau Mot, +084, Vietnam # Wrong address: There's no 'An Bình' in 'Thủ Dầu Một'
			# Tầng 3, CT 1A-B – VOV Mễ Trì Plaza, Phường Mễ Trì, Quận Nam Từ Liêm, TP. Hà Nội, 10000, Vietnam # 'Tầng 3 VOV Mễ Trì Plaza' = name
			# Tầng 4, tháp A-B, tòa nhà Golden Palace, đường Mễ Trì, Hanoi, 100000, Vietnam # 'Tầng 4 tháp A-B' = name
			# Lot 75-76 Phan Liem, Ngu Hanh Son District, Da Nang, Vietnam # English address -> not handle
			# Lô 61 – 62 Phan Liêm, Quận Ngũ Hành Sơn, Đà Nẵng, VN # '61 – 62' = block
			# CC5A bán đảo Linh Đàm, Nguyễn Duy Trinh, P. Hoàng Liệt, Q. Hoàng Mai, Tp. Hà Nội # 'bán đảo Linh Đàm' = name
			# No 03 LK 36 Khu Dịch Vụ 16-17-18a-18b Dương Nội, Hà Đông, Hanoi, Vietnam # OK
			# Số 01, Lô D, -KDV cao cấp Bến Đoan CQ-03, Hạ Long, Quảng Ninh, Việt Nam # Wrong address
			# phường Hồng Gai Số 01 Lô D Khu dịch vụ cao cấp Bến Đoan CQ-03, Ha Long, Quang Ninh, Vietnam # Wrong address
			# Căn số 5, khu dịch vụ Chung Cư 15 Tầng, đường Nguyễn Thái Học, p.7, Vung Tau, 760000, Vietnam # Wrong address
			# BN2, LK 7 - LK8 (Liên Khu) Đường N1, P. Thống Nhất, Tp. Biên Hòa, Đồng Nai # Wrong address
			# Liên khu 15 - 4 Ngô Thì Nhậm, Hà Đông, Hà Nội # ok
			# Lô GD3 - 11 + GD3 - 12 KCN Ngọc Hồi, Xã Ngọc Hồi, Huyện Thanh Trì, Hanoi, 10000, Vietnam # ok
			# "Khu N4 cơ khí, Quốc lộ 12, P. Na Lay, Thị xã Mường Lay, T. Điện Biên" # ok
			# "2 lô 4 khu B chung cư Phú Thọ, Lê Đại Hành, P. 15, Q. 11, Tp. Hồ Chí Minh" # ok
			# Ki ot số 3 khu CT4A2 Bắc Linh Đàm, Hanoi, 1000, Vietnam # ok, khu CT4A2 Bắc Linh Đàm = group???
			# Ki ot số 3 , Hanoi, 1000, Vietnam # Useless address
			# "29 Yersin, Phường 9, Thành phố Đà Lạt, Lâm Đồng Chung cư Yersin Lô B, Phòng 607, Vietnam" # 'Yersin Phòng 607' = name
			# 'Ki ốt 12 CT5 Đơn Nguyên 1 KĐT mới Định Công, Trần Điền, P. Định Công, Q. Hoàng Mai, Tp. Hà Nội' # 'CT5 Đơn Nguyên 1' = building_name
			# 'Sao Bọng-Đăng Hà, Xã Đức Liễu, H. Bù Đăng, T. Bình Phước' # 'Sao Bọng-Đăng Hà' = street

			##############unhandled###############
			
			# Quốc lộ 14, Xã Đức Liễu, Huyện Bù Đăng, Tỉnh Bình Phước, Phuoc Tin, 570000, Vietnam # have to fix this
			# 32 LK 6A ĐT Mỗ Lao, Nguyễn Văn Lộc, P. Mộ Lao, Q. Hà Đông, Tp. Hà Nội # 'ĐT Mỗ Lao' = name?
			# Số 27, đường ĐT 741, K03, Phước Bình, thị xã Phước Long, Bình Phước, Việt Nam
			# 15 Khu dịch vụ 3, KĐT Văn Phú, Lê Trọng Tấn, P. Phú La, Q. Hà Đông, Tp. Hà Nội # caustion
			# 66 Khu Dịch Vụ 1 Văn Phú, Quận Hà Đông, Hà Nội
			# Khu dân cư khóm 8, Đường số 1, P. Châu Phú A, Thành phố Châu Đốc, T. An Giang
			# "Phòng 38, lô C TTTM Núi Sam, Quốc lộ 91, P. Núi Sam, Thành phố Châu Đốc, T. An Giang"
			# Ngã 3 QL 1A - Nguyễn Văn Linh, Sơn Tịnh, Quảng Ngãi
			# "Ngã 3 Trần Quang Diệu, Nguyễn Du, Tt. Đức Phổ, H. Đức Phổ, T. Quảng Ngãi"
			# số 73/23 đường Phạm Ngũ Lão, Phường 1, TP. Trà Vinh, 940000, Vietnam
			# 141 Phạm Hồng Thái, Khóm 3 Phường 2, Thành Phố Trà Vinh
			# "địa chỉ: số 1, Phạm Thái Bường, Phường 3, Trà Vinh, 940000, Vietnam" # quite good
			# 195, Nguyen Thi Minh Khai, Khom6, Phuong7, Tp Tra Vinh, Tinh Tra Vinh, Vietnam # Caustion
			# "Hùng Vương, Hòa Thuận, Tp. Trà Vinh"
			# 11, Tránh Quốc Lộ 53, P. 5, Thành phố Trà Vinh, T. Trà Vinh
			# Ngã 4 Trần Thủ Độ - Đường Tránh, Tp. Đồng Hới, Quảng Bình
			# Ngã 3 Phan Kế Bính - Võ Thị Sáu, Tp. Đồng Hới, Quảng Bình
			# Ngã 3 Ngô Gia Tự - Tố Hữu, P. Nam Sách, Tp. Đồng Hới, Quảng Bình
			# Ngã tư bưu điện, Trần Hưng Đạo, P. Đồng Phú, Thành phố Đồng Hới, T. Quảng Bình # Gg map is great
			# Ngã tư Quảng Thọ, P. Quảng Thọ, Thị xã Ba Đồn, T. Quảng Bình # gg map is not good for this case
			# 11, Tránh Quốc Lộ 53, P. 5, Thành phố Trà Vinh, T. Trà Vinh # gg map is not good for this too
			# DK Watch, Co.opmart, Nguyễn Đáng, P. 6, Thành phố Trà Vinh, T. Trà Vinh
			# Điện máy Xanh, 21, Điện Biên Phủ, P. 6, Thành phố Trà Vinh, T. Trà Vinh # gg map UNSUREs about this
			# Phố Ẩm Thực, Trần Phú, P. 7, Thành phố Trà Vinh, T. Trà Vinh
			# Sơn Thông, Khóm, P. 7, Tp. Trà Vinh
			
			# raw_address = remove_redunts(handle_dup_substr(meta_address["address"]))
			raw_address = remove_redunts(handle_dup_substr(\
				"Điện Biên, Tp. Yên Bái"))
			
			address = clean_address(raw_address, hash_key, non_accent_dict)
			# print(address)

			one_addr_dict = parse_address(raw_address, std_add_graph, address, hash_key, p.viet_eng_ref, city_list)

			isValid = True
			if one_addr_dict == None:
				isValid = False
			else:
				for key, meta_data in one_addr_dict.items():
					if key != p.NAME_ADMIN_LV and isinstance(key, int) and regex.search(meta_data[0]) != None:
						isValid = False
						break

			if not isValid:
				# unhandled address logging
				with open(p._LOG_DIR + p.UNHANDLED_LOG_PATH, 'a', encoding='utf-8') as f:
					f.write('{}: {}\n'.format(hash_key, handle_dup_substr(raw_address)))
			else:
				one_addr_dict[p.TITLE_ADMIN_LV] = [meta_address['title'], 'title', 'Tiêu đề', raw_address]
				one_addr_dict['raw_address'] = raw_address
				one_addr_dict['gps'] = meta_address['gps']
				if 'country' not in one_addr_dict:
					one_addr_dict['country'] = ['Việt Nam', 'Việt Nam', \
					-1, -1, 'Việt Nam']
					
				pp.pprint(one_addr_dict)
				# print()
				addr_dict_list.append(one_addr_dict)
			break
		break
	with open(p._LOG_DIR + p.SPEC_INP_LOG_PATH, 'a', encoding='utf-8') as f:
		for hash_key, old_addr in spec_input_dict.items():
			f.write('{}: {}\n'.format(hash_key, old_addr))
	return addr_dict_list

def handle_hcm_addr_dict():
	with open(p._PICKLE_DIR + p.CITY_SET_PKL_PATH, 'rb') as f: 
		city_list = list(pickle.load(f))
	with open(p._PICKLE_DIR + p.NON_ACCENT_STD_FIELD_DICT_PKL_PATH, 'rb') as f:
		non_accent_dict = pickle.load(f)
	# with open(p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH, 'rb') as f:
	# 	std_add_graph = pickle.load(f)
	with open(p._PICKLE_DIR + p.HANDLED_ADDR_GRAPH_PKL_PATH, 'rb') as f:
		hld_add_graph = pickle.load(f)

	# regex = re.compile('[@_!#$%^&*()<>?|.}{~:]') 
	addr_dict_list = []

	wb = xlrd.open_workbook(p._RAW_DATA_DIR_PATH + p.RAW_HCM_DATA_PATH) 
	sheet = wb.sheet_by_index(0) 

	for i in range(1, sheet.nrows): 
		raw_address = remove_redunts(handle_dup_substr(sheet.cell_value(i, 1)))
		hash_key = sheet.cell_value(i, 0)

		address = clean_address(raw_address, hash_key, non_accent_dict)

		one_addr_dict = parse_address(raw_address, hld_add_graph, address, hash_key, p.viet_eng_ref, city_list)

		isValid = True
		if one_addr_dict == None:
			isValid = False
		# else:
		# 	for key, meta_data in one_addr_dict.items():
		# 		if key != p.NAME_ADMIN_LV and isinstance(key, int) and regex.search(meta_data[0]) != None:
		# 			isValid = False
		# 			break

		if not isValid:
			# unhandled address logging
			with open(p._LOG_DIR + p.HCM_UNHANDLED_LOG_PATH, 'a', encoding='utf-8') as f:
				f.write('{}: {}\n'.format(hash_key, handle_dup_substr(raw_address)))
		else:
			one_addr_dict['raw_address'] = raw_address
			
			# pp.pprint(one_addr_dict)
			# print()
			addr_dict_list.append(one_addr_dict)
	with open(p._LOG_DIR + p.HCM_SPEC_INP_LOG_PATH, 'a', encoding='utf-8') as f:
		for hash_key, old_addr in spec_input_dict.items():
			f.write('{}: {}\n'.format(hash_key, old_addr))
	return addr_dict_list

def main():
	import time
	start_time = time.time()
	addr_dict_list = handle_addr_dict()
	print("--- %s seconds ---" % (time.time() - start_time))
	print('total handled addresses = ', len(addr_dict_list))
	# with open(p._PICKLE_DIR + p.HANDLED_ADDR_LIST_PKL_PATH, 'wb') as f:
	# 	pickle.dump(addr_dict_list, f)
	# import random as rd
	# for x in rd.sample(addr_dict_list, 100):
	# 	print(x)
	# 	print()
	###################################################################
	# import time
	# start_time = time.time()
	# hcm_addr_dict_list = handle_hcm_addr_dict()
	# print("--- %s seconds ---" % (time.time() - start_time))
	# print('total handled addresses = ', len(hcm_addr_dict_list))

	# with open(p._PICKLE_DIR + p.HCM_HANDLED_ADDR_LIST_PKL_PATH, 'wb') as f:
	# 	pickle.dump(hcm_addr_dict_list, f)

if __name__ == '__main__':
	main()