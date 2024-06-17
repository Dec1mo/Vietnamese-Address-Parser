# Rule-based-Address-Parser
An Vietnamese address parser that based on rules.

> **Warning**
> This repo is not maintained. Please visit the issues tab for data related questions.

## Table of Contents
+ [Example](#example)
+ [Requirements](#requirements)
+ [Running & How it works](#working)
+ [Acknowledgments](#acknowledgments)

## Example <a name = "example"></a>
An unstructure Vietnamese address can be parsed into structured one.

Input:
```
107 Bạch Đằng, Âu Cơ, Phu Tho, 35000, Vietnam
```
Ouput:
```
"house_number": "107",
"house_number_type": "Số",
"post_code": "35000",
"country": "Việt Nam",
"street": "Bạch Đằng",
"street_type": "Đường",
"ward": "Âu Cơ",
"ward_type": "Phường",
"town": "Phú Thọ",
"town_type": "Thị xã",
"province": "Phú Thọ",
"province_type": "Tỉnh"
```

## Requirements <a name = "requirements"></a>
+ Python 3.7.7
+ [xlrd](https://pypi.org/project/xlrd/)

## Running & How it works <a name = "working"></a>
### Export the standard addresses (from province level to ward level)
```
>> python excel_parser/excel_parser.py
```

### Export the standard address tree (The address tree has country as the root node and each child node of a node has a smaller address level)
In ```addr_graph.py```, uncomment this line and comment the rest:
```python
std_addr_graph = export_std_addr_graph()
```
Then, execute the following command:
```
>> python address_graph/addr_graph.py
```

### Clean the raw address data
```
>> python ultis/clean_data.py
```

### Parse the cleaned address data 
```
>> python json_parser/json_parser.py
```

### Lastly, use standard address tree to standardize the address (export to a Reference Address Table - RAT):
In ```addr_graph.py```, uncomment this lines and comment the rest:
```python
std_addr_graph.export_to_RAT(p._CLEAN_DATA_DIR_PATH + p.RAT_JSON_PATH)
```
Then, execute the following command:
```
>> python address_graph/addr_graph.py
```

After the program finishes, we will get our Reference Address Table.

## Acknowledgments <a name = "acknowledgments"></a>
+ I have developed ner_data_parser module, which can transform data to train the ner model.


