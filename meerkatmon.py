#!/usr/bin/env python
from urlparse import urlparse, ParseResult
from inspect import getmembers, isclass
import strategies as strategies_module
# from cli.app import CommandLineApp

class MeerkatMon(): #CommandLineApp):

	default_config_filename = "./meerkatmon.conf"
	strategies = list()
	config = dict()

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
		self.load_config()
		self.collect_strategies()
		self.assign_strategies()
		self.test_targets()

	def load_config(self, filename = None):
		"""
		Method loads configuration from file into dicts.
		"""
		filename = filename or self.default_config_filename
		self.debug("loading configuration from '%s'" % filename)
		fp = open(filename, "r")
		config = dict()
		options = dict()
		for line in fp.readlines():
			line = line.strip()

			if line.startswith("#"):
				continue

			if line.startswith('[') and line.endswith(']'):
				options = dict()
				config[line[1:-1]] = options
				continue

			if '=' in line:
				key, value = tuple(line.split("=", 1))
				options[key.strip()] = value.strip()
				continue

		fp.close()
		self.debug("configuration is: '%s'" % unicode(config))
		self.config = self.parse_targets(config)

	def parse_targets(self, config):
		"""
		Tries to trnasform "target"s from config into ParseResults.
		Raises if not possible.
		"""
		for section, options in config.iteritems():

			if section == "global":
				continue

			target_str = options['target']
			self.debug("parsing target for %s (%s)" % (section, target_str))

			if "//" not in target_str:
				target_str = "//" + target_str

			parsed_target = urlparse(target_str)
			options['parsed_target'] = parsed_target
			self.debug("	" + str(parsed_target))

		return config

	def collect_strategies(self):
		"""
		Acquires all strategies (classes) in the module 'strategies'.
		"""
		self.strategies = [	t[1] for t in
							getmembers(strategies_module, isclass) ]
		self.debug("found stategies: %s" % unicode(self.strategies))

	def assign_strategies(self):
		pass

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

	def __init__(self, target, config=None):
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
