import os
import sys
lib_path = os.path.abspath(os.path.join('.'))
sys.path.append(lib_path)
# print(sys.path)

import pickle
import json

from address_graph.node import Node 
import ultis.parameters as p

ROOT = Node(level=0, id=None, address='Việt Nam', label='country')

class SetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return list(obj)
		return json.JSONEncoder.default(self, obj)

class AddressGraph():
	def __init__(self):
		self.root = ROOT
		self.nodes = {self.root.id: self.root}
		self.edges = {}

	def __add_edge(self, pid, cid):
		if pid in self.edges:
			self.edges[pid].add(cid)
		else:
			self.edges[pid] = set([cid])

	def __add_node(self, level=None, id=None, pid=None, address=None, label=None, v_type=None, raw_addr=None, \
		post_code=None, other=None, country=None):
		_id = id if id != None else hash(str(pid) + address + label) % ((sys.maxsize + 1) * 2)
		if _id in self.nodes:
			if raw_addr != None:
				if self.nodes[_id].raw_addr != None:
					self.nodes[_id].raw_addr.add(raw_addr)
				else:
					self.nodes[_id].raw_addr = set([raw_addr])
			return self.nodes[_id]

		true_raw_addr = None
		if raw_addr != None:
			true_raw_addr = set([raw_addr])
		node = Node(level=level, id=_id, pid=pid, address=address, label=label, v_type=v_type, raw_addr=true_raw_addr, \
			post_code=post_code, other=other, country=country)
		self.nodes[_id] = node
		return node

	@staticmethod
	def build_graph(address_list):
		graph = AddressGraph()
		for address in address_list:
			next_pid = None
			addr_list = [(level, entity) for level, entity in address.items()]
			for level, entity in sorted(addr_list, key=lambda x: x[0]):
				# if entity[3] == 'Thành phố':
				# 	print('entity {}'.format(entity))
				# {1:[], 2:[], 3:[]}
				# Becareful with dict index
				node = graph.__add_node(level=level, id=entity[2], v_type=entity[3],\
					pid=next_pid, address=entity[0], label=entity[1])
				graph.__add_edge(next_pid, entity[2]) # self.edges[None] = {'01', '02',...}
				next_pid = entity[2]
		return graph

	def update(self, address_list):
		for address in address_list:
			# print(address)
			next_pid = address['pid']
			if self.nodes[next_pid].raw_addr == None:
				self.nodes[next_pid].raw_addr = set([address['next_raw_addr']])
			else:
				self.nodes[next_pid].raw_addr.add(address['next_raw_addr'])

			post_code = None
			other = None
			country = None
			if 'post_code' in address:	
				post_code = address['post_code'][0]
			if 'other' in address:	
				other = address['other'][0]
			if 'country' in address:	
				country = address['country'][-1]

			cur_node = None
			for level in range(p.viet_eng_ref['KP.'][1], p.TITLE_ADMIN_LV + 1):
				try:
					entity = address[level]
					cur_node = self.__add_node(level=level, pid=next_pid, address=entity[0], label=entity[1], \
						v_type=entity[-2], raw_addr=entity[-1], post_code=post_code, other=other, country=country)
					# cur_node.print()

					self.__add_edge(next_pid, cur_node.id)
					# print(cur_node.id)
					next_pid = cur_node.id
				except KeyError:
					continue
			if cur_node != None:
				self.nodes[cur_node.id].gps = address['gps']
				# self.nodes[cur_node.id].raw_addr = set([address['dirty_raw_address']])
		return self

	def search(self, province=None, province_type=None, county=None, county_type=None, ward=None, ward_type=None):
		def recur(node_id, query, height, max_height, result):
			clean_query = query.lower().replace('.', '').strip()
			if height == max_height:
				addr = self.nodes[node_id].address.lower()
				if max_height == 2: # county:
					if addr == clean_query or \
					('q' + addr) == clean_query or \
					addr.replace('y', 'i') == clean_query or \
					addr.replace('i', 'y') == clean_query or \
					addr.replace('c', 'k') == clean_query or \
					addr.replace('k', 'c') == clean_query:
						if county_type == None or (county_type == self.nodes[node_id].label):
							result.append(self.nodes[node_id])
				elif max_height == 3: # ward:
					if addr == clean_query or \
					('p' + addr) == clean_query or \
					addr.replace('y', 'i') == clean_query or \
					addr.replace('i', 'y') == clean_query or \
					addr.replace('c', 'k') == clean_query or \
					addr.replace('k', 'c') == clean_query:
						if ward_type == None or (ward_type == self.nodes[node_id].label):
							result.append(self.nodes[node_id])
				elif max_height == 1: # province:
					if addr == clean_query or \
					addr.replace('y', 'i') == clean_query or \
					addr.replace('i', 'y') == clean_query or \
					addr.replace('c', 'k') == clean_query or \
					addr.replace('k', 'c') == clean_query:
						if province_type == None or (province_type == self.nodes[node_id].label):
							result.append(self.nodes[node_id])
			else:
				# print('node_id = ', node_id)
				childs = list(self.edges[node_id]) if node_id in self.edges else None
				# print("childs = ", childs)
				if childs != None:
					for child in childs:
						recur(child, query, height + 1, max_height, result)

		def recur_search(province, county, ward):
			# return (result, x1x2x3) with x1x2x3 is a binary string means having (p, c, w) or not.
			province_res = []
			# Province != None
			if province != None:
				recur(None, province, 0, 1, province_res)
				# print ('province_res = ', province_res)
				if not province_res:
					county_res = []
					if county != None:
						recur(None, county, 0, 2, county_res)
					# Ward == None:
					if ward == None:
						if not county_res:
							return None, 0 # 000
						else:
							return county_res, 2 #  010
					# Ward != None:
					elif ward != None:
						ward_res = []
						if not county_res:
							for p in province_res:
								recur(p.id, ward, 0, 3, ward_res)
							# print ('county = None, ward_res = ', ward_res)
							if not ward_res:
								return None, 0 # 000
							else:
								return ward_res, 1 # 001
						else:
							for c in county_res:
								recur(c.id, ward, 2, 3, ward_res)
							# print ('county != None, ward_res = ', ward_res)
							if not ward_res:
								return county_res, 2 #  010
							else:
								return ward_res, 3 # 011
				# County != None	
				elif county != None:
					county_res = []
					for p in province_res:
						recur(p.id, county, 1, 2, county_res)
					# Ward == None:
					if ward == None:
						if not county_res:
							return province_res, 4 # 100
						else:
							return county_res, 6 # 110
					# Ward != None:
					elif ward != None:
						ward_res = []
						if not county_res:
							for p in province_res:
								recur(p.id, ward, 1, 3, ward_res)
							# print ('county = None, ward_res = ', ward_res)
							if not ward_res:
								return province_res, 4 # 100
							else:
								return ward_res, 5 # 101
						else:
							for c in county_res:
								recur(c.id, ward, 2, 3, ward_res)
							# print ('county != None, ward_res = ', ward_res)
							if not ward_res:
								return county_res, 6 # 110
							else:
								return ward_res, 7 # 111
				# County == None	
				else:
					# Ward == None:
					if ward == None:
						return province_res, 4 # 100
					# Ward != None:
					elif ward != None:
						ward_res = []
						for p in province_res:
							recur(p.id, ward, 1, 3, ward_res)
						if not ward_res:
							return province_res, 4 # 100
						else:
							return ward_res, 5 # 101
			# Province == None
			else:
				if county == None and ward == None:
					return None, 0 # 000
				elif county != None and ward == None:
					county_res = []
					recur(None, county, 0, 2, county_res)
					if not county_res:
						return None, 0 # 000
					else:
						return county_res, 2 # 010
				elif county == None and ward != None:
					ward_res = []
					recur(None, ward, 0, 3, ward_res)
					if not ward_res:
						return None, 0 # 000
					else:
						return ward_res, 1 # 001
				else:
					# print('county = ', county)
					# print('ward = ', ward)
					county_res = []
					recur(None, county, 0, 2, county_res)
					# print('county_res = ', county_res)
					if not county_res:
						ward_res = []
						recur(None, county, 0, 3, ward_res)
						if not ward_res:
							return None, 0 # 000
						else:
							return ward_res, 1 # 001
					else:
						ward_res = []
						for c in county_res:
							recur(c.id, ward, 2, 3, ward_res)
						if not ward_res:
							return county_res, 2 # 010
						else:
							return ward_res, 3 # 011

		def normalize_field(field, fields, norm_ref):
			if field == None:
				return
			for number, latin in reversed(norm_ref):
				if number in field:
					fields.append(field.replace(number, latin))
					break
				if latin in field:
					fields.append(field.replace(latin, number))
					break
		
		provinces = [province]
		counties = [county]
		wards = [ward]
		number_latin = [('1', 'I'), ('2', 'II'), ('3', 'III'), ('4', 'IV'), ('5', 'V')]
		normalize_field(province, provinces, number_latin)
		normalize_field(county, counties, number_latin)
		normalize_field(ward, wards, number_latin)
		# print('provinces = ', provinces)
		# print('counties = ', counties)
		# print('wards = ', wards)
		try:
			longest_id_nodes, field_check = recur_search(province, county, ward)
			for p in provinces:
				for c in counties:
					for w in wards:
						# print('p, c, w = ', p, c, w)
						field_res, check = recur_search(p, c, w)
						# print(field_res)
						if field_res == None:
							continue
						if len(field_res[0].id) > len(longest_id_nodes[0].id):
							longest_id_nodes = field_res
							field_check = check
			return longest_id_nodes, field_check
		except TypeError:
			return None
			# print ('provinces = ', provinces)
			# print ('counties = ', counties)
			# print ('wards = ', wards)
	
	def export_to_RAT(self, path):
		# city_node_counts = (0, 0) # HN, HCM
		def recur(node_id, rat):
			# if node_id not in self.edges:
			# 	return
			# else:
			child_ids = list(self.edges[node_id]) if node_id in self.edges else None 
			# print(child_ids)
			if child_ids != None:
				for child_id in child_ids:
					child_node = self.nodes[child_id]
					if child_node.raw_addr != None: # Here filter std address with new address
						isValid = True
						for raw_address in list(child_node.raw_addr):
							print('raw = ', raw_address)
							unwanted_chars = ['/', '\\', '-']
							try:
								for char in unwanted_chars:
									if (' ' + char) in raw_address or \
									(char + ' ') in raw_address or \
									(char + ',') in raw_address:
										isValid = False
									break
							except TypeError:
								print('child_node.raw_addr = ', child_node.raw_addr)
								print('child_node.id = ', child_node.id)
								print('child_node.address = ', child_node.address)
						if isValid:
							true_addr = child_node.address
							print('true = ', true_addr)
							if child_node.address.isdigit():
								true_addr = child_node.v_type + ' ' + child_node.address
							one_node_dict = {"pid":child_node.pid, \
							child_node.label:child_node.address, \
							child_node.label + '_type':child_node.v_type}
							# one_node_dict = {"pid":child_node.pid}
							one_node_dict["raw_address"] = child_node.raw_addr
							if child_node.gps != None:
								one_node_dict["gps"] = child_node.gps
							if child_node.post_code != None:
								one_node_dict["post_code"] = child_node.post_code
							if child_node.other != None:
								one_node_dict["other"] = child_node.other
							if child_node.country != None:
								one_node_dict["country"] = child_node.country

							while child_node.pid != None:
								child_node = self.nodes[child_node.pid]
								# child_node.print()
								true_addr = child_node.address
								if child_node.address.isdigit():
									true_addr = child_node.v_type + ' ' + child_node.address
								one_node_dict[child_node.label] = true_addr.strip()
								one_node_dict[child_node.label + '_type'] = child_node.v_type

							# print(one_node_dict)
							rat[child_id] = one_node_dict
					recur(child_id, rat)

		rat = dict()
		recur(None, rat)
		# print(rat)
		print('len rat = ', len(rat))
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(rat, f, indent=2, cls=SetEncoder, ensure_ascii=False)

		hn_node_count = 0
		hcm_node_count = 0
		for hash_key, meta_addr in rat.items():
			try:
				if meta_addr['municipality'] == 'Hà Nội' and 'gps' in meta_addr:
					hn_node_count += 1
				if meta_addr['municipality'] == 'Hồ Chí Minh' and 'gps' in meta_addr:
					hcm_node_count += 1
			except:
				pass
		print('Số địa chỉ ở HN = {}\nSố địa chỉ ở HCM = {}'.format(hn_node_count, hcm_node_count))

		

	def print_graph(self):
		# print(self.nodes['32244'].level)
		# print(self.edges)
		# print(len(self.nodes))
		# print(len(self.edges))
		pass


def export_std_addr_graph():
	with open(p._PICKLE_DIR + p.ADDR_LIST_PKL_PATH, 'rb') as f:
		address_list = pickle.load(f)

	std_add_graph = AddressGraph.build_graph(address_list)
	with open(p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH, 'wb') as f:
		pickle.dump(std_add_graph, f)
	print ('exported to ', p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH)
	return std_add_graph

if __name__ == '__main__':
	# std_addr_graph = export_std_addr_graph()
	# res_nodes = std_addr_graph.search(province=None, county=None, ward='Lao Chải')

	# print('res_nodes = ', res_nodes)
	# std_addr_graph.nodes[res_nodes[0][0].id].print()
	#############################################

	with open(p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH, 'rb') as f:
		std_addr_graph = pickle.load(f)
	# with open(p._PICKLE_DIR + p.HANDLED_ADDR_LIST_PKL_PATH, 'rb') as f:
	# 	addr_dict_list = pickle.load(f)
	addr_dict_list = [{   4: ['Điện Biên', 'province', '', [0], [9], 'Điện Biên'],
	6: [' Yên Bái', 'provincial_city', ' Tp.', [10, 14], [14, 22]],
	19: [   'Trường Tiểu học Số 2 Mường Lói',
			'title',
			'Tiêu đề',
			'Điện Biên, Tp. Yên Bái'],
	'country': ['Việt Nam', 'Việt Nam', -1, -1, 'Việt Nam'],
	'gps': {'latitude': 20.942306, 'longitude': 103.249284},
	'next_raw_addr': 'Tp. Yên Bái,Điện Biên',
	'pid': '11',
	'raw_address': 'Điện Biên, Tp. Yên Bái'}]
	std_addr_graph.update(addr_dict_list)
	# std_addr_graph.export_to_RAT(p._CLEAN_DATA_DIR_PATH + p.RAT_JSON_PATH)
	std_addr_graph.export_to_RAT(p._CLEAN_DATA_DIR_PATH + 'temp.json')

	# with open(p._PICKLE_DIR + p.std_addr_graph_PKL_PATH, 'wb') as f:
	# 	pickle.dump(std_addr_graph, f)
	#############################################
	# with open(p._PICKLE_DIR + p.STD_ADDR_GRAPH_PKL_PATH, 'rb') as f:
	# 	std_addr_graph = pickle.load(f)
	# with open(p._PICKLE_DIR + p.HCM_HANDLED_ADDR_LIST_PKL_PATH, 'rb') as f:
	# 	hcm_addr_dict_list = pickle.load(f)
	# std_addr_graph.update(hcm_addr_dict_list)
	# std_addr_graph.export_to_RAT(p._CLEAN_DATA_DIR_PATH + p.HCM_RAT_JSON_PATH)

