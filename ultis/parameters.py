import re
import os

WORKING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')

viet_eng_ref = {												#Admin_level
				# 'Nước':'country',									#	0

				# # 'Tỉnh': 'province',								#	4 
				# # 'T.': 'province',								#	4 
				# # 'Thành phố': 'municipality',					#	4
				
				# 'Thành phố': 'provincial_city',					#	6
				# 'Tp.': 'provincial_city',	

				# 'Huyện': 'county',								#	6
				# 'H.': 'county',									#	6
				# 'Quận': 'district',								#	6
				# 'Q.': 'district',									#	6
				# 'Thị xã': 'town',									#	6
				# 'Tx.': 'town',									#	6

				# 'Phường': 'ward',									#	8
				# 'P.': 'ward',										#	8
				# 'Xã': 'commune',									#	8
				# 'X.': 'commune',									#	8
				# 'Thị trấn': 'township',							#	8
				# 'Tt.': 'township',								#	8
				
				'Khu phố': ['neighboorhood', 9],					
				'KP.': ['neighboorhood', 9],						
				'KP ': ['neighboorhood', 9],	
				'Khu vực': ['big_hamlet', 9],
				'KV.': ['big_hamlet', 9],					
				'KV ': ['big_hamlet', 9],					
				'Làng': ['village',	9],																	
				'Thôn ': ['village',	9],								
				'Bản ': ['village', 9],		
				'Khóm': ['village', 9],
				'K.': ['village', 9], # Khóm
				'Liên ấp': ['big_hamlet', 9], # Becareful							
				'Ấp': ['big_hamlet', 9],
				# Sóc, Buôn				

				'Xóm': ['hamlet', 10],								
				# 'Đội': ['hamlet', 10],								
				'Tổ dân phố': ['big_group',	10],
				'TDP.': ['big_group', 10],								
				'TDP': ['big_group', 10],								

				'Quốc lộ': ['route', 11],							
				'QL.': ['route', 11],								
				'QL ': ['route', 11],								
				'Đường tỉnh': ['street', 11],												
				'Đường huyện': ['street', 11],												
				'Đường': ['street',	11],							
				'Đ.': ['street', 11],								
				'Đại lộ': ['street', 11],							
				'Hương lộ': ['street', 11],							
				'Xa lộ': ['street', 11],							
				'Tỉnh lộ': ['street', 11],							
				# 'Lộ ': ['street', 11],							
				'Phố': ['street', 11],		
				
				'Cụm dân cư': ['group', 12], # Becareful
				'Cư xá': ['group', 12],	
				'Khối': ['group', 12],							
				'Tiểu khu': ['group', 12],							
				'Tổ.': ['group', 12],							
				'Tổ ': ['group', 12],							
				'Khu nhà ở': ['group',	12],						
				'Khu dân cư': ['group',	12],						
				'KDC.': ['group', 12],								
				'KDC': ['group', 12],								
				'Khu tập thể': ['group', 12],					
				'Khu TT.': ['group', 12],					
				'Khu TT': ['group',	12],					
				'KTT.': ['group', 12],						
				'KTT': ['group', 12],	
				'Tập thể': ['group', 12],						
				'TT.': ['group', 12],						
				'TT ': ['group', 12],						
				'Khu công nghệ cao': ['group', 12],						
				'Khu CNC': ['group', 12],						
				'Khu đô thị mới': ['group', 12],	
				'KĐT mới': ['group', 12],	
				'Khu ĐTM': ['group', 12],						
				'KĐTM.': ['group', 12],						
				'KĐTM': ['group', 12],						
				'Khu đô thị': ['group', 12],						
				'Khu ĐT': ['group', 12],						
				'KĐT.': ['group', 12],
				'KĐT': ['group', 12],
				'Khu công nghiệp': ['group', 12],	
				'Khu CN ': ['group', 12],						
				'KCN.': ['group', 12],								
				'KCN': ['group', 12],								
				'Khu tái định cư': ['group', 12],								
				'Khu TĐC': ['group', 12],								
				'KTĐC': ['group', 12],								
				'Cụm công nghiệp': ['group', 12],					
				'CCN.': ['group', 12],								
				'CCN': ['group', 12],								
				'Khu liền kề': ['group', 12],							
				'Khu LK': ['group', 12],			
				# More with 'Khu'-prefix remaing as: Khu ẩm thực, Khu du lịch
				'Khu dịch vụ': ['group', 12],
				'Kdv': ['group', 12],
				'Khu ẩm thực': ['group', 12],
				'Khu biệt thự': ['group', 12],
				'Liên khu': ['group', 12],
				# Can 'chung cu' be here??
				'Chung cư': ['group', 12],	
				'CC.': ['group', 12],	
				'CC': ['group', 12],	
				# 'Khu' can be here


				# 'ô ': ['block',	13.5],		
				# 'Quân Khu': ['block',	13],							
				'Lô ': ['block', 13],							
				'Liền kề': ['block', 13],							
				'LK.': ['block', 13],							
				'LK ': ['block', 13],							
				'Ngõ': ['lane',	13],
				'Ngã sáu': ['junction', 13],		
				'Ngã 6': ['junction', 13],	
				'Ngã năm': ['junction', 13],		
				'Ngã 5': ['junction', 13],								
				'Ngã tư': ['junction', 13],		
				'Ngã 4': ['junction', 13],		
				'Ngã ba': ['junction', 13],		
				'Ngã 3': ['junction', 13],		
				'Km.' : ['km',	13],
				'Km ' : ['km', 13],


				'Ngách': ['alley', 14],							

				'Hẻm': ['small_alley', 15],		

				# Or 'Khu' can be here
				
				'Khu ': ['unknown', -1],
				'Tòa nhà': ['building_name', 16],					
				'Tòa ': ['building_name', 16],	

				'Biệt thự': ['house_number', 17],					
				# 'Ki ốt': ['house_number', 17],					
				# 'Kiôt': ['house_number', 17],					
				# 'Kiot': ['house_number', 17],					
				'Số nhà': ['house_number', 17],					
				'SN': ['house_number', 17],						
				'No.': ['house_number', 17],						
				'No ': ['house_number', 17],						
				'Số ': ['house_number', 17],		

				# 'Tên': 'name'								#	18
				# 'Title': 'title'							#	19
}

std_dict = {
	'tỉnh': 'Tỉnh',		
	't.': 'Tỉnh',
	't': 'Tỉnh',
	'thành phố': 'Thành phố',
	'tp.': 'Thành phố',	
	't.p': 'Thành phố',	
	't.p.': 'Thành phố',	
	'tp': 'Thành phố',	
	'huyện': 'Huyện',							
	'h.': 'Huyện',								
	'quận': 'Quận',						
	'q.': 'Quận',						
	'q': 'Quận',						
	'thị xã': 'Thị xã',								
	'tx.': 'Thị xã',								
	't.x': 'Thị xã',								
	'tx': 'Thị xã',								
	'phường': 'Phường',								
	'p.': 'Phường',								
	'p': 'Phường',								
	'xã': 'Xã',								
	'x.': 'Xã',								
	'x': 'Xã',								
	'thị trấn': 'Thị trấn',						
	# 'tt.': 'Thị trấn', 
	'khu phố':'Khu phố',
	'kp.':'Khu phố',
	'kp':'Khu phố',
	'khu vực':'Khu vực',
	'kv.':'Khu vực',
	'kv':'Khu vực',
	'làng':'Làng',
	'thôn':'Thôn',
	'bản':'Bản',
	'khóm':'Khóm',
	'k.':'Khóm',
	'liên ấp':'Liên ấp',
	'ấp':'Ấp',
	'xóm':'Xóm',
	# 'đội':'Đội',
	'tổ dân phố':'Tổ dân phố',
	'tdp.':'Tổ dân phố',
	'tdp':'Tổ dân phố',
	'quốc lộ':'Quốc lộ',
	'ql.':'Quốc lộ',
	'ql':'Quốc lộ',
	'đường tỉnh':'Đường tỉnh',
	'đường huyện':'Đường huyện',
	# 'đường số ':'Đường số ',
	'đường':'Đường',
	'đ.':'Đường',
	'tỉnh lộ':'Tỉnh lộ',
	'đại lộ':'Đại lộ',
	'hương lộ': 'Hương lộ',							
	'xa lộ': 'Xa lộ',							
	'tỉnh lộ': 'Tỉnh lộ',							
	# 'lộ': 'Lộ',	
	'phố':'Phố',
	'cư xá':'Cư xá',
	'cụm dân cư':'Cụm dân cư',
	'khối':'Khối',
	'tiểu khu':'Tiểu khu',
	'tổ':'Tổ',
	'tổ.':'Tổ',
	'khu dân cư':'Khu dân cư',
	'kdc.':'Khu dân cư',
	'kdc':'Khu dân cư',
	'khu nhà ở':'Khu nhà ở',
	'khu tập thể':'Khu tập thể',
	'khu tt.':'Khu tập thể',
	'khu tt':'Khu tập thể',
	'ktt.':'Khu tập thể',
	'ktt':'Khu tập thể',
	'tập thể':'Khu tập thể',
	'tt.':'Khu tập thể',
	'tt':'Khu tập thể',
	't.t.':'Khu tập thể',
	't.t':'Khu tập thể',
	'khu công nghệ cao':'Khu công nghệ cao',
	'khu cnc':'Khu công nghệ cao',
	'khu đô thị mới':'Khu đô thị mới',
	'kđt mới':'Khu đô thị mới',
	'khu đtm':'Khu đô thị mới',
	'kđtm.':'Khu đô thị mới',
	'kđtm':'Khu đô thị mới',
	'khu đô thị':'Khu đô thị',
	'khu đt':'Khu đô thị',
	'kđt.':'Khu đô thị',
	'kđt':'Khu đô thị',
	'khu công nghiệp':'Khu công nghiệp',
	'khu cn':'Khu công nghiệp',
	'kcn.':'Khu công nghiệp',
	'kcn':'Khu công nghiệp',
	'khu tái định cư':'Khu tái định cư',
	'khu tđc':'Khu tái định cư',
	'ktđc':'Khu tái định cư',
	'cụm công nghiệp':'Cụm công nghiệp',
	'ccn.':'Cụm công nghiệp',
	'ccn':'Cụm công nghiệp',
	'khu liền kề':'Khu liền kề',
	'khu lk':'Khu liền kề',
	'liên khu':'Liên khu',
	'khu dịch vụ':'Khu dịch vụ',
	'kdv':'Khu dịch vụ',
	'khu ẩm thực':'Khu ẩm thực',
	'khu biệt thự':'Khu biệt thự',
	'lô':'Lô',
	'liền kề':'Liền kề',
	'lk.':'Liền kề',
	'lk':'Liền kề',
	'ngõ':'Ngõ',
	'ngã sáu': 'Ngã sáu',		
	'ngã 6': 'Ngã sáu',	
	'ngã năm': 'Ngã năm',		
	'ngã 5': 'Ngã năm',								
	'ngã tư': 'Ngã tư',		
	'ngã 4': 'Ngã tư',		
	'ngã ba': 'Ngã ba',		
	'ngã 3': 'Ngã ba',
	'km.':'KM',
	'km':'KM',
	'ngách':'Ngách',
	'hẻm':'Hẻm',
	'khu':'Khu',
	'tòa nhà':'Tòa nhà',
	'tòa':'Tòa nhà',
	'chung cư':'Chung cư',
	'cc.':'Chung cư',
	'cc':'Chung cư',
	'biệt thự':'Biệt thự',
	'ki ốt':'Ki ốt',
	'kiôt':'Ki ốt',
	'kiot':'Ki ốt',
	'số nhà':'Số nhà',
	'sn':'Số nhà',
	'no.':'Số nhà',
	'no':'Số nhà',
	'số':'Số nhà',
}

acronym_dict = {
	'country':'CTR',
	'province':'PRV',
	'municipality':'MNP',
	'provincial_city':'PCT',
	'county':'CTY',
	'district':'DTR',
	'town':'TWN',
	'ward':'WRD',
	'commune':'CMN',
	'township':'TWS',
	'neighboorhood':'NEG',
	'big_hamlet':'BHL',
	'village':'VIL',
	'hamlet':'HAL',
	'big_group':'BGR',
	'route':'RTE',
	'street':'STR',
	'group':'GRP',
	'building_name':'BLD',
	'block':'BLK',
	'lane':'LNE',
	'junction':'JNC',
	'km':'KIM',
	'alley':'ALY',
	'small_alley':'SAL',
	'house_number':'HNB',
	'name':'NAM',
	'title':'TTL',
}

province_prefix_list = \
	[('thành phố', 'municipality'), \
	('tp.', 'municipality'), \
	('tp', 'municipality'), \
	('t.p.', 'municipality'), \
	('t.p', 'municipality'), \
	('tỉnh', 'province'), \
	('t.', 'province'), \
	(' t ', 'province')]

county_prefix_list = \
	[('thành phố', 'provincial_city'), \
	('tp.', 'provincial_city'), \
	('tp', 'provincial_city'), \
	('t.p.', 'provincial_city'), \
	('t.p', 'provincial_city'), \
	('huyện', 'county'), \
	('h.', 'county'), \
	('quận', 'district'), \
	('q.', 'district'), \
	(' q ', 'district'), \
	('thị xã', 'town'), \
	('tx.', 'town'), \
	('tx', 'town'), \
	('t.x.', 'town'), \
	('t.x', 'town')]

ward_prefix_list = \
	[('phường', 'ward'), \
	('p.', 'ward'), \
	(' p ', 'ward'), \
	('thị trấn', 'township'), \
	('tt.', 'township'), \
	('tt', 'township'), \
	('t.t.', 'township'), \
	('t.t', 'township'), \
	('xã', 'commune'), \
	('x.', 'commune'), \
	(' x ', 'commune')]

mess_wards = ['tả van', 'lao chải']
ignored_number_prefixes = [
							'kiốt', 'ki ốt', 'kiôt', 'ki ôt', 'kiot', 'ki ot', \
							'chợ', 'vov', 'tầng', 'phòng', 'ố ', 'ổ ', 'shop'
							]
must_be_name_strings = ['tỉnh đội', 'ẩm thực', 'quân khu', ]
repl_ignorecase_municipalities = [('HN', 'Hà Nội'), ('Hanoi', 'Hà Nội'), ('Ha noi', 'Hà Nội'), \
									('HCM', 'Hồ Chí Minh'), ('Ho Chi Minh', 'Hồ Chí Minh')]

BUILDING_PATTERN = re.compile(r'^[A-Za-z]{1,2}[0-9]{0,2}\-{0,1}[0-9]{0,2}[A-Za-z]{0,2}[0-9]{0,2}$')
BUILDING_PREFIXES = {'ct', 'hh', 'bt', 'ps', 'ls', 'cd'} #, 'n'}
COUNTRY_ADMIN_LV = None
OTHER_ADMIN_LV = 2
POST_CODE_ADMIN_LV = 3
PROVINCE_ADMIN_LV = 4
COUNTY_ADMIN_LV = 6
WARD_ADMIN_LV = 8
GROUP_ADMIN_LV = 12
BUILDING_NAME_ADMIN_LV = 16
NAME_ADMIN_LV = 18
TITLE_ADMIN_LV = 19

_CLEAN_DATA_DIR_PATH = os.path.join(WORKING_DIR, '_clean_data/')
_RAW_DATA_DIR_PATH = os.path.join(WORKING_DIR, './_raw_data/')
RAW_DATA_JSON_PATH = 'coccoc_data_area_{}.json'
RAW_HCM_DATA_PATH = 'data_hcm.xlsx'
FIRST_AREA = 1
LAST_AREA = 5

_PICKLE_DIR = os.path.join(WORKING_DIR, '_pkl/')
_LOG_DIR = os.path.join(WORKING_DIR, '_log/')

CLEAN_DATA_FILE_PATH = 'clean_addreses.json'
NOT_CLEAN_LOG_PATH = 'not_clean_data.log'
SPEC_INP_LOG_PATH = 'spec_input.log'
HCM_SPEC_INP_LOG_PATH = 'hcm_spec_input.log'

CITY_SET_PKL_PATH = 'city_set.pkl'
NON_ACCENT_STD_FIELD_DICT_PKL_PATH = 'non_accent_std_field_dict.pkl'
ADDR_LIST_PKL_PATH = 'address_list.pkl'
HANDLED_ADDR_LIST_PKL_PATH = 'handled_addr_list.pkl'
HCM_HANDLED_ADDR_LIST_PKL_PATH = 'hcm_handled_addr_list.pkl'

STD_ADDR_EXCEL_PATH = 'standard_address.xls'

STD_ADDR_GRAPH_PKL_PATH = 'std_add_graph.pkl'
HANDLED_ADDR_GRAPH_PKL_PATH = 'handled_addr_graph.pkl'

UNHANDLED_LOG_PATH = 'unhandled_data.log'
HCM_UNHANDLED_LOG_PATH = 'hcm_unhandled_data.log'
RAT_JSON_PATH = 'rat.json'
HCM_RAT_JSON_PATH = 'hcm_rat.json'

NER_ADDR_LIST_FILE_PATH = 'ner_address_list.json'
HCM_NER_ADDR_LIST_FILE_PATH = 'hcm_ner_address_list.json'


