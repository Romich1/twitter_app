""" Client to twitters processing server

Manage queries tasks for users 
Shows data according to processed queries
Available data to browsing - KPIs, twitts 

Requestes processes in server app (tw_server.py)

!Client must saved be in the same dir as the server app!

"""

from json import dumps, loads
from os import listdir, path
from time import time as current_timer, sleep as sleep_timer, strptime 


def initiate(): 
	"""Cheks needed folders and files"""
	
	global QUERIES_DIR, RESULTS_DIR, USERS_FILE_PATH
	global global_mode, global_user
	
	mode = 0 #0 - unauthorized, 1 - user, 2 - admin
	global_user = ''
	result = True 
	
	app_dir = path.abspath(path.dirname(__file__))
	
	QUERIES_DIR = path.normpath(path.join(app_dir,'queries/'))
	RESULTS_DIR = path.normpath(path.join(app_dir,'results/'))
	USERS_FILE_PATH = path.normpath(path.join(app_dir,'users.txt'))
	
	if not path.isdir(QUERIES_DIR):
		print 'No queries dir: %s' %QUERIES_DIR
		result = False
	
	if not path.isdir(RESULTS_DIR):
		print 'No results dir: %s' %RESULTS_DIR
		result = False		
		
	if not path.isfile(USERS_FILE_PATH):
		print 'No users file: %s' %USERS_FILE_PATH
		result = False

	return result
		
def write_request(user,request='',time_seconds=''):
	"""Write users request to file"""
	
	print '\n== WRITING REQUEST ==\n'
	if not request:
		request = raw_input('Enter search frase: ')
	
	if not time_seconds:
		correct = False
		while not correct: 
			time_seconds = raw_input('Enter search time (in seconds): ')
			try: 
				int_time_seconds = int(time_seconds)				
			except: 	
				print('Not correct input. Integer expected.')
				continue
			
			if int_time_seconds < 0 or int_time_seconds > 3600: 
				print('Not correct input. Time must be > 0 and <3600 seconds.')
			else:	
				correct = True		
	
	filename = str(current_timer()).replace('.','')+'_%s_new' %user
	
	query_dict = {'user_name': user, 
				  'query': request, 
				  'time_seconds' : time_seconds}

	with open(path.join(QUERIES_DIR,filename),'w') as query_file:
		query_file.write(dumps(query_dict))

	query_file.close()

	print('Wroute request: '+str(query_dict))


def show_data(filename_full,mode='twitts'):
	"""Print data from twitts file 
	
	Args:
		filename_full: data file name with full path, 
					   file must be created by tw_server.py in JSON format
		mode: string with 2 option - 'twitts' and 'kpi' 
			  to show apropriate section of data
	
	"""
	
	reulsts_file = open(filename_full,'r')
	result_data = loads(reulsts_file.read())
	reulsts_file.close()

	if mode == 'twitts':
		result_data = result_data.get('statuses')
		colums_to_print = ('user','id_str','text')
	elif mode == 'kpi':
		result_data = result_data.get('kpi')

	print '\n -- %s --' % mode.upper()

	for twitt in result_data:
				
		if mode == 'twitts':
			print '\n ID - %s ' %twitt['id']				
				
			for colum in colums_to_print:
							
				if colum == 'user':  
				#user - is section in dict, will print name and id from it
					
					user_name = str(twitt.get(colum).get('name').encode(
																	 'utf-8'))
					user_id = str(twitt.get(colum).get('id_str'))
					print 'user {}  id {}'.format(user_name,user_id)
					continue 
					
				print '{}: {}'.format(colum,str(twitt.get(colum).encode(
																	'utf-8')))
		
		elif mode == 'kpi':
			
			if twitt == 'user':  
			#user - is section in dict, will print all data instead of lists
				
				user_data = result_data.get('user')
				for user_column in user_data:
					
					if type(user_data.get(user_column)) is list: 
						continue  #not shows lists, becouse of big len
					
					print '\n user: {}: {}'.format(user_column,
											str(user_data.get(user_column)))
				
				continue 
					
			print '\n {}: {}'.format(twitt,str(result_data.get(twitt)))
	
	print '\n -- %s end --' % mode.upper()		

	
def show_requests(user):
	"""Display saved requests for 'user'
	and give possibilite to choise one for showing it data
	
	Return:
		True - if choisen exit mode 
		in other option - calls itself 
	
	"""
	
	print '\n== REQUESTS =='
	
	counter = 0
	filesarray = {}
		
	for filename in sorted(listdir(QUERIES_DIR)):
		if user in filename:
			counter += 1 
			filesarray[str(counter)] = filename			
	
	filesarray['e'] = 'Exit to previus menu'

	if filesarray: 
		answer = QuestionFromArray('Choose file',filesarray)
	
	if answer == 'e': 
		return True
	
	if filesarray[answer][-5:] == '_done': 
		print '\nChoosen file: %s  ' %filesarray[answer] 
		
		answers_file = filesarray[answer].replace('_done','_results')		
		fileactions = {'1':'Show KPIs',
					   '2':'Show twitts',
					   'e':'Exit to files list'}
		action = QuestionFromArray('Choose action on file',fileactions)
		
		if action == '1': 
			show_data(path.join(RESULTS_DIR,answers_file),'kpi')
		elif action == '2': 
			show_data(path.join(RESULTS_DIR,answers_file),'twitts')
			
	else:
		print('This file haven`t handled yet')
	
	show_requests(user)

	
def autorization():
	"""Autorizes user
	Users data keeps in text file (not secure)
	!Need to change users list from file to database in future! 	
	
	Return: 
		True - if autorize, False - if not
	
	"""
	
	global global_mode, global_user
	
	username = raw_input('Input username: ')
	password = raw_input('Input password: ')
	
	usersfile = open(USERS_FILE_PATH,'r')	
	users = loads(str(usersfile.readlines()))
	
	for user in users:
		
		user_dict = loads(user.replace("'","\""))

		if username == user_dict.get('user_name'):
			if password == user_dict.get('password'):
				global_user = username
				if user_dict.get('admin_role') == '1':
					global_mode = 'admin'
				else: 
					global_mode = 'user'
					
				return True
		
	return False

	
def QuestionFromArray(message,inputarray):
	"""Prupose to choice one option from inputarray
	Can be ended only by inputing available in inputarray option"""
	
	print('\n'+message) 
	
	if isinstance(inputarray,str): 
		variantslist = list(inputarray)
		
	elif isinstance(inputarray,dict): 			
		
		message = ''
		for key in sorted(inputarray.keys()):
			print(key+' - '+inputarray[key])		
		
		variantslist = list(sorted(inputarray.keys()))	
		
	else:
		variantslist = inputarray

	while True:
		answer = raw_input('Your choise - '+str(variantslist)+'? : ')
				
		if (answer in variantslist):
			return answer
			break
		else:
			print('You need to input one the variant - '+str(variantslist)+
														'. Please try again')	


def choise_action():
	"""Shows main menu and prupose to choise action
	Can be ended only by choising Exit option"""
	
	actions = {'1':'New query',
			   '2':'Browse queries'}
	
	if global_mode == 'admin': 
		actions['3'] = 'Manage users'
		actions['4'] = 'Change password'
	
	actions['e'] = 'Exit'
	print '\n== MAIN MENU =='
	
	answer = QuestionFromArray('Choose action',actions)
	if answer == 'e':
		print('Goodby')
		return 
		
	if answer == '1': 
		write_request(global_user)	
	elif answer == '2': 
		show_requests(global_user)	
	elif answer == '3': 
		print 'Function will be able in next relise'
	elif answer == '4': 
		print 'Function will be able in next relise'
	
	choise_action()

	
### MAIN FLOW ###

if initiate():
	if autorization():
		print '\nWELCOME! %s \nOur mode: %s' %(global_user,global_mode)	
		choise_action()
	else:
		print('Wrong login data. By-by')
else:
	print 'Initiating error \nTry run server app to make initiation'
