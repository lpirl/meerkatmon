import stat
from urllib.parse import ParseResult
from os import access, environ, pathsep, X_OK, sep, chmod, makedirs
from os.path import isfile, join as path_join, dirname, isdir

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