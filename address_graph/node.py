class Node():
	def __init__(self, level=None, id=None, pid=None, address=None, \
		label=None, gps=None, v_type=None, raw_addr=None, post_code=None, \
		other=None, country=None):
		self.level = level
		self.id = id if id != None else self.__hash__(pid, address, label)
		self.pid = pid
		self.address = address
		self.label = label
		self.gps = gps
		self.v_type = v_type
		self.raw_addr = raw_addr
		self.post_code = post_code
		self.other = other
		self.country = country
		# self.std_label = std_label
# {level:0, id:0, pid: None, address:"Viet Nam", label:"Nuoc"}
# {level:1, id:01, pid: 0, address:"Ha Noi", label:"Thanh Pho"}
		
	def __hash__(self, pid, address, label):
		return hash(str(pid) + address + label)

	def print(self):
		print(self.__dict__)