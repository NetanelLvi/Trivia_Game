##############################################################################
# server.py
"""
- the client_sockets now become internal variable of the main()

- all the function regarding the client socket disconnection now
have the client_sockets list as argument to prevent error of [select fd= -1]

- the handle_logout_message() now deal with the complete process of logging out 
and the dispose_dead_client() just called to make sure of client leaving correctly
any time an empty msg received 

bug!
- when a client disconnect using keyboard interrupt i cant remove him from logged_users{}
	seems to be fixed

"""
##############################################################################
import select
import socket
import chatlib
from enum import *
from typing import *
import random
# from chatlib import PROTOCOL_CLIENT  


# GLOBALS
#***********************************************************************
users = {}
questions = {}
logged_users = {} # a dictionary of clients address to usernames e.g "(1.1.1.1, 5345)": yossi
messages_to_send = []  # Tuples of (socket.getpeername() : str, (full msg ready to be send) : str)

# CONSTANTS #
#***********************************************************************
ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"	#   or "0.0.0.0" for all routed networks


#***********************************************************************
class EmptyMsgReceived(Exception):
	"""exception raised when the remote socket closed so the data received is empty"""
	def __init__(self):
		super().__init__()


#region HELPER SOCKET METHODS
#***********************************************************************
def build_and_send_message(conn : socket.socket,code : str, msg : str) -> None:
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.\n
	Parameters;  conn : socket.socket , code : str, msg : str
	\nReturns; -> None
	"""
	try:
		FullMsg = chatlib.build_message(code , msg.strip())
		FullMsg = FullMsg.encode('utf-8')
		messages_to_send.append((conn,FullMsg))
		# conn.send(FullMsg)
		print(f"[SERVER]", fr"'{FullMsg}'")	  # Debug print

	except (ConnectionResetError, ConnectionAbortedError, OSError):  
		pass 	# Handle unexpected client disconnection
	except Exception as e:  # for debugging only
		print(f"unexpected problem in: 'build_and_send_message'\n {e} ")


def recv_message_and_parse(conn : socket.socket):
	"""
	Receives a new message from given socket,
	then parses the message using chatlib.\n
	Parameters : socket.socket
	Returns: ->	cmd (str) and data (str) of the received message. 
	If error occurred, will return None, None
	"""
	try:
		RawMsg = conn.recv(chatlib.MAX_DATA_LENGTH).decode('utf-8')
		if not RawMsg:
			raise EmptyMsgReceived()
		CleanMsg = RawMsg.strip()
		full_msg = CleanMsg

		cmd, data = chatlib.parse_message(full_msg)
		print(f"[CLIENT] {conn.getpeername()}", fr'msg:"{full_msg}"')	  # Debug print
		return cmd, data
	
	except (ConnectionResetError, EmptyMsgReceived):  # Handle unexpected client disconnection
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)

	except Exception as e:  # for debugging only
		print(f"unexpected problem in: 'recv_message_and_parse'\n the function return (None, None) \n {e} ")
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)



# Data Loaders #
#***********************************************************************
def load_questions():# -> dict[str, dict[str, Any]]:
	"""
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: questions dictionary
	"""
	questions = {
				2313 : {"question":"How much is 2+2","answers":["3","4","2","1"],"correct":2},
				4122 : {"question":"What is the capital of France?","answers":["Lion","Marseille","Paris","Montpellier"],"correct":3} 
				}
	
	return questions


def load_user_database():
	"""
	Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: user dictionary
	"""
	users = {
			"test"		:	{"password":"test","score":0,"questions_asked":[]},
			"yossi"		:	{"password":"123","score":50,"questions_asked":[]},
			"master"	:	{"password":"master","score":200,"questions_asked":[]}
			}
	return users




# region SOCKET CREATOR
#***********************************************************************
def setup_socket() -> socket.socket:
	"""
	Creates new listening socket and returns it
	Receives: -
	Returns: the socket object
	"""
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_address = (SERVER_IP, SERVER_PORT)
	sock.bind(host_address)
	sock.listen()	
	return sock
	
	
def send_error(conn : socket.socket, error_msg : str) -> None:
	"""
	Send error message with given message
	Receives: socket, message error string from called function
	Returns: None
	"""
	# to be checked later
	cmd = chatlib.PROTOCOL_SERVER['login_failed_msg']
	if not error_msg or error_msg == '':
		error_msg =  ERROR_MSG

	build_and_send_message(conn, cmd, error_msg)


# currently unused
def dispose_dead_client(conn : socket.socket, client_sockets : list): # new adding
	global logged_users
	try:
			# conn.getpeername()
		# if conn in client_sockets:
			del logged_users[conn.getpeername()]

			print(f"[LOGGER] A client disconnected unexpectedly and has removed from the lists but not from logged users.")
			conn.close()  # Ensure socket is closed
			client_sockets.remove(conn)
			# global logged_users	
	except :
		pass 	# OSError Handle potential error if the socket is already closed




##### MESSAGE HANDLING
#***********************************************************************

def handle_getscore_message(conn, username : str): #new adding
	global users	 # This is needed to access the same users dictionary from all functions
	global logged_users
	
	data = str(users[username]["score"])
	cmd = chatlib.PROTOCOL_SERVER["my_score_rspn"]	
	build_and_send_message(conn, cmd, data)


def handle_logout_message(conn : socket.socket, client_sockets : list): # new adding
	"""
	Closes the given socket remove socket from client_sockets
	\n(in later chapters, also remove user from logged_users dictionary)
	Receives: socket
	Returns: None
	"""
	global logged_users
	player = logged_users.pop(conn.getpeername()) # in sudden disconnecting won't work
	
	print(f"[LOGGER] '{player}' logged out...")
	client_sockets.remove(conn)
	conn.close()


def handle_login_message(conn : socket.socket, data : str):  #new adding
	"""
	Gets socket and message data of login message. Checks weather user and pass exists and match.
	If not - sends error and finished. If all ok, sends LOGGING OK message and adds user and address to logged_users
	Receives: socket, message code and data
	Returns: None (sends answer to client)
	"""
	global users  # This is needed to access the same users dictionary from all functions
	global logged_users	 # To be used later

	UserName, Password = tuple(chatlib.split_data(data , 2))
	if UserName not in users:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_failed_msg'], msg= 'user not found!')
		return
	
	elif Password == users[UserName]['password']:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_ok_msg'], msg= '')
		logged_users[conn.getpeername()] = UserName

	else:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_failed_msg'], msg= 'incorrect password!')


def handle_logged_message(conn):  #new func
	global users	 # This is needed to access the same users dictionary from all functions
	global logged_users
	logged = str()
	
	cmd = chatlib.PROTOCOL_SERVER["logged_rspn"]
	for key, value in logged_users.items():
		logged += value + ','
	data = logged[:-1]
	build_and_send_message(conn, cmd, data)


def handle_highscore_message(conn):   #new func
	global users	 # This is needed to access the same users dictionary from all functions
	cmd = chatlib.PROTOCOL_SERVER["highscore_rspn"]
	
	# Extract (name, score) tuples from the users dictionary
	list_of_tuples = [(name, data["score"]) for name, data in users.items()]

	# Sort the list by score in descending order
	sorted_list = sorted(list_of_tuples, key=lambda x: x[1], reverse=True)

	data = str()
	for tpl in sorted_list:
		data += f"{tpl[0]}:{tpl[1]}\n"
	print(cmd , data)
	build_and_send_message(conn, cmd, data)


def handle_question_message(conn : socket.socket): # new func
	"""
	uses the func create_random_question()
	for generating the data and send the question 
	to the client according to the protocol
	"""
	global users 
	global logged_users
	cmd = chatlib.PROTOCOL_SERVER["get_question_rspn"]
	data = create_random_question()
	build_and_send_message(conn, cmd, data)


def handle_answer_message(conn:socket.socket, data :str, username:str):  # new func
	"""
	gives a feedback to user answer 
	updating his score accordingly
	updating the questions_asked list
	""" 
	global users 
	global logged_users
	global questions
	
	Qid, UserAns = chatlib.split_data(data, 2)
	UserAns = int(UserAns)
	Qid = int(Qid)

	if questions[Qid]['correct'] == UserAns:
		cmd = chatlib.PROTOCOL_SERVER["correct_answer_rspn"]
		data = ''
		users[username]['score'] += int(5) 
		
	else:
		cmd = chatlib.PROTOCOL_SERVER["wrong_answer_rspn"]
		data = str(questions[Qid]['correct'])

	users[username]['questions_asked'].append(Qid)
	build_and_send_message(conn, cmd, data)



def handle_client_message(conn: socket.socket, cmd: str, data: str, client_sockets : list) -> bool: #new adding

	"""
	Gets message code and data and calls the right function to handle command
	Receives: socket, message code and data
	\nReturns: \nTrue: if socket ok \n False: if no msg to handle or socket is closed
	"""
	#note! 'from chatlib import PROTOCOL_CLIENT'  to get rid of the module name	
	global logged_users	 

	if conn.getpeername() not in logged_users:
		if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:  # Use comparison with dictionary value
			handle_login_message(conn, data)
			return  
	
	elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
		handle_logout_message(conn, client_sockets)
	elif cmd == chatlib.PROTOCOL_CLIENT["logged_list_rqst" ]:
		handle_logged_message(conn)
	elif cmd == chatlib.PROTOCOL_CLIENT["top_score_rqst"]:
		handle_highscore_message(conn)
	elif cmd == chatlib.PROTOCOL_CLIENT["my_score_rqst"]:
		handle_getscore_message(conn, username=logged_users[conn.getpeername()])
	elif cmd == chatlib.PROTOCOL_CLIENT["question_rqst"]:
		handle_question_message(conn)		
	elif cmd == chatlib.PROTOCOL_CLIENT["answer_question_rqst"]:
		handle_answer_message(conn, data, username=logged_users[conn.getpeername()])

	elif not cmd:
		# client probably shutdown or already logged in
		pass 
	else:  # Wildcard pattern for unknown commands
		msg = f"Unknown command: '{cmd}'"
		send_error(conn, error_msg=msg)




# region GAME HELPER FUNCTIONS
#***********************************************************************

#  unused
def print_client_sockets(users_list = logged_users) -> print:
	""" shows the logged users Ip and port using the global logged_users[]"""
	print("client list:")
	for client in users_list:
		print(f"\t{client[0]} | {client[1]}")



def create_random_question() -> str:
	"""
	take a random value from questions and format it to question msg ready to be sent
	"""
	global questions
	global users
	# Get a list of the dictionary's keys
	keys = list(questions.keys())

	# Select a random key from the list of keys
	random_key = random.choice(keys)
	msg = str(random_key) + '#'
	msg += questions[random_key]["question"]
	for answer in questions[random_key]["answers"]:
		msg+= f"#{answer}"

	return msg


#***********************************************************************
def main():
	# Initializes global users and questions dictionaries using load functions
	global users
	global questions
	global logged_users
	global messages_to_send

	users = load_user_database()
	questions = load_questions()
	ServerSocket = setup_socket()
	
	client_sockets = []		# all saved sockets (fd) to select.select
	print("\n\t+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+\n\t|\t Welcome to Trivia Server!  \t|\n\t+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+\n")

	# try:
	while True:
		# Monitor sockets for activity
		ready_to_read, ready_to_write, in_error = select.select([ServerSocket] + client_sockets, client_sockets, []) # client_sockets
	
		# Handle new clients 
		for current_socket in ready_to_read:
			if current_socket is ServerSocket:
				(client_sock, client_address) = ServerSocket.accept()
				print(f"[LOGGER] New client joined! {client_address}")
				client_sockets.append(client_sock)
			else:
				# Handle communication with existing clients
				# try:
					cmd, data = recv_message_and_parse(current_socket)
					handle_client_message(current_socket, cmd, data, client_sockets)
						# dispose_dead_client(current_socket, client_sockets) # , client_sockets
				# except Exception as e:  # Handle unexpected error
					# print("not good at all\n",e)
					# continue  # Move to the next iteration to avoid processing a closed socket
	
		# Send messages to ready clients
		for conn_and_msg in messages_to_send:
			conn, msg = conn_and_msg
			if conn in ready_to_write:
				# build_and_send_message(client, msg)
				conn.send(msg)
				messages_to_send.remove(conn_and_msg)
	
	# except Exception as e:  # Catch any unexpected errors
	# 	print(f"Unexpected Error:\n{e} from:\n {current_socket}")
		
	# except ValueError as e:  # Catch any unexpected errors
	# 	# print(f"Unexpected Error:\n{e} from:\n {current_socket}")
	# 	pass



#***********************************************************************
if __name__ == '__main__':
	main()




#_____________________________________bugs fixed and insights______________________________________________
"""
	use the keyword 'global' to import variable from outside the scope 
	and access modify abilities when they'r at the module level (scope)
"""

"""
'import chatlib'  -> 	
	must contain the module reference ('chatlib.') 
	before each imported object

'from chatlib import PROTOCOL_CLIENT'  -> 
	to get rid of specifying the module name as reference ('chatlib.')
"""


"""
ConnectionResetError -> when the host side (current) is disconnecting 
							or shutting down unexpectedly
ConnectionAbortedError -> when the remote side (server\client doesn't matter)
							is shutting down or disconnecting unexpectedly

This both exception class handle the error called:
[WinError 10053] 
'An established connection was aborted by the software in your host machine.'

this practice down below prevent the software from crushing in that case 
we use this any time the client is interacting with the server socket
such as sending messages or running the game menu.

except (ConnectionAbortedError, ConnectionResetError):
	print("Server has a problem. connection lost. Exiting...")
	exit()
"""


"""
except (ConnectionResetError):    
	prevent the server from crushes when client is shutting down unexpectedly 
	without logging out correctly.
	note: if you try to parse his last msg 'None' you will probably meet an error
"""

"""
when the client socket shutdown unexpectedly it sends an empty msg ''
(since we used .decode('utf-8'))
so make sure to handle it immediately at your recv method
as i did in the 'class EmptyMsgReceived(exception)'
"""

"""
for python 3.10 and above!

match cmd:
		case value if value == chatlib.PROTOCOL_CLIENT["login_msg"]:  # Use comparison with dictionary value
			handle_login_message(conn, data)
			.
			.
			.
		case _:  # Wildcard pattern for unknown commands
			print(f"Unknown command: {cmd} from {conn}")
			send_error(conn, cmd)
"""

"""
	because of the need to convert the fields to str() 
	so the method str.join() will work therefor this occurred
	questions keys works with str only instead of int
		4112 -> error '4112' -> work

	the user answer input course:
	[client]
	user input (str) -> validate_numeric_input (int) -> 
	handle_answer_input() (int) -> chatlib.join_data() (str) -> send_answer() (str) 
	-> join_data() (str) -> play_question()
	[server]
	handle_answer_message() (str) -> int() fetching dict question key 
	
	due to inconsistency of value type, changes have made.
	1) the chatlib.join_data() now convert the fields_list to str
	2) the user answer is of type(str) until the handle_answer_message() func convert it to an (int)
	to match the dict keys
"""