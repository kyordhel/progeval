#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/specs.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################

# from .evaluator import Evaluator
import re
import os
import shlex
from xml.dom import minidom
from .common import error, warn
from .vfuncs import parse as vfparse


def from_xml(file):
	if not os.path.isfile(file):
		error(f'File {file} not found.')
		return None
	doc = minidom.parse(file)
	conf = doc.getElementsByTagName('testconf')
	if not conf or len(conf) < 1:
		error(f'Malformed document {file}. Expected <testconf>.')
		return None
	if not 'language' in conf[0].attributes:
		error(f'Malformed document {file}. Expected a language attribute.')
		return None
	lang = conf[0].attributes['language'].value.lower().strip()

	if lang == 'c':
		return CSpecs(conf[0])
	elif lang == 'c++':
		return CPPSpecs(conf[0])
	elif lang == 'python':
		return PySpecs(conf[0])
	else:
		error(f'Unsupported language {lang}.')
		return None
# end def



class Specs():
	def __init__(self, domconf):
		self._buildTool = None
		self._buildFlags = None
		self._buildScore = 0
		self._lang = None
		self._testbeds = []
	# end def


	@property
	def language(self):
		return self._lang
	# end def


	@property
	def buildTool(self):
		return self._buildTool
	# end def


	@property
	def buildFlags(self):
		return self._buildFlags
	# end def


	@property
	def buildScore(self):
		return self._buildScore
	# end def


	@property
	def testbeds(self):
		return self._testbeds
	# end def


	def _parseBuild(self, conf):
		build = conf.getElementsByTagName('build')
		if not build or len(build) < 1:
			return
		if 'score' in build[0].attributes:
			self._buildScore = float(build[0].attributes['score'].value)

		flags = build[0].getElementsByTagName('flags')
		if not flags or len(flags) < 1:
			return
		self._buildFlags = flags[0].firstChild.data
	# end def


	def _parseTestbeds(self, conf):
		tbl = conf.getElementsByTagName('testbeds')
		if not tbl or len(tbl) != 1:
			return

		tbl = tbl[0].getElementsByTagName('testbed')
		if not tbl or len(tbl) < 1:
			return

		i = 0
		for tbi in tbl:
			i+= 1
			tb = self.__parseTestbed(tbi)
			if not tb.name:
				# tb.name = f'Testing set {i}' if i < 2 else 'Main testing set'
				tb.name = f'Testset {i}'
			if len(tb.testruns) > 1:
				self._testbeds.append(tb)
	# end def


	@staticmethod
	def __parseTestbed(tbe):
		tb = Testbed()
		tb.name = None
		if 'score' in tbe.attributes:
			tb.score = float(tbe.attributes['score'].value)

		if 'name' in tbe.attributes:
			tb.name = tbe.attributes['name'].value

		if 'type' in tbe.attributes:
			tb.type = tbe.attributes['type'].value

		if 'onerror' in tbe.attributes:
			tb.onError = tbe.attributes['onerror'].value

		tb.testruns.extend(Specs.__parseTestruns(tbe))
		return tb
	# end def


	@staticmethod
	def __parseTestruns(tbe):
		trl = tbe.getElementsByTagName('testrun')
		if not trl or len(trl) < 1:
			return []

		testruns = []
		for tre in trl:
			tr = Specs.__parseTestrun(tre)
			if tr:
				testruns.append(tr)
		return testruns
	# end def


	@staticmethod
	def __parseTestrun(tre):
		return TestRun.parse(tre)
	# end def
# end class



class CSpecs(Specs):
	def __init__(self, domconf):
		Specs.__init__(self, domconf)
		self._lang = 'C'
		self._buildTool = 'gcc'
		self._parseBuild(domconf)
		self._parseTestbeds(domconf)
	# end def
# end class



class CPPSpecs(Specs):
	def __init__(self, domconf):
		Specs.__init__(self, domconf)
		self._lang = 'C++'
		self._buildTool = 'g++'
		self._parseBuild(domconf)
		self._parseTestbeds(domconf)
	# end def
# end class



class PySpecs(Specs):
	def __init__(self, domconf):
		Specs.__init__(self, domconf)
		self._lang = 'Python'
	# end def
# end class



class Testbed(Specs):
	def __init__(self):
		self._score = 0
		self._name = 'Testing set'
		self._type = None
		self._onError = 'halt'
		self._testruns = []
	# end def

	@property
	def name(self):
		return self._name
	@name.setter
	def name(self, value):
		self._name = value
	# end def

	@property
	def onError(self):
		return self._onError
	@onError.setter
	def onError(self, value):
		self._onError = value
	# end def

	@property
	def score(self):
		return self._score
	@score.setter
	def score(self, value):
		self._score = value
	# end def

	@property
	def testruns(self):
		return self._testruns

	@property
	def type(self):
		return self._type
	@type.setter
	def type(self, value):
		self._type = value
	# end def

	def __len__(self):
		return len(self.testruns)
	# end def

	def __iter__(self):
		return self.testruns.__iter__()
	# end def

	def __str__(self):
		return self._name
	# end def

	def __repr__(self):
		return '<Testbed:' +               \
			f'name=\'{self.name}\', ' +    \
			f'score={self.score}, ' +      \
			f'type={self.type}, ' +        \
			f'onerror={self.type}, ' +     \
			f'testruns={len(self.testruns)}>'
	# end def
# end class



class TestRun():
	def __init__(self):
		self._args = None
		self._cout = None
		self._cerr = None
		self._coutCheckFunc = None
		self._cerrCheckFunc = None
		self._retvalCheckFunc = None
		self._retval = 0
		self._timeout = 5
	# end def

	@property
	def args(self):
		return self._args
	@args.setter
	def args(self, value):
		if isinstance(value, str):
			value = shlex.split(value)
		self._args = value
	# end def

	@property
	def cout(self):
		return self._cout
	@cout.setter
	def cout(self, value):
		if isinstance(value, str):
			self._cout = value
			self._coutCheckFunc = vfparse(value)
	# end def

	@property
	def cerr(self):
		return self._cerr
	@cerr.setter
	def cerr(self, value):
		if isinstance(value, str):
			self._cerr = value
			self._cerrCheckFunc = vfparse(value)
	# end def

	@property
	def retval(self):
		return self._retval
	@retval.setter
	def retval(self, value):
		if isinstance(value, str):
			self._retval = value
			self._retvalCheckFunc = vfparse(value)
	# end def

	@property
	def timeout(self):
		return self._timeout
	@timeout.setter
	def timeout(self, value):
		self._timeout = value
	# end def

	def checkCout(self, value):
		if self._coutCheckFunc:
			return self._coutCheckFunc(value)
		return True
	# end def

	def checkCerr(self, value):
		if self._cerrCheckFunc:
			return self._cerrCheckFunc(value)
		return True
	# end def

	def checkRetval(self, value):
		if self._retvalCheckFunc:
			return self._retvalCheckFunc(value)
		return True
	# end def


	@staticmethod
	def parse(tre):
		tr = TestRun()
		if 'args' in tre.attributes:
			tr.args = tre.attributes['args'].value

		if 'cout' in tre.attributes:
			tr.cout = tre.attributes['cout'].value

		if 'cerr' in tre.attributes:
			tr.cerr = tre.attributes['cerr'].value

		if 'retval' in tre.attributes:
			tr.retval = int(tre.attributes['retval'].value)

		if 'timeout' in tre.attributes:
			tr.retval = float(tre.attributes['timeout'].value)

		return tr
	# end def
# end class

