##############################################################################
# server.py
"""- the help i  got from a friend

- solving the fd = -1 error of select.select() by making the client_sockets []
  removing the disconnected socket from it
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
client_sockets = []

# CONSTANT #
#***********************************************************************
ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"	#   or "0.0.0.0" for all routed networks



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

	except (ConnectionResetError, ConnectionAbortedError, OSError):  # Handle unexpected client disconnection
		# print(f"A client disconnected unexpectedly.")
		# client_sockets.remove(conn)
		# print(client_sockets)		#
		# try:
		# 	conn.close()  # Ensure socket is closed
		# except OSError:
			pass 	# Handle potential error if the socket is already closed


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
		CleanMsg = RawMsg.strip()
		full_msg = CleanMsg

		cmd, data = chatlib.parse_message(full_msg)
		print("[CLIENT] ",full_msg)	  # Debug print
		return cmd, data
	
	except (ConnectionResetError, ConnectionAbortedError, OSError):  # Handle unexpected client disconnection
		print(f"A client disconnected unexpectedly. (line 70)")
		client_sockets.remove(conn)
		try:
			conn.close()  # Ensure socket is closed
		except OSError:
			pass 	# Handle potential error if the socket is already closed
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)

	except Exception as e:
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

	


# SOCKET CREATOR
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



	
##### MESSAGE HANDLING
#***********************************************************************

def handle_getscore_message(conn, username):
	global users	 # This is needed to access the same users dictionary from all functions

	# Implement this in later chapters

	
def handle_logout_message(conn : socket.socket):
	"""
	Closes the given socket (in later chapters, also remove user from logged_users dictioary)
	Recieves: socket
	Returns: None
	"""
	# conn.close()
	global client_sockets
	if conn is not None:
		try:
			client_sockets.remove(conn)
			conn.close()
		except OSError:
			pass 	# Handle potential error if the socket is already closed
	print(f"user from: {conn} logged out...")

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


def handle_client_message(conn: socket.socket, cmd: str, data: Any) -> None:
	"""
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	Returns: None
	"""
	#note! 'from chatlib import PROTOCOL_CLIENT'  to get rid of the module name	
	if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:  # Use comparison with dictionary value
		handle_login_message(conn, data) 
	
	elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
		handle_logout_message(conn)
	
		# to be added later
	# elif cmd == chatlib.PROTOCOL_CLIENT["my_score_rqst"]:
	# 	# logged_users -> dict of socket['users'] -> user['score']
	# 	handle_getscore_message(conn, username=None)
	
	else:  # Wildcard pattern for unknown commands
		print(f"Unknown command: '{cmd}' from {conn}")
		send_error(conn, cmd)


	global logged_users	 # To be used later
	
	# Implement code ...
	



#***********************************************************************
def main():
	# Initializes global users and questions dictionaries using load functions
	global users
	global questions
	global client_sockets

	users = load_user_database()
	questions = load_questions()

	ServerSocket = setup_socket()
	
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
				print(f"New client joined! {client_address}")
				client_sockets.append(client_sock)
			else:
				# Handle communication with existing clients
				# try:
					cmd, data = recv_message_and_parse(current_socket)	
					handle_client_message(current_socket, cmd, data)
				# except (ConnectionResetError,ConnectionAbortedError, Exception):  # Handle unexpected client disconnection
					# print(f"Client {client_address} disconnected unexpectedly. (line 259)")
					# try:
					# 	client_sockets.remove(current_socket)
					# 	current_socket.close()  # Ensure socket is closed
					# except OSError:		# prevent crushing if it;s closed already
					# 	print('OSError')
						# pass
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
except ConnectionResetError:    
	 add to avoid server crushes when client is shutting down unexpectedly 
	 without logging out socket.close() !!!!!!!!!!

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