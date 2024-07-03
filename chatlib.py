from typing import List,Tuple, Union

#region Protocol Constants
CMD_FIELD_LENGTH = 16	# Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Other constants
ERROR_RETURN = None  # What is returned in case of an error
#endregion 


##____________________________________________________________________________


# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
"login_msg" : 'LOGIN',
"logout_msg" : 'LOGOUT',
"logged_list_rqst" : 'LOGGED',
"question_rqst" : 'GET_QUESTION',
"answer_question_rqst" : 'SEND_ANSWER',
"my_score_rqst" : 'MY_SCORE',
"top_score_rqst" : 'HIGHSCORE',
} # .. Add more commands if needed


PROTOCOL_SERVER = {
"login_ok_msg" : "LOGIN_OK",
"login_failed_msg" : "ERROR",
"logged_rspn" : 'LOGGED_ANSWER',
"get_question_rspn" : 'YOUR_QUESTION',
"no_question_left_rspn" : 'NO_QUESTIONS',
"correct_answer_rspn" :'CORRECT_ANSWER',
"wrong_answer_rspn" : 'WRONG_ANSWER',
"my_score_rspn" : 'YOUR_SCORE',
"highscore_rspn": 'ALL_SCORE',
} # ..  Add more commands if neede


##____________________________________________________________________________


#region error classes
class UndefinedCommandError(Exception):
    """Exception raised when a command is not defined in the protocol dictionaries."""
    
    def __init__(self, command):
        self.message = f"Undefined command: {command}"
        super().__init__(self.message)


class ProtocolFormatError(Exception):
    """Exception raised when data to be parsed is not as the specified format such as: 
		the number of sectors is incorrect or the delimiters is incorrect."""
    
    def __init__(self, data):
        self.message = f"Message format or delimiters is incorrect: '{data}'"
        super().__init__(self.message)


class DataLengthExceedsLimitError(Exception):
    """Exception raised when data length exceeds the maximum allowed limit of this protocol."""

    def __init__(self, max_data_length):
        self.message = f"Data exceeds the limit supported length which is: {max_data_length}"
        super().__init__(self.message)
#endregion

##____________________________________________________________________________

# subfunction utility
def valid_Length(num) -> bool:
	try:
		integer = int(num)	# isnumeric() -> bool
		if 0 <= integer <=9999:
			return True
	except:
		return False
##____________________________________________________________________________


def build_message(cmd: str, data: str):
	"""
	Gets command name (str) and data field (str) and creates a valid protocol message.
	Returns: str, or None if an error occurred.
	"""
	try:
		cmd = cmd.strip()
		cmd = cmd.upper()

		# Check if the command is defined in the protocol dictionaries
		if cmd not in PROTOCOL_CLIENT.values() and cmd not in PROTOCOL_SERVER.values():
			raise UndefinedCommandError(cmd)

		body_len = len(data)
		if body_len > MAX_DATA_LENGTH:
			raise DataLengthExceedsLimitError(MAX_DATA_LENGTH)

		length_field = str(body_len).zfill(4)
		msg_type = str(cmd.ljust(16))
		full_msg = msg_type + DELIMITER + length_field + DELIMITER + data
		return full_msg

	except (DataLengthExceedsLimitError, UndefinedCommandError) as e:
		print(f'build_message error: {e}')
		return ERROR_RETURN

	except Exception as e:	
		print(f'Unexpected error at build_message: {e}')
		return ERROR_RETURN

##____________________________________________________________________________


def parse_message(data: str) -> Union[Tuple[str, str], Tuple[None, None]]:
	"""
	Parses protocol message and returns command name and data field.
	Returns: cmd (str), msg (str). If some error occurred, returns (None, None).
	"""
	try:
		# Check if the data format fits to the protocol 
		parts = data.split(DELIMITER)
		if len(parts) != 3:
			raise ProtocolFormatError(data)		
		
		cmd, msgLen, msg = parts
		cmd = cmd.strip()
		msgLen = int(msgLen)

		# Check if the msgLen fields fits to the protocol format
		if not valid_Length(msgLen):
			raise ValueError()

		# Check if the command is defined in the protocol dictionaries
		if cmd not in PROTOCOL_CLIENT.values() and cmd not in PROTOCOL_SERVER.values():
			raise UndefinedCommandError()	
		
		return (cmd, msg)	
		
	except ValueError:
		print(f'Value Error at parse_message:\n{msgLen} != {len(msg)}')
		return (ERROR_RETURN, ERROR_RETURN)
		
	except (UndefinedCommandError,ProtocolFormatError) as e:
		print(f'Error at parse_message: {data} \n {e}')
		return (ERROR_RETURN, ERROR_RETURN)

	except Exception as e:
		print(f'Unexpected error at parse_message:{data}\n {e}')	
		return (ERROR_RETURN, ERROR_RETURN)

##____________________________________________________________________________

def join_data(msg_fields: List[str]) -> Union[str, None]:
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter. 
	Returns: string that looks like cell1#cell2#cell3
	"""
	try:
		# Use the join method with '#' as the delimiter
		return DATA_DELIMITER.join(msg_fields)
		
	except Exception as e:
		raise(f'Unexpected error at join_data: {e}')

##____________________________________________________________________________


def split_data(msg : str, expected_fields : int)-> Union[list, None]:
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string 
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns None
	"""
	try:
		# Use the split method with '#' as the delimiter
		fields_list = msg.split(DATA_DELIMITER)
		if len(fields_list) == expected_fields:
			return fields_list

		raise ValueError(f"Recieved {len(fields_list)} instead of {expected_fields} fields")

	except ValueError as e:
		print(f'Error at split_data: {e}')
		return ERROR_RETURN

	except Exception as e:
		print(f'Unexpected error at split_data: {e}')
		return ERROR_RETURN



#_____________________________________bugs fixed and insights______________________________________________
"""
at line 137: 
if not valid_Length(msgLen) or msgLen != len(msg):
there has been a problem since the bytes size at msg with '\n' 
is different from the len(str(msg)).
since the len() doesnt count the '\n' as a str object
"""

"""
raise 'mentioning the exception type while the default is 'Exception' '('args to pass to the exception block')
"""