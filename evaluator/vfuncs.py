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
			'around'      : self._around,
			'between'     : self._between,
			'minlength'   : self._minlength,
			'maxlength'   : self._maxlength,
			'lt'          : self._lt,
			'leq'         : self._leq,
			'gt'          : self._gt,
			'geq'         : self._geq,
			'contains'    : self._contains,
			'anyof'       : self._anyof,
			'in'          : self._anyof,
			'noneof'      : self._noneof,
			'notin'       : self._noneof,
			'matches'     : self._matches
		}.get(self._fname, None)
	# end def


	def _equals(self, value):
		if isinstance(self._fargs[0], (int, float)):
			value = VFunc._tofloat(value)
			if value is None: return False
		# elif isinstance(self._fargs[0], int):
		# 	value = VFunc._toint(value)
		# 	if not value: return False
		# print(f'equals: "{value}" == "{self._fargs[0]}"')
		return value == self._fargs[0]
	# end def

	def _different(self, value):
		if isinstance(self._fargs[0], (int, float)):
			value = VFunc._tofloat(value)
			if value is None: return False
		return value == self._fargs[0]
	# end def

	def _minlength(self, value):
		return len(value) >= self._fargs[0]
	# end def

	def _maxlength(self, value):
		return len(value) <= self._fargs[0]
	# end def

	def _around(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return abs(value - self._fargs[0]) < self._fargs[0] * self._fargs[1]
	# end def

	def _between(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return value >= self._fargs[0] and value <= self._fargs[1]
	# end def


	def _lt(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return value < self._fargs[0]
	# end def


	def _leq(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return value <= self._fargs[0]
	# end def


	def _gt(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return value > self._fargs[0]
	# end def


	def _geq(self, value):
		value = VFunc._tofloat(value)
		if value is None: return False
		return value >= self._fargs[0]
	# end def


	def _contains(self, value):
		return self._fargs[0] in value
	# end def


	def _anyof(self, value):
		return value in self._fargs
	# end def


	def _noneof(self, value):
		return value not in self._fargs
	# end def


	def _matches(self, value):
		return re.search(self._fargs[0], value) is not None
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
	# print(f'parsing: {s}')
	fname, fargs = __split(s.strip())
	# print(f'\tfname: {fname}')
	# print(f'\tfargs: {fargs}')

	supported = ['equals', 'different',
	             'between', 'around',
	             'minlength', 'maxlength',
	             'lt', 'leq', 'gt', 'geq',
	             'contains', 'anyof', 'in',
	             'notin', 'noneof', 'matches']

	if not fname or not fname in supported:
		fname = 'equals'
		fargs = [fargs]
	else:
		fargs = __split_fargs(fargs)
		# print(f'\tfargs (split): {fargs}')

	okfargs = False
	if fname in ['equals', 'different']:
		okfargs = __check_fargs(fargs, argstype=None, num=1)
	elif fname in ['between', 'around']:
		okfargs = __check_fargs(fargs, argstype=float, num=2)
	elif fname in ['minlength', 'maxlength']:
		okfargs = __check_fargs(fargs, argstype=int, num=1)
	elif fname in ['lt', 'leq', 'gt', 'geq']:
		okfargs = __check_fargs(fargs, argstype=float, num=1)
	elif fname in ['anyof', 'noneof', 'in', 'notin']:
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
	print(f'fargs: "{s}"')
	cc = 0
	bcc = 0
	fargs = []
	while cc < len(s):
		if s[cc] == '\\':
			cc+=1
		elif s[cc] == '"' or s[cc] == '\'':
			qstr, cc = __read_quotedstr(s, cc)
			fargs.append(qstr)
			bcc = cc+1
		elif s[cc] == ',' or s[cc].isspace():
			if cc > bcc:
				fargs.append(s[bcc:cc])
				bcc = cc+1
			bcc = cc = __skips_paces(s, cc+1)
			continue
		# elif s[cc].isspace():
			# print(f'\tbcc: {bcc} | cc: {cc} | s[cc]: {s[cc] if cc < len(s) else None} | s[bcc:cc]: {s[bcc:cc]} | args: {fargs}')
			# bcc = cc = __skips_paces(s, cc+1)
			# continue
		print(f'\tbcc: {bcc} | cc: {cc} | s[cc]: {s[cc]} | s[bcc:cc]: {s[bcc:cc]} | args: {fargs}')
		cc+=1
	#end while
	if cc > bcc:
		fargs.append( s[bcc:min(cc, len(s))].strip() )
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



def __unescape(s):
	replacements = {
		'\\r' : '\r',
		'\\n' : '\n',
		'\\t' : '\t',
	}
	for r in replacements:
		s = s.replace(r, replacements[r])
	return s
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
			if isinstance(fargs[i], str):
				fargs[i] = __unescape(fargs[i])
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



if __name__ == '__main__':
	print('Vfunc:', parse('between(3, 5)')  )
	print('Vfunc:', parse('between(3,5)')   )
	print('Vfunc:', parse('between( 3, 5 )')   )
	print('Vfunc:', parse('between( 3,5 )')   )
	print('Vfunc:', parse('notin( "uno", "dos", "tres" )')   )
