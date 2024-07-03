import socket
from enum import Enum
import chatlib  # To use chatlib functions or consts, use chatlib.
from typing import *
from time import sleep

#***********************************************************************

#region CONSTS
#***********************************************************************
SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
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
			pass
		player_input = input("Please select a number")


def print_fields_options(fields_list : list) -> print:
	try:
		print(f"\n{fields_list.pop(0)}")
		for idx in range(len(fields_list)):
			print(f"({idx+1}) {fields_list[idx]}")
	
	except Exception as e:
		print(f"Error at 'print_fields_options': {e}")


#***********************************************************************
#endregion



#region HELPER SOCKET METHODS
#***********************************************************************

def build_and_send_message(conn : socket.socket, code : str, msg : str) -> None:
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), data (str)
	Returns: Nothing
	"""
	try:
		FullMsg = chatlib.build_message(code , msg.strip()).encode('utf-8')
		# print(f"sending to server: {FullMsg}")
		conn.send(FullMsg)

	except ConnectionResetError:
		print("Connection to server lost. Exiting...")
	except Exception as e:
		print(f"error at : 'build_and_send_message'\n{e}")


def recv_message_and_parse(conn : socket.socket) -> Tuple[str, str]:
	"""
	Recieves a new message from given socket,
	then parses the message using chatlib.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message. 
	If error occured, will return None, None
	"""
	try:
		RawMsg = conn.recv(chatlib.MAX_DATA_LENGTH).decode('utf-8')
		CleanMsg = RawMsg.strip()
		full_msg = CleanMsg

		cmd, data = chatlib.parse_message(full_msg)
		return cmd, data
	
	except Exception as e:
		print(f"Error at : 'recv_message_and_parse()'\n{e}")
		return (chatlib.ERROR_RETURN, chatlib.ERROR_RETURN)


def build_send_recv_parse(conn, cmd, data) -> Tuple[str, str]:
	"""a combination of 'build_and_send_message' and 'recv_message_and_parse'
		in order to shorten the code text
	"""
	try:
		build_and_send_message(conn, cmd, data)
		return recv_message_and_parse(conn)
	
	except ConnectionResetError:
		print("Connection to server lost. Exiting...")
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
	# try:
	# 	logout(conn)
	# except Exception as e:
	# 	print("cant logout correctly\n", e)
	conn.close()
	sleep(3)
	print(f"disconnecting from the server!\n")
	exit()


#endregion
#***********************************************************************

#region MESSAGES TO SERVER METHODS 
#***********************************************************************

def login(conn) -> None:
	""" after establishing connection to server logging in with user details 
	"""
	try:
		while True:
			username = input("Please enter username: \n")
			password = input("Please enter your password: \n")

			playerID = chatlib.join_data([username, password])
			build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],playerID)

			if recv_message_and_parse(conn)[0] == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
				print(f"User '{username}': succesfuly logged in.")
				break
			print("Wrong user or id!")

	except Exception as e:
		print(f"error at : 'login'\n{e}")


def logout(conn : socket.socket) -> None:
	"""
		sendig logout message to the server.
		use only when loggin out the game correctly
		and when the sockets connection is intact
	"""
	try:
		build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"],"")	
		print('loggin out from the game...')
		sleep(3)
	except Exception as e:
		print("can't logout correctly\n", e)



def get_score(conn) -> print:
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


def get_highscore(conn) -> print:
	"""using the helper method in our scope 
		fetching the top score from the server
		conn : socket -> None"""
	try:
		Ccode , Cdata = chatlib.PROTOCOL_CLIENT['top_score_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccode, Cdata)

		if Scmd != chatlib.PROTOCOL_SERVER['highscore_rspn']:
			print(f'Error fetching high scores: cmd {Scmd} ,data {Sdata}')
			return 
		print(f"Top players: \n{Sdata}.\n")

	except Exception as e:
		print(f"Error at : 'get_highscore'\n{e}")


def get_question(conn) -> Tuple[int, list]:
		"""fetching a random question from the qustion stock in the server"""

		Ccode , Cdata = chatlib.PROTOCOL_CLIENT['question_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccode, Cdata)

		if Scmd == chatlib.PROTOCOL_SERVER['no_question_left_rspn']:
			print("no questions left.")
			return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN

		Question = chatlib.split_data(Sdata,6)
		Question_Id = Question.pop(0)
		return Question_Id, Question


def get_logged_users(conn) -> print:
	"""getting a list of all connected players from the server"""
	try:
		Ccmd , Cdata = chatlib.PROTOCOL_CLIENT['logged_list_rqst'] , ''
		Scmd, Sdata = build_send_recv_parse(conn, Ccmd, Cdata)

		if Scmd == chatlib.PROTOCOL_SERVER['logged_rspn']:
			logged_number = len(Sdata.split(',')) 
			print(f"\nlogged members: {logged_number}")
			print(Sdata)
			# for idx in range(len(Sdata)):
			# 	print(f"({idx+1}) {Sdata[idx]}")
			return 
		
	except Exception as e:
		print(f"Error at : fetching logged users \n{e}")


def send_answer(conn, Question_Id, anwer) -> Tuple[str, str]:
	""" send answer to a given question according to the protocol
		join_data([]) get a list-like argument
	"""
	try:
		Ccmd = chatlib.PROTOCOL_CLIENT["send_answer_rqst"]
		Cdata = chatlib.join_data([Question_Id, anwer])

		Scmd, Sdata = build_send_recv_parse(conn, Ccmd, Cdata)
		return Scmd, Sdata

	except Exception as e:
		print(f"Error at : 'send_answer'\n{e}")
		return (chatlib.ERROR_RETURN , chatlib.ERROR_RETURN)

#region future command
# def for_future_updates(conn):
# 	""" a pattern for future features
# 	"""
# 	try:
# 		pass

# 	except Exception as e:
# 		print(f"Error at : ' '\n{e}")

#endregion

#endregion
#***********************************************************************

#region GAMEPLAY METHODS
#***********************************************************************
def handle_menus_input(enum_class :Enum) -> str:
	"""Getting an input and validat it to be right option to the current menu
		this is a block function untill availeable choice is picked. 
		returning a function name from the enum argument to be execute in the main()"""
	
	print(f"\n{'__'*20}{enum_class.get_menu_name()}{'__'*20} \n\n")
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
			print("Connection to server lost. Exiting...")
			exit()
		player_choice = input("'Invalid choice! Please select a valid menu option.'")


def play_question(conn) -> None:
	"""Manages the question-answer procedure of the game"""
	try:
		Question_Id, DataList = get_question(conn)
		if not DataList:
			print(f'\n\n{'__'*20}GameOver{'__'*20}')
			return

		# printing question
		print_fields_options(DataList)
		my_answer = input("\nyour answer: ")
		# sending ans to server
		Scmd, Sdata = send_answer(conn,Question_Id ,my_answer)
		# getting rspn weather true or not
		if Scmd == chatlib.PROTOCOL_SERVER['correct_answer_rspn']:
		# print the server rspn
			print('Correct!')
			return
		
		print(f'Not correct, the answer is: {Sdata}')	

	except Exception as e:
		print(f"Error at : 'play_question'\n{e}")


#endregion
#***********************************************************************


def main():
	try:
		conn = connect() # Establish connection with the server

		login(conn)		 # User login procedure

			#____The GamePlay client <-> server communication_____

		# Main Menu screen
		while True:
			selected_action = handle_menus_input(Main_Menu)
			globals()[selected_action](conn)
			if selected_action != 'logout':
				Main_Menu.user_guide_option()
			else:	# means you logged out
				break



	# Handle crushes correctly
	except ConnectionResetError:
		print("Connection to server lost. Exiting...")
		# exit_the_game(conn)


	except Exception as error_msg:
		print(f'The game crushed due to a critical error:\n {error_msg}')
		# exit_the_game(conn)

	finally:
		exit_the_game(conn)
		
		
	


if __name__ == '__main__':
# make sure the server is running first
	main()

	r"""
	cd C:\Users\netan\OneDrive\Documents\VisualStudioCode-projects\python_projects\Network_py_course\rolling_task
	c:\Users\netan\OneDrive\Documents\VisualStudioCode-projects\python_projects\Network_py_course\python_38.venv\Scripts\python.exe server.pyc
	python Trivia_client_v5.py
	""" 
	# when playing the game this method will be called to control the GamePlay











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