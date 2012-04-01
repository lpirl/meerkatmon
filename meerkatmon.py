#!/usr/bin/env python
from urlparse import urlparse, ParseResult
from cli.app import CommandLineApp

class MeerkatMon(CommandLineApp):

	strategies = list()
	config = dict()

	def main(self):
		print "running"
		self.load_config(self)
		self.collect_strategies(self)
		self.run_strategies(self)

	def load_config(self):
		pass

	def collect_strategies(self):
		pass

	def run_strategies(self):
		for strategy in self.strategies:
			strategy.setup()
			strategy.do_check()
			strategy.teardown()

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
			0: I cannot check this target
			1: I can tell you if the target is there
			2: I can tell you all above and if it is working
			3: I can tell you all above and do sophisticated checks

		The return values of all strategies will be used to determine
		the best strategy for each target.
		"""
		raise NotImplementedError("Subclass %s must provide target_knowledge()" % self.__class__)

if __name__ == "__main__":
	monitor = MeerkatMon()
	monitor.main()

	import strategies
	print dir(strategies)
	s2 = strategies.ping.Ping("8.8.8.8")
