##############################################################################
# server.py
"""
- the client_sockets now become internal variable of the main()

- all the function regardig the client socket disconection now
have the client_sockets list as argument to prevent error of [select fd= -1]

- the handle_logout_message() now deal with the complete process of logging out 
and the dispose_dead_client() just called to make sure of client leaving correctly
any time an empty msg recived 
"""
##############################################################################
import select
import socket
import chatlib
from enum import *
from typing import *
# from chatlib import PROTOCOL_CLIENT  


# GLOBALS
#***********************************************************************
users = {}
questions = {}
logged_users = {} # a dictionary of client hostnames to usernames - will be used later
# client_sockets = []
# CONSTANT #
#***********************************************************************
ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"	#   or "0.0.0.0" for all routed networks


#***********************************************************************
class EmptyMsgRecieved(Exception):
	"""exception raised when the remote socket closed so the data recived is empty"""
	def __init__(self):
		super().__init__()


#region HELPER SOCKET METHODS
#***********************************************************************
def build_and_send_message(conn : socket.socket,code : str, msg : str) -> None:
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.\n
	Paramaters;  conn : socket.socket , code : str, msg : str
	\nReturns; -> None
	"""
	try:
		FullMsg = chatlib.build_message(code , msg.strip())
		conn.send(FullMsg.encode('utf-8'))
		print("[SERVER] ",FullMsg)	  # Debug print

	except (ConnectionResetError, ConnectionAbortedError, OSError):  
		pass 	# Handle unexpected client disconnection
	except Exception as e:  # for debugging only
		print(f"unexpected problem in: 'build_and_send_message'\n {e} ")


def recv_message_and_parse(conn : socket.socket):
	"""
	Recieves a new message from given socket,
	then parses the message using chatlib.\n
	Paramaters : socket.socket
	Returns: ->	cmd (str) and data (str) of the received message. 
	If error occured, will return None, None
	"""
	try:
		RawMsg = conn.recv(chatlib.MAX_DATA_LENGTH).decode('utf-8')
		if not RawMsg:
			raise EmptyMsgRecieved()
		CleanMsg = RawMsg.strip()
		full_msg = CleanMsg

		cmd, data = chatlib.parse_message(full_msg)
		print(f"[CLIENT] '{full_msg}'.")	  # Debug print
		return cmd, data
	
	except (ConnectionResetError, EmptyMsgRecieved):  # Handle unexpected client disconnection
		# dispose_dead_client(conn)
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)

	except Exception as e:  # for debugging only
		print(f"unexpected problem in: 'recv_message_and_parse'\n the function return (None, None) \n {e} ")
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)
	
	


# Data Loaders #
#***********************************************************************
def load_questions():
	"""
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Recieves: -
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
	Recieves: -
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
	Recieves: -
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
	Recieves: socket, message error string from called function
	Returns: None
	"""
	# to be checked later
	cmd = chatlib.PROTOCOL_SERVER['login_failed_msg']
	if not error_msg or error_msg == '':
		error_msg =  ERROR_MSG

	build_and_send_message(conn, cmd, error_msg)


def dispose_dead_client(conn : socket.socket, client_sockets : list): 
	try:
		conn.getpeername()
		if conn in client_sockets:
			print(f"[LOGGER] A client disconnected unexpectedly and has removed from the lists.")
			conn.close()  # Ensure socket is closed
			client_sockets.remove(conn)
			# global logged_users	
	except :
		pass 	# OSError Handle potential error if the socket is already closed

#endregion


	
##### MESSAGE HANDLING
#***********************************************************************

def handle_getscore_message(conn, username):
	global users	 # This is needed to access the same users dictionary from all functions

	# Implement this in later chapters

	
def handle_logout_message(conn : socket.socket, client_sockets : list):
	"""
	Closes the given socket remove socket from client_sockets
	\n(in later chapters, also remove user from logged_users dictioary)
	Recieves: socket
	Returns: None
	"""
	
	print(f"[LOGGER] user {conn.getpeername()} logged out...")
	client_sockets.remove(conn)
	conn.close()
	# if conn is not None:
	# 	try:
	# 		client_sockets.remove(conn)
	# 		conn.close()
	# 	except (OSError, ValueError):
	# 		pass 	# Handle potential error if the socket is already closed

	global logged_users
	
	# Implement code ...


def handle_login_message(conn, data):
	"""
	Gets socket and message data of login message. Checks weather user and pass exists and match.
	If not - sends error and finished. If all ok, sends LOGGING OK message and adds user and address to logged_users
	Recieves: socket, message code and data
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

	else:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_failed_msg'], msg= 'incorrect password!')


def manage_to_handle_client_message(conn: socket.socket, cmd: str, data: str, client_sockets : list) -> bool:
	"""
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	\nReturns: \nTrue: if socket ok \n False: if no msg to handle or socket is closed
	"""
	#note! 'from chatlib import PROTOCOL_CLIENT'  to get rid of the module name	
	if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:  # Use comparison with dictionary value
		handle_login_message(conn, data) 
	
	elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
		handle_logout_message(conn, client_sockets)
		return True
	
		# to be added later
	# elif cmd == chatlib.PROTOCOL_CLIENT["my_score_rqst"]:
	# 	# logged_users -> dict of socket['users'] -> user['score']
	# 	handle_getscore_message(conn, username=None)
	elif not cmd:
		# client probably shutdown
		return False

	else:  # Wildcard pattern for unknown commands
		# print(f"Unknown command: '{cmd}' from {conn}")
		send_error(conn, cmd)

	global logged_users	 # To be used later
	# Implement code ...
	
	return True
	



#***********************************************************************
def main():
	# Initializes global users and questions dictionaries using load functions
	global users
	global questions

	users = load_user_database()
	questions = load_questions()
	ServerSocket = setup_socket()
	
	client_sockets = []		# all saved sockets to select.select
	messages_to_send = []  # Tuples of (socket, code, data)

	print("Welcome to Trivia Server!")

	# try:
	while True:
		# Monitor sockets for activity
		ready_to_read, ready_to_write, in_error = select.select([ServerSocket] + client_sockets, [], []) # client_sockets
	
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
					if not manage_to_handle_client_message(current_socket, cmd, data, client_sockets):
						dispose_dead_client(current_socket, client_sockets) # , client_sockets
				# except Exception as e:  # Handle unexpected error
					# print("not good at all\n",e)
					# continue  # Move to the next iteration to avoid processing a closed socket
	
		# Send messages to ready clients
		for message in messages_to_send:
			client, code, msg = message
			if client in ready_to_write:
				build_and_send_message(client, code, msg)
				messages_to_send.remove(message)
	
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
	 to get rid of specifiying the module name as reference ('chatlib.')
"""

"""
except (ConnectionResetError):    
	 prevent the server from crushes when client is shutting down unexpectedly 
	 without logging out correctly.
	 note: if you try to parse his last msg 'None' you will probably meet an error
"""

"""
when the client socket shutdown unexpectetdly it sends an emty msg ''
(since we used .decode('utf-8'))
so make sure to handle it immidiatly at your recv method
as i did in the 'class EmptyMsgRecieved(Excption)'
"""

"""
for python 3.10 and above!

match cmd:
		case value if value == chatlib.PROTOCOL_CLIENT["login_msg"]:  # Use comparison with dictionary value
			handle_login_message(conn, data)
		case value if value == chatlib.PROTOCOL_CLIENT["logout_msg"]:
			handle_logout_message(conn)
			# to be added later
		# case value if value == chatlib.PROTOCOL_CLIENT["my_score_rqst"]:
			# logged_users -> dict of socket['users'] -> user['score']
			# handle_getscore_message(conn, username=None)
		case _:  # Wildcard pattern for unknown commands
			print(f"Unknown command: {cmd} from {conn}")
			send_error(conn, cmd)
"""