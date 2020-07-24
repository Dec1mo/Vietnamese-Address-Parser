import os
import sys
lib_path = os.path.abspath(os.path.join('.'))
sys.path.append(lib_path)

import xlrd 
import pickle
import unicodedata

import ultis.parameters as p

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

def non_accent_convert(utf8_str):
	import re
	INTAB = "ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđẠẢÃÀÁÂẬẦẤẨẪĂẮẰẶẲẴÓÒỌÕỎÔỘỔỖỒỐƠỜỚỢỞỠÉÈẺẸẼÊẾỀỆỂỄÚÙỤỦŨƯỰỮỬỪỨÍÌỊỈĨÝỲỶỴỸĐ"
	INTAB = [ch for ch in INTAB]
	OUTTAB = "a" * 17 + "o" * 17 + "e" * 11 + "u" * 11 + "i" * 5 + "y" * 5 + "d" + \
			 "A" * 17 + "O" * 17 + "E" * 11 + "U" * 11 + "I" * 5 + "Y" * 5 + "D"
	r = re.compile("|".join(INTAB))
	replaces_dict = dict(zip(INTAB, OUTTAB))

	return r.sub(lambda m: replaces_dict[m.group(0)], utf8_str)

def main():
	viet_eng_ref = {
					# 'Nước':'country',

					'Tỉnh': 'province',					            #	4
					'Thành phố (thuộc TW)': 'municipality',		    #	4
					
					'Thành phố': 'provincial_city',					#	6
					'Huyện': 'county',					            #	6
					'Quận': 'district',					        	#	6
					'Thị xã': 'town',								#	6

					'Phường': 'ward',								#	8
					'Xã': 'commune',								#	8
					'Thị trấn': 'township',							#	8
					}
	# [{1:("hanoi","city",id), 2:("Hai Ba Trung","county",id), 3:("Bach Mai", "precinct", id)},...]

	wb = xlrd.open_workbook(p._CLEAN_DATA_DIR_PATH + p.STD_ADDR_EXCEL_PATH) 
	sheet = wb.sheet_by_index(0) 
	
	MIN_THRESHOLD = 5
	city_set = set()
	non_accent_dict = {}
	address_list = []
	for i in range(1, sheet.nrows): 
		one_address = {}
		for viet_add, eng_add in viet_eng_ref.items():
			# if viet_add.lower() in sheet.cell_value(i, 7).lower():
			# 	city = norm(sheet.cell_value(i, 7).replace(viet_add+' ',''))
			idx = sheet.cell_value(i, 7).lower().find(viet_add.lower())
			if idx != -1:
				city = norm(sheet.cell_value(i, 7)[idx + len(viet_add):]).strip()
				city_set.add(city)
				if len(non_accent_convert(city)) > MIN_THRESHOLD and len(city.split()) > 1:
					if non_accent_convert(city) in non_accent_dict and city != non_accent_dict[non_accent_convert(city)]:
						non_accent_dict[non_accent_convert(city)] = -1
					else:
						non_accent_dict[non_accent_convert(city)] = city
				if viet_add.lower() != 'thành phố':
					one_address[4] = [city, eng_add, sheet.cell_value(i, 6), viet_add]
				else:
					one_address[4] = [city, 'municipality', str(sheet.cell_value(i, 6)), viet_add]
				break
			
		for viet_add, eng_add in viet_eng_ref.items():
			idx = sheet.cell_value(i, 5).lower().find(viet_add.lower())
			if idx != -1:
				name = norm(sheet.cell_value(i, 5)[idx + len(viet_add):]).strip()
				try:
					name_number = int(name)
					one_address[6] = [str(name_number),\
							eng_add, str(sheet.cell_value(i, 4)), viet_add]
				except:
					one_address[6] = [name, eng_add, str(sheet.cell_value(i, 4)), viet_add]
					if len(non_accent_convert(name)) > MIN_THRESHOLD and len(name.split()) > 1:
						if non_accent_convert(name) in non_accent_dict and name != non_accent_dict[non_accent_convert(name)]:
							non_accent_dict[non_accent_convert(name)] = -1
						else:
							non_accent_dict[non_accent_convert(name)] = name
					
				break
				

		idx = sheet.cell_value(i, 1).lower().find(sheet.cell_value(i, 3).lower())
		name = norm(sheet.cell_value(i, 1)[idx + len(sheet.cell_value(i, 3)):]).strip()
		try:
			name_number = int(name)
			one_address[8] = [str(name_number),\
					viet_eng_ref[sheet.cell_value(i, 3)], str(sheet.cell_value(i, 0)), sheet.cell_value(i, 3)]
			address_list.append(one_address)
		except:

			one_address[8] = [name, viet_eng_ref[sheet.cell_value(i, 3)], str(sheet.cell_value(i, 0)), sheet.cell_value(i, 3)]
			if name == 'Đức Chánh':
				print(one_address)
			if len(non_accent_convert(name)) > MIN_THRESHOLD and len(name.split()) > 1:
				if non_accent_convert(name) in non_accent_dict and name != non_accent_dict[non_accent_convert(name)]:
					non_accent_dict[non_accent_convert(name)] = -1
				else:
					non_accent_dict[non_accent_convert(name)] = name

			address_list.append(one_address)


	with open(p._PICKLE_DIR + p.ADDR_LIST_PKL_PATH, 'wb') as f:
		pickle.dump(address_list, f)

	with open(p._PICKLE_DIR + p.CITY_SET_PKL_PATH, 'wb') as f:
		pickle.dump(city_set, f)

	print(len(non_accent_dict))

	non_accent_dict = {k:v for k,v in non_accent_dict.items() if v != -1}

	print(len(non_accent_dict))

	# for key, value in non_accent_dict.items():
	# 	print('key = {}, value = {}'.format(key, value))

	with open(p._PICKLE_DIR + p.NON_ACCENT_STD_FIELD_DICT_PKL_PATH, 'wb') as f:
		pickle.dump(non_accent_dict, f)

	# print(non_accent_dict['Binh Thanh'])

if __name__ == '__main__':
	main()

