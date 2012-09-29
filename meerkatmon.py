#!/usr/bin/env python3

from sys import argv
import stat
from os import access, environ, pathsep, X_OK, sep, chmod, makedirs
from os.path import isfile, join as path_join, dirname, isdir
from urllib.parse import urlparse, ParseResult
from inspect import getmembers, isclass
from smtplib import SMTP
from email.mime.text import MIMEText

import strategies as strategies_module

COLOR_STD='\033[0m'
COLOR_FAIL='\033[31m'
COLOR_LIGHT='\033[33m'

def debug(msg):
	if __debug__:
		print(msg)

class MeerkatMon():

	default_configs_filename = ""

	configs = dict()

	default_configs = {
		'timeout': '10',
		'admin': 'root@localhost',
		'mail_success': False,
	}

	global_configs = {
		'mail_together': 'False',
		'mail_from': 'meerkatmon',
		'tmp_directory': '/tmp/meerkatmon'
	}

	def __init__(self, config_file=None):
		"""
		Accepts and sets alternative config file, if provided.
		"""
		self.default_configs_filename = config_file or path_join(
			dirname(argv[0]),
			"meerkatmon.conf"
		)

	def auto(self):
		"""
		Run all actions in the correct order to read config and
		check all targets.
		"""
		debug("started in auto mode")
		self.load_configs()
		self.test_targets()
		self.mail_results()

	def config_file_to_dict(self, filename = None):
		"""
		Method loads configuration from file into dictionary.
		"""
		filename = filename or self.default_configs_filename
		debug("loading configuration from '%s'" % filename)
		fp = open(filename, "r")
		configs = dict()
		options = dict()
		for line in fp.readlines():
			line = line.strip()

			if line.startswith("#"):
				continue

			if line.startswith('[') and line.endswith(']'):
				options = dict()
				configs[line[1:-1].strip()] = options
				continue

			if '=' in line:
				key, value = tuple(line.split("=", 1))
				options[key.strip()] = value.strip()
				continue

		fp.close()
		debug("configuration is: '%s'" % str(configs))

		return configs

	def load_configs(self, filename = None):
		"""
		Coordinates loading of config.
		Seperates special sections.
		"""
		configs = self.config_file_to_dict(filename)

		self.global_configs.update(
			configs.pop('global', dict())
		)

		self.default_configs.update(
			configs.pop('default', dict())
		)

		configs = self.preprocess_configs(configs)

		self.configs = configs

	def preprocess_configs(self, configs):
		"""
		Method prepares every service in configs for running the tests.
		"""
		self._strategies = MeerkatMon.get_strategies()
		for section, options in configs.items():
			debug("processing service '%s'" % section)
			options = self.convert_types(section, options)
			if section not in ['default', 'global']:
				options = self.apply_defaults(section, options)
				options = self.parse_target(section, options)
				options = self.assign_strategy(section, options)
			configs[section] = options
		return configs

	def apply_defaults(self, section, options):
		"""
		Applies default configs to section.
		"""
		full_options = dict(self.default_configs)
		full_options.update(options)
		return full_options

	def parse_target(self, section, options):
		"""
		Tries to transform a "target" into a ParseResults.
		Raises if not possible.
		"""

		try:
			target_str = options['target']
		except KeyError:
			raise KeyError(
				"Section '%s' has no target. " % section +
				"We won't ignore this error since it is an obvious " +
				"misconfiguration"
			)
		debug("  parsing target '%s'" % target_str)

		if "//" not in target_str:
			target_str = "//" + target_str

		parsed_target = urlparse(target_str)
		options['parsed_target'] = parsed_target
		debug("    " + str(parsed_target))

		return options

	@classmethod
	def get_strategies(cls):
		"""
		Acquires all strategies (classes) in the module 'strategies'.
		"""
		strategies = [	t[1] for t in
						getmembers(strategies_module, isclass) ]
		debug("found stategies: %s" % str(
				[s.__name__ for s in strategies]
			))
		return strategies


	@classmethod
	def get_strategies_options_help(cls):
		"""
		Collects and returns options and the corresponding help text
		from all strategies.
		"""
		helps = dict()
		for strategy in cls.get_strategies():
			helps[strategy.__name__] = strategy.get_options_help()
		return helps

	def assign_strategy(self, section, options):
		"""
		Rates all strategies for all targets and selects the best one.
		"""
		debug("  Searching strategy")
		global_configs = self.global_configs
		best_strategy = (None, KNOWLEDGE_NONE)
		for strategy in self.get_strategies():
			strategy_for_target = 	strategy(
										global_configs,
										section,
										options,
									)
			knowledge = strategy_for_target.target_knowledge()
			if knowledge > best_strategy[1]:
				best_strategy = (strategy_for_target, knowledge)

		debug("    choosen '%s'" % strategy.__name__)
		options['strategy'] = best_strategy[0]

		return options

	def convert_types(self, section, options):
		"""
		Parses types from values from options.
		"""

		for key, value in options.items():
			if key in ['mail_success', 'mail_together']:
				options[key] = bool(value)

		return options

	def test_targets(self):
		"""
		Method simply runs tests for every section.
		"""
		for section, options in self.configs.items():
			debug("do check for %s" % section)
			options['strategy'].do_check()

	def mail_results(self):
		"""
		Method is responsible for informing the cerresponding admin
		about errors and success (if desired).
		"""
		results = dict()
		for section, options in self.configs.items():
			strategy = options['strategy']

			if not options['mail_success'] and strategy.get_last_check_success():
				continue

			results[section] = {
				'message': strategy.get_mail_message(),
				'subject': strategy.get_mail_subject()
			}

		if self.global_configs['mail_together']:
			self.mail_results_together(results)
		else:
			self.mail_results_separate(results)

	def mail_results_together(self, results):
		"""
		Method mails test results all together to global admin.
		"""
		mail_from = self.global_configs['mail_from']
		admin = self.default_configs['admin']
		subject = 'Output from checking ' + ', '.join(list(results.keys()))
		delim = "\n\n%s\n\n" % ("="*80)
		message = delim.join((
			''.join(("--- ", r['subject'], " ---\n", r['message']))
			for r in list(results.values())
		))
		if not message:
			debug("Mailing together. Nothing to do.")
			return
		srsm_tuple = (mail_from, admin, subject, message)
		debug("Mailing together. Collected %s" % str(srsm_tuple))
		self.send_mails([srsm_tuple])

	def mail_results_separate(self, results):
		"""
		Method mails test results all together to admin specified in
		corresponding section or global admin if absent.
		"""
		srsm_tuples = list()
		mail_from = self.global_configs['mail_from']
		for section, result in results.items():
			admin = self.configs[section]['admin']
			subject = result['subject']
			message = result['message']
			srsm_tuples.append((
				(mail_from, admin, subject, message)
			))
		debug("mailing separate. Collected %s" % str(srsm_tuples))
		self.send_mails(srsm_tuples)

	def send_mails(self, sender_recipient_subject_message_tuples=None):
		"""
		Method actually does send an email.
		"""
		if not sender_recipient_subject_message_tuples:
			return

		s = SMTP('localhost')
		for srsm in sender_recipient_subject_message_tuples:
			msg = MIMEText(srsm[3])
			msg['From'] = srsm[0]
			msg['To'] = srsm[1]
			msg['Subject'] = srsm[2]
			debug("sending %s" % str(msg))
			s.sendmail(srsm[0], [srsm[1]], msg.as_string())
		s.quit()


KNOWLEDGE_NONE = 0
KNOWLEDGE_EXISTS = 10
KNOWLEDGE_ALIVE = 20
KNOWLEDGE_NOTICE = 40
KNOWLEDGE_WORKS = 50
KNOWLEDGE_FULL = 100

class BaseStrategy:
	target = None

	def __init__(self, global_options, section, options):
		target = options['parsed_target']
		if not isinstance(target, ParseResult):
			TypeError(
				"A Strategy must be initialized with an urlparse.ParseResult"
			)
		self.global_options = global_options
		self.section = section
		self.options = options
		self.target = target


	def _raise_subclass_error(self, method_name):
		raise NotImplementedError(
			"Subclass %s must provide method %s()" % (
				self.__class__,
				method_name
			)
		)

	def which(self, search_program):
		"""
		Helps finding a binary.
		Takes binary name and returns full path to it.
		Inspired by http://stackoverflow.com/a/377028
		"""
		is_exec = lambda x: isfile(x) and access(x, X_OK)

		if dirname(search_program) and is_exec(search_program):
			return search_program

		for path in environ["PATH"].split(pathsep):
			exec_file = path_join(path, search_program)
			if is_exec(exec_file):
				return exec_file

		return None

	def target_knowledge(self):
		"""
		This method is used to ask a strategy for its knowledge about a
		target (how well it can determine it's availability).

		The return value should be
			KNOWLEDGE_NONE:		I cannot check this target
			KNOWLEDGE_EXISTS:	I can tell you if the target exists
								(ex: ping)
			KNOWLEDGE_ALIVE:	Aditionally, I can tell if target is
								alive (ex HTTP return code 200)
			KNOWLEDGE_NOTICE:	Aditionally, I can tell you if the target
								behaves similar to the last check.
			KNOWLEDGE_WORKS:	Aditionally, I can tell you if the target
								works as expected
								(ex: delivers expected HTML)
			KNOWLEDGE_FULL		I check the whole fuctionality of the
								target

		The return values of all strategies will be used to determine
		the best strategy for each target.
		"""
		self._raise_subclass_error('target_knowledge')

	def do_check(self):
		"""
		Method that actually runs the checks.
		"""
		self._raise_subclass_error('do_check')

	def get_mail_message(self):
		"""
		Returns the subject and body containing *all* relevant
		information about the error/sucess.
		Will never be mailed w/o information from get_mail_subject.
		"""
		self._raise_subclass_error('get_mail_message')

	def get_mail_subject(self):
		"""
		Returns a short, meaningful summary of the error/success.
		Will never be mailed w/o information from get_mail_message.
		"""
		self._raise_subclass_error('get_mail_subject')

	def get_last_check_success(self):
		"""
		Returns Boolean if last check was successful
		"""
		self._raise_subclass_error('get_last_check_success()')

	def get_sample_filename(self):
		"""
		Returns the file name where the state is saved in.
		"""
		file_name = "__".join((
			environ["LOGNAME"],
			self.section,
		)) + ".sample"
		file_name = file_name.replace(sep, "_")
		return path_join(
			self.global_options['tmp_directory'],
			file_name,
		)

	def load_sample(self):
		"""
		Returns the last saved sample as string.
		"""
		try:
			with open(self.get_sample_filename(), 'r') as f:
				sample_data = f.read()
			return sample_data
		except IOError as e:
			return None

	def save_sample(self, string):
		"""
		Saves a sample (string) to file.
		"""
		file_name = self.get_sample_filename()
		dir_name = dirname(file_name)
		if not isdir(dir_name):
			makedirs(
				dir_name,
				0 | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
			)
		with open(file_name, 'wb') as f:
			f.write(
				bytes(
					str(string, errors='replace'),
					'utf8'
				)
			)
		chmod(file_name, 0 | stat.S_IRUSR | stat.S_IWUSR)

	@classmethod
	def get_options_help(cls):
		"""
		Returns all possible options and the corresponding help texts
		for this strategy. This return value is a list of tuples in the
		following form:
		(optional, key, help_text, )
			optional: boolean if option required
		"""
		return []

if __name__ == "__main__":
	if argv[1] in ['--help', '-h']:
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
			for optional, key, help_text in options_list:
				''.join((
					'[' if optional else '',
					key,
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
