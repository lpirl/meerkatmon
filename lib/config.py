"""
Various classes to simplify handling of configuration.

Terminology:
	config[uration]		whole set of sections and their options
	section				set of options
	option				key, value pair
"""

from lib.util import debug

class OptionsDict(dict):
	"""
	Like a dictionary, but can privede values casted to some type.
	"""

	true_strings = ("yes", "true", "1", )

	def apply_defaults(self, dict_with_defaults):
		"""
		Like dict's update(…) but w/o overwrites.
		"""
		for key, default_value in dict_with_defaults.items():
			if not self.__contains__(key):
				self.__setitem__(key, default_value)

	def get_int(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		return int(super(OptionsDict, self).get(*args, **kwargs))

	def get_bool(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		value = super(OptionsDict, self).get(*args, **kwargs)
		return value.lower() in self.true_strings

	def get_float(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		return float(super(OptionsDict, self).get(*args, **kwargs))

class ConfigDict(dict):
	"""
	Ensures that nested dicts in FillFromFileDict are OptionsDict's.
	"""

	def fill_from_file(self, filename):
		"""
		Method loads configuration from file into dictionary.
		"""
		debug("filling configuration from '%s'" % filename)
		fp = open(filename, "r")
		sections = dict()
		options = OptionsDict()
		for line in fp.readlines():
			line = line.strip()

			if line.startswith("#"):
				continue

			if line.startswith('[') and line.endswith(']'):
				options = OptionsDict()
				sections[line[1:-1].strip()] = options
				continue

			if '=' in line:
				key, value = tuple(line.split("=", 1))
				options[key.strip()] = value.strip()
				continue

		fp.close()
		debug("filled configuration is: '%s'" % str(sections))

		self.update(sections)
