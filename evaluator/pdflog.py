#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/pdflog.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################

import re
import os
import sys
import hashlib
import subprocess as sp
from .common import execute, delete

DEFAULT_TIMEOUT = 20
pyprint = print


def section(s):
	__pdflog.section(s)
#end def

def subsection(s):
	__pdflog.subsection(s)
#end def

def warning(s):
	# pyprint(f'[WARN]: {s}')
	__pdflog.warn(s)
#end def

def info(s):
	# pyprint(f'[INFO]: {s}')
	__pdflog.info(s)
#end def

def error(s):
	# pyprint(f'[ERROR]: {s}')
	__pdflog.error(s)
#end def

def rawwrite(s):
	__pdflog.rawwrite(s)
#end def

def write(s, color=None):
	__pdflog.write(s, color=None)
#end def

def writeline(s='', color=None):
	__pdflog.writeline(s, color=color)
#end def

def writeverbatim(verbatim):
	__pdflog.writeverbatim(verbatim)
#end def

def print(s, end="\n\n", color=None):
	__pdflog.print(s, end="\n\n", color=color)
#end def

def setfile(file):
	__pdflog.output = file
#end def

def build():
	return __pdflog.build()
#end def

def encrypt_pdf(pdffile):
	sha1 = hashlib.sha1()
	if not isinstance(pdffile, str) or not os.path.exists(pdffile):
		pyprint(f'Failed to encrypt {pdffile}. File does not exist.', file=sys.stderr)
		return

	with open(pdffile, 'rb') as f:
		while True:
			data = f.read(65535)
			if not data:
				break
			sha1.update(data)
	sha1 =  sha1.hexdigest()
	efname = f'{sha1}.pdf'

	args = [
		pdffile, 'output', efname, 'encrypt_128bit',
		'owner_pw', sha1, 'allow', 'printing',
		'allow', 'CopyContents'
	]
	pyprint(f'encrypting {pdffile} into {efname}')
	o, e, p = execute('pdftk', args, addpath=False)
	pyprint(f'cout: {o}')
	pyprint(f'cerr: {e}')
	pyprint('Updating...')
	if os.path.exists(efname):
		delete(pdffile)
		os.rename(efname, pdffile)
	else:
		pyprint(f'{efname} does not exist', file=sys.stderr)
	pyprint('Done')
#end def



def getVerbChar(s):
	if __latexmk_ver >= 4.31:
		verchars = '§¬¥^|`"<>!@#$%&+-/.,:;()~'
	else:
		verchars = '^|`"<>!@#$%&+-/.,:;()~'
	for c in verchars:
		if c in s:
			continue
		return c
#end def



def _get_pdftk_version():
	o, e, p = execute('pdftk', ['--version'], timeout=1, addpath=False)
	if p is None or p.returncode != 0:
		raise(OSError('pdftk is not installed'))
		# pdftk port to java 3.0.9
	m = re.search(r'pdftk([a-z ]+)\s+(\d+\.\d+)(\.\d+)?', o, re.I)
	if m:
		pyprint(f'pdftk version {m.group(2)}')
		return float(m.group(2))
	return None
#end def



def _get_latexmk_version():
	o, e, p = execute('latexmk', ['--version'], timeout=1, addpath=False)
	if p is None or p.returncode != 0:
		raise(OSError('latexmk is not installed'))
	m = re.search(r'Version\s+(\d+\.\d+)', o, re.I)
	if m:
		return float(m.group(1))
	return None
#end def



def _pdfbuild(texfile):
	# args = ['-halt-on-error', '-output-directory', 'tex', texfile]
	# return execute('pdflatex', args, timeout=20)
	tfpath = os.path.abspath(texfile)
	aopath = os.path.dirname(tfpath)
	args = [
		'-gg', '-pdf', '-silent',
		f'-auxdir={aopath}',
		f'-outdir={aopath}',
		'-halt-on-error',
	]
	if __latexmk_ver >= 4.31:
		args.append('-xelatex')
	args.append(texfile)
	# pyprint('\nExec: latexmk ' + '\n  '.join(args) + '\n')
	return execute('latexmk', args, timeout=DEFAULT_TIMEOUT, addpath=False)
#end def



def _pdfclean(texfile):
	tfpath = os.path.abspath(texfile)
	aopath = os.path.dirname(tfpath)
	args = [
		'-c',
		f'-auxdir={aopath}',
		f'-outdir={aopath}',
		texfile
	]
	if __latexmk_ver >= 4.31:
		args.append('-xelatex')
	return execute('latexmk', args, addpath=False)
#end def



class PdfLog():
	def __init__(self):
		self._content = []
		self._loadTemplate()
	# end def

	def _loadTemplate(self):
		self.__header = ''
		self.__footer = ''
		rxContent = re.compile(r'%Content%[\r\n]*')
		here = os.path.abspath(os.path.dirname(__file__))
		template = os.path.join(here, 'template.tex')
		with open(template, 'r', encoding='utf-8') as f:
			line = f.readline()
			flag = False
			while line:
				if rxContent.fullmatch(line):
					flag = True
					line = f.readline()
					continue

				if flag:
					self.__footer+= line
				else:
					self.__header+= line
				line = f.readline()
			# end while
		# end with
	# end def

	def section(self, s):
		self._content.append(f'\\section{{{s}}}\n')
	# end def

	def subsection(self, s):
		self._content.append(f'\\subsection{{{s}}}\n')
	# end def

	def warn(self, s, color='YellowOrange'):
		pyprint(f'[WARN]: {s}')
		self.writeline(f'[WARN]: {s}')
	# end def

	def info(self, s):
		pyprint(f'[INFO]: {s}')
		# self._content.append(f'[INFO]: {s}')
		self.writeline(s)
	# end def

	def error(self, s, color='Maroon'):
		pyprint(f'[ERROR]: {s}')
		self.writeline(f'[ERROR]: {s}')
	# end def

	def rawwrite(self, s):
		self._content.append(f'{s}')
	# end def

	def write(self, s, color=None):
		self.print(s, end='', color=color)
	# end def

	def writeline(self, s='', color=None):
		self.print(s, color=color)
	# end def

	def writeverbatim(self, verbatim):
		if not isinstance(verbatim, str) or len(verbatim) < 1:
			return
		if '\n' in verbatim:
			self.writeVerbatimBlock(verbatim)
		else:
			self.writeVerbatimInline(verbatim)
	#end def

	def writeVerbatimBlock(self, verbatim):
		self.rawwrite('\n\\begin{Verbatim}\n')
		self.rawwrite(verbatim)
		self.rawwrite('\n\\end{Verbatim}\n')
	#end def

	def writeVerbatimInline(self, verbatim):
		vc = getVerbChar(verbatim)
		self.rawwrite(f'\\Verb{ vc }{ verbatim }{ vc }')
	#end def

	def print(self, s, end='\n\n', color=None):
		if not isinstance(s, str):
			s = ''
		if not isinstance(end, str):
			end = ''
		color = PdfLog.__texcolor(color)

		s = PdfLog.__format(s)
		if color:
			self._content.append(f'{{\\color{{{color}}}{s}}}{end}')
		else:
			self._content.append(f'{s}{end}')

	# end def

	def build(self):
		text = self.__header + '\n'
		text+= ''.join(self._content)
		text+= self.__footer

		fprefix = hashlib.sha1(text.encode('utf-8')).hexdigest()
		fprefix = 'foo'
		texfile = os.path.join('tex', f'{fprefix}.tex')
		logfile = os.path.join('tex', f'{fprefix}.log')
		auxfile = os.path.join('tex', f'{fprefix}.aux')
		pdffile = os.path.join('tex', f'{fprefix}.pdf')

		if not os.path.exists('tex'):
			os.mkdir('tex')
		with open(texfile, 'w', encoding='utf-8') as f:
			f.write(text)

		if not _pdfbuild(os.path.abspath(texfile)):
			pyprint(f'Failed to build {pdffile}: no input file {texfile}', file=sys.stderr)

		_pdfclean(os.path.abspath(texfile))

		if not os.path.exists(pdffile):
			pyprint(f'Failed to build {pdffile}', file=sys.stderr)
			return None
		return pdffile
	# end def


	@staticmethod
	def __texcolor(color):
		if color is None:
			return None
		if not isinstance(color, str):
			return 'black'
		texcolors = [
			'black', 'blue', 'brown', 'cyan', 'darkgray', 'gray',
			'green', 'lightgray', 'lime', 'magenta', 'olive',
			'orange', 'pink', 'purple', 'red', 'teal', 'violet'
			'white', 'yellow'
		]

		divps = [
			'Apricot', 'Aquamarine', 'Bittersweet', 'Black',
			'Blue', 'BlueGreen', 'BlueViolet', 'BrickRed',
			'Brown', 'BurntOrange', 'CadetBlue', 'CarnationPink',
			'Cerulean', 'CornflowerBlue', 'Cyan', 'Dandelion',
			'DarkOrchid', 'Emerald', 'ForestGreen', 'Fuchsia',
			'Goldenrod', 'Gray', 'Green', 'GreenYellow',
			'JungleGreen', 'Lavender', 'LimeGreen', 'Magenta',
			'Mahogany', 'Maroon', 'Melon', 'MidnightBlue',
			'Mulberry', 'NavyBlue', 'OliveGreen', 'Orange',
			'OrangeRed', 'Orchid', 'Peach', 'Periwinkle',
			'PineGreen', 'Plum', 'ProcessBlue', 'Purple',
			'RawSienna', 'Red', 'RedOrange', 'RedViolet',
			'Rhodamine', 'RoyalBlue', 'RoyalPurple', 'RubineRed',
			'Salmon', 'SeaGreen', 'Sepia', 'SkyBlue',
			'SpringGreen', 'Tan', 'TealBlue', 'Thistle',
			'Turquoise', 'Violet', 'VioletRed', 'White',
			'WildStrawberry', 'Yellow', 'YellowGreen', 'YellowOrange',
		]

		if color in texcolors or color in divps:
			return color
		return 'black'
	# end def


	@staticmethod
	def __format(s):
		s = s.replace('\r\n', '\n')
		s = s.replace('\n', '\n\n')
		s = s.replace('\\', '\\textbackslash')
		s = s.replace('_', '\\_')
		s = s.replace('$', '\\$')
		s = s.replace('%', '\\%')
		# s = s.replace('', '')
		# s = s.replace('', '')
		s = s.replace('\t', '\\hspace{2em}')
		return s
	# end def
# end class

__pdflog = PdfLog()
__pdftk_ver = _get_pdftk_version()
__latexmk_ver = _get_latexmk_version()
