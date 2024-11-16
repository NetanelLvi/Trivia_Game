import socket
from enum import Enum
import chatlib  # To use chatlib functions or constants, use chatlib.
from typing import *
from time import sleep


#***********************************************************************

#region GLOBAL
#***********************************************************************
SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
menu_format = "____________________"
#endregion

#***********************************************************************

#region ENUMS CLASSES
#***********************************************************************
class Main_Menu(Enum):
	get_score = 1
	get_highscore = 2
	play_question = 3
	get_logged_users = 4
	logout = 5

	def get_menu_name():
		return("Main_Menu")
	def user_guide_option() -> str:
		return(f"'Press the number of your choice':\n (1) 'get score'\n (2) 'Top score'\n (3) 'play question'\n (4) 'get logged users'\n (5) 'logout'\n... ")

#endregion
#***********************************************************************


#region BASIC HELPER METHODS
#***********************************************************************
def validate_numeric_input() -> int:
	while True:
		try:
			player_input = input()
			return int(player_input)

		except ValueError:
			print("Please select a number! ")


def print_fields_options(fields_list : list) -> print:
	"""print every field in a separate line get rid of first one (the title)"""
	try:
		print(f"\n{fields_list.pop(0)}")
		for idx in range(len(fields_list)):
			print(f"({idx+1}) {fields_list[idx]}")
	
	except Exception as e:
		print(f"Error at 'print_fields_options': {e}")


def handle_answer_input() -> str:
	"""
	make sure the input is between 1 - 4
	"""
	while True:
		integer = validate_numeric_input()
		if 1 <= integer <= 4:
			return str(integer)
		print('select a value between 1-4')


#***********************************************************************
#endregion



#region HELPER SOCKET METHODS
#***********************************************************************

def build_and_send_message(conn : socket.socket, code : str, msg : str) -> None:
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.
	Parameters: <- conn (socket.socket), code (str), data (str)
	Returns: -> None
	"""
	try:
		FullMsg = chatlib.build_message(code , msg.strip()).encode('utf-8')
		conn.send(FullMsg)

	except ConnectionResetError:
		print("Connection to server lost. Exiting...1")
		exit()
	except ConnectionAbortedError as e:
		print(f"Server has a problem. connection lost. Exiting...11\n {e}")
		exit()
		
	# except Exception as e:
	# 	print(f" unexpected error at : 'build_and_send_message'\n{e}")


def recv_message_and_parse(conn : socket.socket):
	"""
	Receives a new message from given socket,
	then parses the message using chatlib.
	Parameters: conn (socket.socket)\n
	\n return -> Tuple[str, str]
	If error occurred, will return None, None
	"""
	try:
		RawMsg = conn.recv(chatlib.MAX_DATA_LENGTH).decode('utf-8')
		CleanMsg = RawMsg.strip()
		full_msg = CleanMsg

		cmd, data = chatlib.parse_message(full_msg)
		return cmd, data
	
	except (ConnectionResetError, ConnectionAbortedError):
		# if you got here it means the server stopped running
		exit()
	except Exception as e:
		print(f"Error at : 'recv_message_and_parse()'\n{e}")
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)


def build_send_recv_parse(conn : socket.socket, cmd, data):
	"""a combination of 'build_and_send_message' and 'recv_message_and_parse'
		in order to shorten the code text
		\n return -> Tuple[str, str]
	"""
	try:
		build_and_send_message(conn, cmd, data)
		return recv_message_and_parse(conn)
	
	except ConnectionResetError:
		print("Connection to server lost. Exiting...2")
		exit()
	except Exception as e:
		print(f"Error at : 'build_send_recv_parse()'\n{e}")
		return (chatlib.ERROR_RETURN , chatlib.ERROR_RETURN)


def connect() -> socket.socket:
	"""init a client and connecting to the Game server"""
	try:
		client = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
		client.connect((SERVER_IP, SERVER_PORT))
		return client

	except Exception as e:
		print(f"Connection failed, due to error at : 'connect'\n{e}")
		exit()


def exit_the_game(conn : socket.socket) -> None:
		"""use this after logout() to disconnect correctly
		\n use this method without logout() when connection lost 
		"""
	# if conn is not None:
		try:
			logout(conn)
			conn.close()
		except OSError:
			pass	# Handle potential error if the socket is already closed
		sleep(1)
		print(f"disconnected from the server!\n")
		exit()


#endregion
#***********************************************************************

#region MESSAGES TO SERVER METHODS 
#***********************************************************************

def login(conn : socket.socket) -> None:
	""" after establishing connection to server logging in with user details """
	try:
		while True:
			username = input("Please enter username: \n")
			password = input("Please enter your password: \n")

			playerID = chatlib.join_data([username, password])
			build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],playerID)

			if recv_message_and_parse(conn)[0] == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
				print(f"User '{username}': successfully logged in.\n")
				break
			print("Wrong user or id!")

	except Exception as e:
		print(f"error at : 'login'\n{e}")


def logout(conn : socket.socket) -> None:
	"""
		sending logout message to the server.
		use only when logging out the game correctly
		and when the sockets connection is intact
	"""
	try:
		build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"],"")	
		print('logging out from the game...')
		sleep(2)
	except Exception as e:
		print("can't logout correctly\n", e)



def get_score(conn : socket.socket) -> print:
	"""Using the helper function in our scope to print the user current score.
		get socket (conn) as argument and send 'my_score_rqst' to the server and recv 'get_question_rspn' """
	try:
		Ccode , Cdata = chatlib.PROTOCOL_CLIENT['my_score_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccode, Cdata)

		if Scmd != chatlib.PROTOCOL_SERVER['my_score_rspn']:
			print(f'Error fetching your score: {Sdata}')
			return 
		print(f"Your score is: {Sdata}.\n")

	except Exception as e:
		print(f"Error at : 'get_score'\n{e}")


def get_highscore(conn : socket.socket) -> print:
	"""using the helper method in our scope 
		fetching the top score from the server
		conn : socket -> None"""
	try:
		Ccode , Cdata = chatlib.PROTOCOL_CLIENT['top_score_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccode, Cdata)

		if Scmd != chatlib.PROTOCOL_SERVER['highscore_rspn']:
			print(f'Error fetching high scores: cmd {Scmd} ,data {Sdata}')
			return 
		print(f"Top players: \n{Sdata}\n")

	except Exception as e:
		print(f"Error at : 'get_highscore'\n{e}")


def get_question(conn : socket.socket) -> Tuple[str, list]:
		"""fetching a random question from the question stock in the server"""

		Ccode , Cdata = chatlib.PROTOCOL_CLIENT['question_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccode, Cdata)

		if Scmd == chatlib.PROTOCOL_SERVER['no_question_left_rspn']:
			print("no questions left.")
			return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN

		Question = chatlib.split_data(Sdata,6)
		Question_Id = Question.pop(0)
		return str(Question_Id), Question


def get_logged_users(conn : socket.socket) -> print:
	"""getting a list of all connected players from the server"""
	try:
		Ccmd , Cdata = chatlib.PROTOCOL_CLIENT['logged_list_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccmd, Cdata)

		if Scmd == chatlib.PROTOCOL_SERVER['logged_rspn']:
			logged_number = len(Sdata.split(',')) 
			print(f"\nlogged members: {logged_number}")
			print(Sdata)
			return 
		
	except Exception as e:
		print(f"Error at : fetching logged users \n{e}")


def send_answer(conn : socket.socket, Question_Id, answer)  -> Tuple[str, str]:
	""" send answer to a given question according to the protocol
		\njoin_data([]) get a list-like argument
	"""
	# try:
	Question_Id = str(Question_Id)
	answer = str(answer)
	Ccmd = chatlib.PROTOCOL_CLIENT["answer_question_rqst"]
	Cdata = chatlib.join_data([Question_Id, answer])
	Scmd, Sdata = build_send_recv_parse(conn, Ccmd, Cdata)
	return (Scmd, Sdata)

	# except:
	print(f"Error at : 'send answer'\n")
	return (chatlib.ERROR_RETURN , chatlib.ERROR_RETURN)


#endregion
#***********************************************************************

#region GAMEPLAY METHODS
#***********************************************************************
def handle_menus_input(enum_class :Enum) -> str:
	"""Getting an input and validate it to be right option to the current menu
		this is a block function until available choice is picked. 
		returning a function name from the enum argument to be execute in the main()"""
	
	# print(f"\n{'__'*20}{enum_class.get_menu_name()}{'__'*20} \n\n")
	player_choice = input(enum_class.user_guide_option())
	while True:
		try:
			choice = int(player_choice)
			if choice in [item.value for item in enum_class]:
				# print(enum_class.user_guide_option())
				return enum_class(choice).name
		except ValueError:
			pass
		except ConnectionResetError:
			print("Connection to server lost. Exiting...3")  #
			exit()
		player_choice = input("'Invalid choice! Please select a valid menu option.'\n")


def play_question(conn  : socket.socket) -> None:
	"""Manages the question-answer procedure of the game"""
	try:
		Question_Id, DataList = get_question(conn)
		if not DataList:
			print(f'\n\n{menu_format}GameOver{menu_format}')
			return

		# printing question
		print_fields_options(DataList)
		# getting player ans
		my_answer = handle_answer_input() 
		# sending ans to server
		Scmd, Sdata = send_answer(conn, Question_Id ,my_answer)
		# getting rspn weather true or not
		if Scmd == chatlib.PROTOCOL_SERVER['correct_answer_rspn']:
		# print the server rspn
			print('Correct!')
			return
		
		print(f'Not correct, the answer is: {Sdata}')	

	except ConnectionResetError:
			print("Connection to server lost. Exiting...4")
			exit()
	# except: # Exception as e
	# 	print(f"Unexpected Error at : 'play_question'\n")


#endregion
#***********************************************************************


def main():
	try:
		conn = connect() # Establish connection with the server

		login(conn)		 # User login procedure

			#____The GamePlay client <-> server communication_____

		# Main Menu screen
		while True:
			print(f"{menu_format}{Main_Menu.get_menu_name()}{menu_format}\n")
			selected_action = handle_menus_input(Main_Menu)
			if selected_action != 'logout':
				globals()[selected_action](conn)
				Main_Menu.user_guide_option()
			else:	# means you logged out
				break



	# Handle crushes correctly
	except ConnectionResetError:
		print("Connection to server lost. Exiting...")
		exit()

	except Exception as error_msg: # Exception as error_msg
		print(f'The game crushed due to a critical error: {error_msg}\n') # {error_msg}
		exit()

	finally:
		exit_the_game(conn)





if __name__ == '__main__':
# make sure the server is running first
	main()	# when playing the game this method will be called to control the GamePlay











#_____________________________________bugs fixed and insights______________________________________________
"""
this is how we use a dynamic call to function in our scope (scope: current file and imported module):		
'globals()[selected_action]("args")'
"""

"""
.pyc  -> python compiled files (pc language)
you need to run these with the specific version its made of
otherwise you'll encounter  'bad magic number error'
"""

"""
'builtin_function_or_method' object is not subscriptable -> means you used wrong access method [] <-> () <-> {}
"""

"""
print(f'\n'.join(map(str, DataList)))	# for data as list
print(Question_Id.replace('#', '\n')) 	# for data as string
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