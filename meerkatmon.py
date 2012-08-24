#!/usr/bin/env python
from urlparse import urlparse, ParseResult
from inspect import getmembers, isclass
import strategies as strategies_module

class MeerkatMon():

	default_configs_filename = "./meerkatmon.conf"
	configs = dict()
	global_config = dict()

	default_config = {
		'target': '',
		'timeout': '10',
		'admin': 'root@localhost',
	}

	def debug(self, msg):
		# TODO: go *args, **kwargs
		if __debug__:
			print(msg)

	def auto(self):
		self.debug("started in auto mode")
		self.load_configs()
		self.preprocess_configs()
		#self.assign_strategies()
		self.test_targets()

	def load_configs(self, filename = None):
		"""
		Method loads configuration from file into dicts.
		"""
		filename = filename or self.default_configs_filename
		self.debug("loading configuration from '%s'" % filename)
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
		self.debug("configuration is: '%s'" % unicode(configs))

		global_config = configs.get('global', self.default_config)
		configs.pop('global', None)

		self.configs = configs

	def preprocess_configs(self):
		"""
		Method prepares every service in configs for monitoring.
		"""
		for section, options in self.configs.iteritems():
			self.debug("processing service '%s'" % section)
			options = self.parse_target(section, options)
			options = self.assign_strategy(section, options)

	def parse_target(self, section, options):
		"""
		Tries to trnasform a "target" into ParseResults.
		Raises if not possible.
		"""
		target_str = options['target']
		self.debug("  parsing target '%s'" % target_str)

		if "//" not in target_str:
			target_str = "//" + target_str

		parsed_target = urlparse(target_str)
		options['parsed_target'] = parsed_target
		self.debug("    " + str(parsed_target))

		return options

	def get_strategies(self):
		"""
		Acquires all strategies (classes) in the module 'strategies'.
		"""
		if not getattr(self, '_strategies', None):
			self._strategies = [	t[1] for t in
									getmembers(strategies_module, isclass) ]
			self.debug("found stategies: %s" % unicode(self._strategies))
		return self._strategies

	def assign_strategy(self, section, options):
		"""
		Rates all strategies for all targets and selects the best one.
		"""
		self.debug("  Searching strategy")
		best_strategy = (None, KNOWLEDGE_NONE)
		for strategy in self.get_strategies():
			strategy_for_target = 	strategy(
										options['parsed_target'],
										options
									)
			knowledge = strategy_for_target.target_knowledge()
			if knowledge > best_strategy[1]:
				best_strategy = (strategy_for_target, knowledge)
		self.debug("    found '%s'" % strategy.__name__)

		return options

	def test_targets(self):
		# TODO
		pass

KNOWLEDGE_NONE = 0
KNOWLEDGE_EXISTS = 10
KNOWLEDGE_ALIVE = 20
KNOWLEDGE_WORKS = 30
KNOWLEDGE_FULL = 100

class Strategy:
	target = None

	def __init__(self, target, configs=None):
		if not isinstance(target, ParseResult):
			TypeError(
				"A Strategy must be initialized with an urlparse.ParseResult"
			)
		self.target = target

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

if __name__ == "__main__":
	monitor = MeerkatMon()
	monitor.auto()
