from subprocess import *
import time

Popen('python json_parser.py & python addr_graph.py & python data_parser_for_ner.py', shell=True)
time.sleep(1)
# Popen('python addr_graph.py', shell=True)
# time.sleep(1)
# Popen('python data_parser_for_ner.py', shell=True)