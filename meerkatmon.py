#!/usr/bin/env python
from urlparse import urlparse, ParseResult
# from cli.app import CommandLineApp

class MeerkatMon(): #CommandLineApp):

	strategies = list()
	config = dict()

	def main(self):
		self.load_config()
		self.collect_strategies()
		self.run_strategies()

	def load_config(self):
		"""
		Method loads configuration from file into dicts.
		"""
		fp = open("./meerkatmon.conf", "r")
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
		self.config = config

	def collect_strategies(self):
		pass

	def run_strategies(self):
		for strategy in self.strategies:
			strategy.setup()
			strategy.do_check()
			strategy.teardown()


KNOWLEDGE_NONE = 0
KNOWLEDGE_EXISTS = 10
KNOWLEDGE_ALIVE = 20
KNOWLEDGE_WORKS = 30
KNOWLEDGE_FULL = 100

class Strategy:
	target = None

	def __init__(self, target):
		if not isinstance(target, ParseResult):
			TypeError("A Strategy must be initialized with an urlparse.ParseResult")
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
		raise NotImplementedError("Subclass %s must provide target_knowledge()" % self.__class__)

if __name__ == "__main__":
	monitor = MeerkatMon()
	monitor.main()

