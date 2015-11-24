""" Twitters processing server

Takes queries from folder with tasks line
Works in endless loop while running
In each task query: 
	Search twits according to search params during selected time 
	Calculate KPIs 
	Write data 

Requestes task managing and result view available in client app (tw_client.py)

"""

from json import loads, dumps
import oauth2 
from os import remove as osremove, listdir, makedirs, path
from time import time as current_timer, sleep as sleep_timer 


def initiate(): 
	"""Declaring needed paths and globals
	Cheks for needed dirs - 'queries' , 'relusts' in home directory
									and make them if they not exist 
	Cheks for users file and make it if not exist  
	
	"""
	
	global QUERIES_DIR, RESULTS_DIR, KPI_DICT_TEMPLATE
	
	reslut = True
	
	app_dir = path.abspath(path.dirname(__file__))
	QUERIES_DIR = path.normpath(path.join(app_dir,'queries/'))
	RESULTS_DIR = path.normpath(path.join(app_dir,'results/'))
	users_file_path = path.normpath(path.join(app_dir,'users.txt'))
	
	if not path.isdir(QUERIES_DIR):
		makedirs(QUERIES_DIR)
		print 'Made dir for queries: %s' %QUERIES_DIR
	
	if not path.isdir(RESULTS_DIR):
		makedirs(RESULTS_DIR)
		print 'Made dir for results: %s' %RESULTS_DIR
	
	if not path.isfile(users_file_path):
		users_file = open(users_file_path,'w')
		
		users_template = ( 
				"{'user_name': 'admin', 'password': '0', 'admin_role': '1'}\
				\n{'user_name': 'user1', 'password': '1', 'admin_role': '0'}\
				\n{'user_name': 'user2', 'password': '2', 'admin_role': '0'}")
					
		users_file.write(users_template)
		users_file.close()
		print 'Made users file: %s' %users_file_path	
	
	KPI_DICT_TEMPLATE = {
					'twitts_counter':0,
					'queries_counter':0,
					'retweeted':0,
					'languages':[],
					'languages_counter':0,
					'user':
						{'uniqe_users':[],
						'users_counter':0,
						'geo_enabled':0,
						'followers_count':0,
						'time_zones':[],
						'time_zone_counter':0,}
					}
	

def start_working():
	"""Processes queries files in never ended loop with some time delay"""
	
	default_timer = run_time = 60
	
	while True: 
		
		waiting_time = max(default_timer - run_time,1)
		print 'Next run will start in - %s seconds' %waiting_time		
		sleep_timer(waiting_time) 		
		start_time = current_timer()		
		print('Starting reading queries line') 

		for filename in sorted(listdir(QUERIES_DIR)):
			
			if filename[-5:] == '_done': continue
			
			todo_file_path = path.join(QUERIES_DIR,filename) 
			print('Start processing file: %s' %todo_file_path)
			todo_file = open(todo_file_path,'r') 

			line = todo_file.readline()
			
			try:
				dict_line = loads(line.replace("'", "\""))
			except Error as err: 
				print 'Error in JSON loading: %s' %err
				continue						
			
			try:
				start_task(dict_line,filename)
			except Error as err: 
				print 'Error in task doing: %s' % err
				continue			
			
			#mark query file as proccessed by changing suffics  
			done_file_path = path.join(QUERIES_DIR,filename.replace('_new','')  
																	 +'_done')
			done_file = open(done_file_path,'a')
			done_file.write(line) 
			done_file.close()

			todo_file.close()
			osremove(todo_file_path)
		
		run_time = current_timer() - start_time
		print 'Finished of reading queries directory, reading time - %s'\
		%run_time
	

def make_client(): 
	"""Makes connector to twitter through oauth2 and returns it"""
	
	# INSERT YOUR ACCESS DATA HERE!! 
	ACCESS_TOKEN = '4092480916-LKekIbO1izZpfyE4eSIXhd1gB4EXo0nsJnoYJh5'
	ACCESS_SECRET = 'rDLOMkRbye0bwwQqAtWKJwiGxqJSoLYPj4VexvkxDoYJ8' 
	CONSUMER_KEY = 'MLkrjaZz5gqkfdl6Y4Pj2ic6B'
	CONSUMER_SECRET = 'JkjN1isrqiXxdViGb28GdcbMreTD30uuEy38oup0ptUzht4G9U'

	consumer = oauth2.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
	token = oauth2.Token(key=ACCESS_TOKEN, secret=ACCESS_SECRET)
	
	return oauth2.Client(consumer, token)


def query_to_twitter(words,only_twitts=False,count = 15, lang='',geo=''):
	"""Gets data from twitter and decode from JSON
	
	Args:
		words: searched frase 
		only_twitts: if True - execute and return 'statuses' section from data
					 if False - return 'pure' data
		count: number of twitts to reciev
		lang: language filter 
		geo: geo filter
		
	Return:
		decoded data
		
	"""
	
	url = 'https://api.twitter.com/1.1/search/tweets.json?'
	url += 'q={}&count={}'.format(words,str(count))
	if lang: url += '&lang=%s' %lang 
	print url

	client = make_client()
	resp, content = client.request( url, 'GET')
	print('Server answer: {}'.format(resp['status']))
	
	if resp['status'] == '503': #out of queries limits
		print ('out of limits')
		sleep_timer(2)
		return ''
	
	data = loads(content.decode('utf-8'))
	
	if only_twitts: 
		data = data.get('statuses')
	
	return data


def process_kpi(twitt,kpi_dict):
	"""Add some data from twitt to KPIs dict with processing
	
	Args:
		twitt: dict with one twitt data
		kpi_dict: general dict with KPIs, 
				  changed and/or extendet after processing
	
	"""
	
	kpi_dict['retweeted'] += twitt.get('retweeted')
	
	if not twitt['lang'] in kpi_dict['languages']:
		kpi_dict['languages'].append(twitt.get('lang'))

	user_id = twitt.get('user').get('id')	
	
	if not user_id in kpi_dict['user']['uniqe_users']:
		
		kpi_dict['user']['uniqe_users'].append(user_id)		
		geo_enabled = int(twitt.get('user').get('geo_enabled'))
		kpi_dict['user']['geo_enabled'] += geo_enabled 
		followers_count = int(twitt.get('user').get('followers_count'))
		kpi_dict['user']['followers_count'] += followers_count
				
	time_zone = twitt.get('user').get('time_zone')	
	if not time_zone in kpi_dict['user']['time_zones']:
		kpi_dict['user']['time_zones'].append(time_zone)


def process_twitts(twitters_data,exclude_twitts,kpi_dict):
	"""Gets twiits form input data and process each of them
	   Calculates KPIs for each tweet and write agregated KPIs to kpi_dict
	   Uses cash to aviod processing repeated twits in session
	
	Args:
		twitters_data: list or dict with twitts 
		exclude_twitts: list for cashing proceseed twits
		kpi_dict: dict with agregated KPIs 
	
	Returns:
		list of processed twitts with all included data (each twitt is a dict)		
	"""
	
	result_list = []

	for twitt in twitters_data:
			
			if twitt['id'] in exclude_twitts:
				print '%s - skipped' %twitt['id']
				continue 
			else:
				exclude_twitts.append(twitt['id'])
				print '%s - added' %twitt['id']
			
			new_twitt = {}

			for colum in twitt:
				
				if type(twitt.get(colum)) is str:
					new_twitt[colum] = twitt.get(colum).encode('utf-8')
				else:
					new_twitt[colum] = twitt.get(colum)

			result_list.append(new_twitt)
			
			process_kpi(twitt,kpi_dict)

	return result_list

def start_task(params,task_file_name=''):
	"""Read task data from file and run twitts processing
	Write processing result in file 
	
	Args:
		params: dict with parameters 
		task_file_name: task file name, need to create appropriate result file
						 if '' - will create own with '_taskmade_' tag in name 
						 
	"""
	
	global KPI_DICT_TEMPLATE	
	
	print('Staring task for user %s' % params.get('user_name'))
	
	if not task_file_name:
		 task_file_name = str(current_timer()).replace('.','')+'_%s_taskmade_'\
		 %user 

	results_file_name = task_file_name.replace('_new','')+'_results'
	results_file_path = path.join(RESULTS_DIR,results_file_name)
	results_file = open(results_file_path,'a')
	
	results_list = []
	twitts_id_cashe = []	
	counter = 0
	target_end_time = current_timer()+float(params.get('time_seconds'))	

	while current_timer() <= target_end_time:
				
		anserw_count = 10
		if counter == 0: anserw_count = 100
		
		twitts = query_to_twitter(params.get('query'),True,anserw_count)
		if not twitts: continue 
		
		kpi_dict = KPI_DICT_TEMPLATE.copy()
		new_twitts_lst =  process_twitts(twitts,twitts_id_cashe,kpi_dict)
		results_list.extend(new_twitts_lst)
		
		counter += 1 
		sleep_timer(5)

	kpi_dict['twitts_counter'] = len(results_list)
	kpi_dict['queries_counter'] = counter
	kpi_dict['languages_counter'] = len(kpi_dict['languages'])
	kpi_dict['user']['users_counter'] = len(kpi_dict['user']['uniqe_users'])
	kpi_dict['user']['time_zone_counter'] = len(kpi_dict['user']['time_zones'])

	result_dict = {'kpi':kpi_dict,'statuses':results_list}
	results_file.write(dumps(result_dict))
	results_file.close()
	
	print ('End task for user {} , cicles - {}'.format(params.get('user_name')
															    ,str(counter)))

																
### MAIN FLOW ### 

initiate()
start_working()
