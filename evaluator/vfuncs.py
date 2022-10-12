#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/vfuncs.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################

import re

__rxfunc = re.compile(r'^(\w+)\s*\((.*)\)$')


class VFunc():
	def __init__(self, fname, fargs):
		self._fname = fname
		if isinstance(fargs, str):
			self._fargs = [fargs]
		elif isinstance(fargs, list):
			self._fargs = fargs
		else:
			raise TypeError('fargs must be a list of strings')
		self._func = None
		self._pickfunc()
	# end def


	def _pickfunc(self):
		self._func = {
			'equals'      : self._equals,
			'different'   : self._different,
			'between'     : self._between,
			'minlength'   : self._minlength,
			'maxlength'   : self._maxlength,
			'lt'          : self._lt,
			'leq'         : self._leq,
			'gt'          : self._gt,
			'geq'         : self._geq,
			'contains'    : self._contains,
			'anyof'       : self._anyof,
			'matches'     : self._matches
		}.get(self._fname, None)
	# end def


	def _equals(self, value):
		if isinstance(self._fargs[0], (int, float)):
			value = VFunc._tofloat(value)
			if not value: return False
		# elif isinstance(self._fargs[0], int):
		# 	value = VFunc._toint(value)
		# 	if not value: return False
		return value == self._fargs[0]
	# end def

	def _different(self, value):
		if isinstance(self._fargs[0], (int, float)):
			value = VFunc._tofloat(value)
			if not value: return False
		return value == self._fargs[0]
	# end def

	def _minlength(self, value):
		return len(value) >= self._fargs[0]
	# end def

	def _maxlength(self, value):
		return len(value) <= self._fargs[0]
	# end def

	def _between(self, value):
		value = VFunc._tofloat(value)
		if not value: return False
		return value >= self._fargs[0] and value <= self._fargs[1]
	# end def


	def _lt(self, value):
		value = VFunc._tofloat(value)
		if not value: return False
		return value < self._fargs[0]
	# end def


	def _leq(self, value):
		value = VFunc._tofloat(value)
		if not value: return False
		return value <= self._fargs[0]
	# end def


	def _gt(self, value):
		value = VFunc._tofloat(value)
		if not value: return False
		return value > self._fargs[0]
	# end def


	def _geq(self, value):
		value = VFunc._tofloat(value)
		if not value: return False
		return value >= self._fargs[0]
	# end def


	def _contains(self, value):
		return self._fargs[0] in value
	# end def


	def _anyof(self, value):
		return value in self._fargs
	# end def


	def _matches(self, value):
		return re.fullmatch(self._fargs[0], value) is not None
	# end def


	def __str__(self):
		fargs = [str(a) for a in self._fargs] if isinstance(self._fargs, list) else [self._fargs]
		return self._fname + '(' + ', '.join(fargs) + ')'
	# end def


	def __call__(self, value):
		if not callable(self._func):
			return
		return self._func(value)


	@staticmethod
	def _tofloat(value):
		try:
			return float(value)
		except:
			return None
	# end def

	@staticmethod
	def _toint(value):
		try:
			return int(value)
		except:
			return None
	# end def
# end class



def parse(s):
	fname, fargs = __split(s.strip())
	supported = ['equals', 'different', 'between',
	             'minlength', 'maxlength',
	             'lt', 'leq', 'gt', 'geq',
	             'contains', 'anyof', 'matches']
	if not fname or not fname in supported:
		return parse(f'equals({fargs})')

	fargs = __split_fargs(fargs)
	okfargs = True
	if fname in ['equals', 'different']:
		okfargs = __check_fargs(fargs, argstype=None, num=1)
	elif fname == 'between':
		okfargs = __check_fargs(fargs, argstype=float, num=2)
	elif fname in ['minlength', 'maxlength']:
		okfargs = __check_fargs(fargs, argstype=int, num=1)
	elif fname in ['lt', 'leq', 'gt', 'geq']:
		okfargs = __check_fargs(fargs, argstype=float, num=1)
	elif fname in ['anyof']:
		okfargs = __check_fargs(fargs, argstype=str, num=-1)
	elif fname in ['contains', 'matches']:
		okfargs = __check_fargs(fargs, argstype=str, num=1)

	if not okfargs:
		return None
	# print(f'fname: {fname}')
	# print(f'fargs: {fargs}')
	return VFunc(fname, fargs)
# end def



def __split(s):
	m = __rxfunc.match(s)
	if not m:
		return None, s
	fname = m.group(1)
	fargs = m.group(2)
	return fname, fargs
# end def



def __split_fargs(s):
	cc = 0
	bcc = 0
	fargs = []
	while cc < len(s):
		if s[cc].isspace():
			bcc = cc = __skips_paces(s, cc+1)
			continue
		elif s[cc] == '\\':
			cc+=1
		elif s[cc] == ',':
			if cc > bcc:
				fargs.append(s[bcc:cc])
		elif s[cc] == '"' or s[cc] == '\'':
			qstr, cc = __read_quotedstr(s, cc)
			fargs.append(qstr)
			bcc = cc+1
		cc+=1
	#end while
	if cc > bcc:
		fargs.append(s[bcc:min(cc, len(s))])
	return fargs
# end def



def __skips_paces(s, cc):
	while cc < len(s) and s[cc].isspace():
		cc+=1
	return cc
# end def



def __read_quotedstr(s, cc):
	qc = s[cc]
	cc+=1
	bcc = cc

	while cc < len(s) and s[cc] != qc:
		if s[cc] == '\\':
			cc+=1
		cc+=1
	return s[bcc:cc], cc
# end def



def __check_fargs(fargs, argstype=str, num=1):
	if num >= 0 and len(fargs) != num:
		return False
	for i in range(len(fargs)):
		try:
			if argstype:
				fargs[i] = argstype(fargs[i])
			else:
				fargs[i] = __autoconvert(fargs[i])
		except:
			return False
	return True
# end def



def __autoconvert(s):
	if re.fullmatch(r'[\+\-]?\d+\.\d+(e[\+\-]\d+)?', s):
		return float(s)
	elif re.fullmatch(r'[\+\-]?\d+', s):
		return int(s)
	return s
# end def
