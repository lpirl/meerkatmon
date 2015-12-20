# coding: UTF8

from smtplib import SMTP
from email.mime.text import MIMEText
from inspect import getmembers, isclass
from sys import argv
from urllib.parse import urlparse
from os.path import join as path_join, dirname
from lib.util import debug
from socket import getfqdn
from tempfile import gettempdir

# see http://bugs.python.org/issue18557
from email.utils import getaddresses

import strategies as strategies_module
from lib.strategies import BaseStrategy, KNOWLEDGE_NONE
from lib.config import ConfigDict, OptionsDict

class MeerkatMon():
	"""
	Class for doing all the administrative work for monitoring.
	"""

	default_configs_filename = path_join(
		dirname(argv[0]),"meerkatmon.conf"
	)

	configs = ConfigDict()

	global_options = OptionsDict({
		'mail_together': 'False',
		'mail_from': 'meerkatmon@%s' % getfqdn(),
		'mail_threaded': 'True',
		'mail_threaded_per_checking_host': 'False',
		'tmp_directory': path_join(gettempdir(), 'meerkatmon')
	})

	global_options_help = {
		'mail_together': 'if False, mails will be sent by section (aggregated othewise)',
		'mail_from': 'envelope sender for mails',
		'mail_threaded': 'enable threaded (per section in config file) view for email clients',
		'mail_threaded_per_checking_host': 'enable additional threading per checking host',
		'tmp_directory': 'a directory where MeerkatMon can store files'
	}

	def __init__(self, config_file=None):
		"""
		Accepts and sets alternative config file, if provided.
		"""
		if config_file:
			self.default_configs_filename = config_file

	def auto(self):
		"""
		Run all actions in the correct order to read config and
		check all targets.
		"""
		debug("started in auto mode")
		self.load_configs()
		self.test_targets()
		self.mail_results()

	def load_configs(self, filename = None):
		"""
		Coordinates loading of config.
		Seperates special sections.
		"""
		configs = self.configs
		configs.fill_from_file(
			filename or self.default_configs_filename
		)

		self.global_options.update(
			configs.pop('meerkatmon_global', dict())
		)
		if 'global' in configs:
			print(
				"WARNING: It seems as if you are using the deprecated section" +
				" name 'global', please rename it to 'meerkatmon_global' as it " +
				"is incompatible with future versions."
			)
			self.global_options.update(configs.pop('global'))

		self.default_configs = configs.pop('meerkatmon_default', dict())
		if 'default' in configs:
			print(
				"WARNING: It seems as if you are using the deprecated section" +
				" name 'default', please rename it to 'meerkatmon_default' as it " +
				"is incompatible with future versions."
			)
			self.default_configs = configs.pop('default')


		configs = self.preprocess_configs(configs)

		self.configs = configs

	def preprocess_configs(self, configs):
		"""
		Method prepares every service in configs for running the tests.
		"""
		self._strategies = MeerkatMon.get_strategies()
		for section, options in configs.items():
			debug("processing service '%s'" % section)
			if section not in ['meerkatmon_default', 'meerkatmon_global']:
				options.apply_defaults(self.default_configs)
				options = self.parse_target(section, options)
				options = self.assign_strategy(section, options)
			configs[section] = options
		return configs

	def parse_target(self, section, options):
		"""
		Tries to transform a "target" into a ParseResults.
		Raises if not possible.
		"""

		target_str = section

		if 'target' in options:
			target_str = options['target']
			print(
				"WARNING: Section '%s' has option 'target'. " % section +
				"This option will go away in the future. " +
				"Please use the section name as target.",
			)
		debug("parsing target '%s'" % target_str)

		if "//" not in target_str:
			target_str = "//" + target_str

		parsed_target = urlparse(target_str)
		options['parsed_target'] = parsed_target
		debug(str(parsed_target))

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
		return {	strategy.__name__: strategy.get_options_help()
					for strategy in cls.get_strategies()}

	@classmethod
	def get_strategies_help(cls):
		"""
		Collects and returns help texts from all strategies.
		"""
		return {	strategy.__name__: strategy.get_help()
					for strategy in cls.get_strategies()}

	def assign_strategy(self, section, options):
		"""
		Rates all strategies for all targets and selects the best one.
		"""
		global_options = self.global_options
		best_strategy = (None, KNOWLEDGE_NONE)
		for strategy in self._strategies:
			strategy_for_target = 	strategy(
										global_options,
										section,
										options,
									)
			knowledge = strategy_for_target.target_knowledge()
			if knowledge > best_strategy[1]:
				best_strategy = (strategy_for_target, knowledge)

		debug("choosen strategy is '%s'" % best_strategy[0].__class__.__name__)
		options['strategy'] = best_strategy[0]

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

			if not options.get_bool('mail_success') and strategy.get_last_check_success():
				continue

			results[section] = {
				'message': strategy.get_mail_message(),
				'subject': strategy.get_mail_subject()
			}

		if self.global_options.get_bool('mail_together'):
			self.mail_results_together(results)
		else:
			self.mail_results_separate(results)

	def _mail_headers_add_references(self, headers, section=None):
		global_options = self.global_options
		if not global_options.get_bool('mail_threaded'):
			return headers
		references = "meerkatmon"
		if section:
			references += '."%s"' % section
		references += "@meerkatmon"
		if global_options.get_bool('mail_threaded_per_checking_host'):
			references += ".%s" % getfqdn()
		headers["References"] = "<%s>" % references
		return headers

	def mail_results_together(self, results):
		"""
		Method mails test results all together to global admin.
		"""
		mail_from = self.global_options['mail_from']
		mail_admin = self.default_configs['admin']
		mail_subject = 'Output from checking ' + ', '.join(list(results.keys()))
		mail_messages_delim = "\n\n%s\n\n" % ("="*80)
		mail_message = mail_messages_delim.join((
			''.join(("--- ", r['subject'], " ---\n", r['message']))
			for r in list(results.values())
		))
		if not mail_message:
			debug("Mailing together. Nothing to do.")
			return
		mail_headers = {
			'From': mail_from,
			'To': mail_admin,
			'Subject': mail_subject,
		}
		self._mail_headers_add_references(mail_headers)

		debug("Mailing together. Collected %s" % str((mail_headers, mail_message)))
		self.send_mails([(mail_headers, mail_message)])

	def mail_results_separate(self, results):
		"""
		Method mails test results all together to admin specified in
		corresponding section or global admin if absent.
		"""

		# list of tuples: (<header dict>, <message str>)
		headers_and_messages = list()

		mail_from = self.global_options['mail_from']
		for section, result in results.items():
			mail_to = self.configs[section]['admin']
			mail_subject = result['subject']
			mail_message = result['message']
			mail_headers = {
				'From': mail_from,
				'To': mail_to,
				'Subject': mail_subject,
			}
			self._mail_headers_add_references(mail_headers, section)
			headers_and_messages.append((mail_headers, mail_message))

		debug("mailing separate. Collected %s" % str(headers_and_messages))
		self.send_mails(headers_and_messages)

	def send_mails(self, headers_and_messages=None):
		"""
		Method actually does send an email.
		"""
		if not headers_and_messages:
			return

		s = SMTP('localhost')
		for headers, message in headers_and_messages:
			msg = MIMEText(message)
			for key, value in headers.items():
				msg[key] = value
			debug("sending %s" % str(msg))
			s.sendmail(
				headers['From'],
				[r[1] for r in getaddresses([headers['To']])],
				msg.as_string()
			)
		s.quit()
