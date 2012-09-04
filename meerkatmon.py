#!/usr/bin/env python3

from os.path import dirname, join as path_join
import sys
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

	default_configs_filename = path_join(
		dirname(sys.argv[0]),
		"meerkatmon.conf"
	)

	configs = dict()

	default_configs = {
		'timeout': '10',
		'admin': 'root@localhost',
		'mail_success': False,
	}

	global_configs = {
		'mail_together': 'False',
		'mail_from': 'meerkatmon',
	}

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
		Seperates speciel sections.
		"""
		configs = self.config_file_to_dict(filename)
		configs = self.preprocess_configs(configs)

		self.global_configs.update(
			configs.pop('global', dict())
		)

		self.default_configs.update(
			configs.pop('default', dict())
		)

		self.configs = configs

	def preprocess_configs(self, configs):
		"""
		Method prepares every service in configs for running the tests.
		This may happen only once during runtime (config remains in memory).
		"""
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
		Tries to transform a "target" into ParseResults.
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

	def get_strategies(self):
		"""
		Acquires all strategies (classes) in the module 'strategies'.
		"""
		if not getattr(self, '_strategies', None):
			self._strategies = [	t[1] for t in
									getmembers(strategies_module, isclass) ]
			debug("found stategies: %s" % str(
				[s.__name__ for s in self._strategies]
			))
		return self._strategies

	def assign_strategy(self, section, options):
		"""
		Rates all strategies for all targets and selects the best one.
		"""
		debug("  Searching strategy")
		best_strategy = (None, KNOWLEDGE_NONE)
		for strategy in self.get_strategies():
			strategy_for_target = 	strategy(
										options['parsed_target'],
										options
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
		message = delim.join([
			r['message'] for r in list(results.values())
		])
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
KNOWLEDGE_WORKS = 30
KNOWLEDGE_FULL = 100

class Strategy:
	target = None

	def __init__(self, target, options=None):
		if not isinstance(target, ParseResult):
			TypeError(
				"A Strategy must be initialized with an urlparse.ParseResult"
			)
		self.target = target
		self.options = options or dict()

	def _raise_subclass_error(self, method_name):
		raise NotImplementedError(
			"Subclass %s must provide method %s()" % (
				self.__class__,
				method_name
			)
		)


	def target_knowledge(self):
		"""
		This method is used to ask a strategy for its knowledge about a target (how well it can determine it's availability).

		The return value should be
			KNOWLEDGE_NONE:		I cannot check this target
			KNOWLEDGE_EXISTS:	I can tell you if the target exists
								(ex: ping)
			KNOWLEDGE_ALIVE:	Aditionally, I can tell if target is
								alive (ex HTTP return code 200)
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
		Returns the body containing all relevant information about
		the error/sucess.
		"""
		self._raise_subclass_error('get_mail_message')

	def get_mail_subject(self):
		"""
		Returns a shprt, meaningful summary of the error/success.
		This may be not queried! (Thus should not provide information
		not in message)
		"""
		self._raise_subclass_error('get_mail_subject')

	def get_last_check_success(self):
		"""
		Returns Boolean if last check was successful
		"""
		self._raise_subclass_error('get_last_check_success()')

if __name__ == "__main__":
	monitor = MeerkatMon()
	monitor.auto()
