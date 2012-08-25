#!/usr/bin/env python
from urlparse import urlparse, ParseResult
from inspect import getmembers, isclass
import strategies as strategies_module

COLOR_STD='\033[0m'
COLOR_FAIL='\033[31m'
COLOR_LIGHT='\033[33m'


def debug(msg):
	# TODO: go *args, **kwargs
	if __debug__:
		print(msg)

class MeerkatMon():

	default_configs_filename = "./meerkatmon.conf"
	configs = dict()
	global_config = dict()

	default_global_config = {
		'target': '',
		'timeout': '10',
		'admin': 'root@localhost',
		'mail_success': 'True',
	}

	def auto(self):
		debug("started in auto mode")
		self.load_configs()
		self.preprocess_configs()
		self.test_targets()

	def load_configs(self, filename = None):
		"""
		Method loads configuration from file into dicts.
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
				configs[line[1:-1]] = options
				continue

			if '=' in line:
				key, value = tuple(line.split("=", 1))
				options[key.strip()] = value.strip()
				continue

		fp.close()
		debug("configuration is: '%s'" % unicode(configs))

		global_config = configs.get('global', dict())
		configs.pop('global', None)
		global_config.update(self.default_global_config)

		self.global_config = global_config
		self.configs = configs

	def preprocess_configs(self):
		"""
		Method prepares every service in configs for monitoring.
		"""
		for section, options in self.configs.iteritems():
			debug("processing service '%s'" % section)
			options = self.parse_target(section, options)
			options = self.assign_strategy(section, options)

	def parse_target(self, section, options):
		"""
		Tries to trnasform a "target" into ParseResults.
		Raises if not possible.
		"""
		target_str = options['target']
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
			debug("found stategies: %s" % unicode(self._strategies))
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

		debug("    found '%s'" % strategy.__name__)
		options['strategy'] = best_strategy[0]

		return options

	def test_targets(self):
		for section, options in self.configs.iteritems():
			debug("do check for %s" % section)
			result = options['strategy'].do_check()

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

	def setup(self):
		pass

	def teardown(self):
		pass

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
		raise NotImplementedError(
			"Subclass %s must provide target_knowledge()" % self.__class__
		)

	def do_check(self):
		"""
		Method that actually runs the checks.
		"""
		raise NotImplementedError(
			"Subclass %s must provide do_check()" % self.__class__
		)

	# TODO: add get_mail_body(), get_mail_subject()

if __name__ == "__main__":
	monitor = MeerkatMon()
	monitor.auto()
