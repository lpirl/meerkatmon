"""
Module for everything that does not fit into one of the other modules.
"""

COLOR_STD = '\033[0m'
COLOR_FAIL = '\033[31m'
COLOR_LIGHT = '\033[33m'

def debug(msg):
	"""
	helper method to honor __debug__ for debug printing
	"""
	if __debug__:
		print(msg)
