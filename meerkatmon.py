#!python3 -OO
"""
This moduly mainly provides CLI interface to class MeerkatMon.
"""

from sys import argv

from lib.base import MeerkatMon

if __name__ == "__main__":
	if '--help' in argv or '-h' in argv:
		print("MeerkatMon - gawky script for monitoring services")
		print("")
		print("usage: [python3] ./meerkatmon.py [config file]")
		print("	python3		turns on debug")
		print("	config file	defaults to './meerkatmon.conf'")
		print("")
		print("Global configuration options:\n")
		for option_key, help_text in MeerkatMon.global_options_help.items():
			print(''.join((
				'	',
				option_key,
				': ',
				help_text,
			)))
		print("")
		print("Strategies and their configuration options:")
		strategies_help = MeerkatMon.get_strategies_help()
		options_help = MeerkatMon.get_strategies_options_help()
		for strategy_name, options_list in options_help.items():
			print('\n	---', strategy_name, '---')
			print('	', strategies_help[strategy_name])
			for option_key, help_text in options_list.items():
				print(''.join((
					'	',
					option_key,
					': ',
					help_text,
				)))

		print("")
		print("\nproject page: https://github.com/lpirl/meerkatmon")
		print("Happy peeking!")
		exit(0)
	try:
		monitor = MeerkatMon(argv[1])
	except IndexError as exception:
		monitor = MeerkatMon()
	monitor.auto()
