#!/usr/bin/env python3

from sys import argv

from lib.base import MeerkatMon
import strategies as strategies_module

if __name__ == "__main__":
	if '--help' in argv or '-h' in argv:
		print("MeerkatMon - gawky script for monitoring services")
		print("")
		print("usage: [python3 -O] ./meerkatmon.py [OPTIONS] [config file]")
		print("	python3 -O	turns off debug")
		print("	config file	defaults to './meerkatmon.conf'")
		print("")
		print("Strategies and their configuration options:")
		strategies_help = MeerkatMon.get_strategies_options_help()
		for startegy_name, options_list in strategies_help.items():
			if options_list:
				print('	---', startegy_name, '---', )
			for optional, option_key, help_text in options_list:
				''.join((
					'[' if optional else '',
					option_key,
					"	",
					help_text,
					']' if optional else '',
				))

		print("")
		print("\nproject page: https://github.com/lpirl/meerkatmon")
		print("Happy peeking!")
		exit(0)
	try:
		monitor = MeerkatMon(argv[1])
	except IndexError as exception:
		monitor = MeerkatMon()
	monitor.auto()
