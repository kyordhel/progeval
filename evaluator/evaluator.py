#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/evaluator.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################
import os
import re
import hashlib
import datetime
from . import common
from . import pdflog

def from_specs(specs):
	return Evaluator(specs)


class Evaluator():
	def __init__(self, specs):
		self._specs = specs
		self._reset()
	#end def

	@property
	def compiled(self):
		return self._specs and self._specs.compiled
	# end def

	def evaluate(self, source):
		if not self._specs:
			return
		self._reset()
		self._srcfile = source

		self._writeSummary()
		pdflog.section('Build')
		if not self._build():
			self._clean()
		else:
			pdflog.section('Tests')
			self._test()

		pdflog.section('Score')
		pdflog.rawwrite(f'Final score: \\labeltext{{{self._score}}}{{txt:score}}')
		pdflog.writeline()
		self._clean()
	#end def

	def _build(self):
		if not self._specs.buildTool:
			return

		build = {
			'C'  : common.cbuild,
			'C+' : common.cppbuild,
			'Py' : common.pybuild,
		}.get(self._specs.language[0:2], None)
		if not build:
			pdflog.error(f'Unsupported language. Program failed to build.')
			return

		srcfile = os.path.basename(self._srcfile)
		pdflog.info('Building {}'.format(srcfile))

		self._exefile = build(self._specs.buildTool, self._srcfile, flags=self._specs.buildFlags)
		if not self._exefile:
			pdflog.warning(f'Source file {srcfile} failed to build')
			return False

		self._score+= self._specs.buildScore

		if not isinstance(self._exefile, str):
			exefile = os.path.basename(self._srcfile)
			self._exefile = self._specs.interpreter
		else:
			exefile = os.path.basename(self._exefile)
		pdflog.info('Built {}'.format(exefile))
		if self._specs.buildScore > 0:
			pdflog.writeline('Score {:+0.1f}'.format(self._specs.buildScore))
		return True
	#end def

	def _test(self):
		for tb in self._specs.testbeds:
			pdflog.subsection(f'Running {tb.name}')
			passcount = self._run_testbed(tb)
			pdflog.rawwrite('\\medskip{\\bfseries Summary}\\\\\n')
			pdflog.writeline(f'Passed {passcount} of {len(tb.testruns)} tests')

			score = tb.score if passcount == len(tb.testruns) else 0
			if tb.type == 'proportional':
				score = tb.score * passcount / len(tb.testruns)
			self._score+= score
			pdflog.writeline('Score {:+0.1f} of {}'.format(score, tb.score))

			if passcount < len(tb.testruns):
				if tb.onError == 'halt':
					pdflog.rawwrite('\\medskip\n')
					pdflog.writeline('Program did not pass all required tests.')
					pdflog.writeline('Evaluation halted.') # , color='Maroon'
				if tb.onError in ['abort', 'halt']:
					break
	#end def


	def _run_testbed(self, tb):
		i = 0
		# srcfile = os.path.basename(self._srcfile)
		# exefile = os.path.basename(self._exefile)
		passcount = 0
		for t in tb:
			if (passcount < i) and (tb.onError in ['abort', 'skip']):
				pdflog.rawwrite('\\medskip\n')
				pdflog.writeline('Program did not pass the previous required test.')
				pdflog.writeline('Test set aborted.') # , color='Maroon'
				break

			i+=1
			pdflog.write(f'Test {i} of {len(tb)}: ')
			self._writeCmdStr(t)

			o, e, p = self._execute(t)

			if p is None:
				return passcount

			if t.cout and not t.checkCout(o):
				self._writeReject('Output', o.strip())
				continue

			if t.cerr and not t.checkCerr(e):
				self._writeReject('Output (stderr)', e.strip())
				continue

			if t.retval and not t.checkRetval(p.returncode):
				self._writeReject('Return code', p.returncode)
				continue

			passcount+= 1
			pdflog.writeline('\tPass', color='OliveGreen')

		return passcount
	#end def

	def _execstr(self, testset):
		exefile = os.path.basename(self._exefile)
		if self.compiled:
			s = './{} '.format(exefile)
		else:
			s = '{} {} '.format(exefile, os.path.basename(self._srcfile))
		s+= ' '.join([
			str(a) if not ' ' in str(a) else f'"{str(a)}"'
			for a in testset.args
		])
		return s.strip()
		# 80
		# 'python3 ground.py "A mamá, Roma le aviva el amor a papá, y a papá, Roma le aviva el"' amor a mamá."
	#end def

	def _execute(self, testset):
		if self.compiled:
			o, e, p = common.execute(self._exefile, testset.args,
				timeout=testset.timeout, addpath=True)
		else:
			o, e, p = common.execute(self._exefile, [ self._srcfile ] + testset.args,
				timeout=testset.timeout, addpath=False)
		if isinstance(o, str):
			o = o.strip()
		if isinstance(e, str):
			e = e.strip()
		return o, e, p
	#end def

	def _reset(self):
		self._srcfile = None
		self._exefile = None
		self._score = 0
	#end def

	def _clean(self):
		common.delete(self._exefile)
	#end def

	def _writeCmdStr(self, testset, width=72):
		estr = self._execstr(testset)
		parts = [ estr[i:i+width] for i in range(0, len(estr), width) ]
		for i in range(len(parts)):
			vc = pdflog.getVerbChar(parts[i])
			if i > 0:
				pdflog.rawwrite('\\hspace{10em}')
			pdflog.rawwrite(f'\\Verb{ vc }{ parts[i] }{ vc }')
			pdflog.writeline()
	#end def

	def _writeReject(self, stream, verbatim):
		verbatim = verbatim.strip()
		pdflog.write(f'\t{stream} ')
		if isinstance(verbatim, str) and len(verbatim) > 0:
			pdflog.writeverbatim(verbatim)
			pdflog.writeline()
		else:
			pdflog.rawwrite(': (none). ')

		pdflog.writeline('REJECTED!', color='YellowOrange')
	#end def

	def _writeSummary(self):
		with open(self._srcfile, 'r') as f:
			src = f.read()
		now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		sha1 = hashlib.sha1(src.encode('utf-8')).hexdigest()
		author = Evaluator.findAuthor(src)
		srcfile = os.path.basename(self._srcfile)
		pdflog.rawwrite('\\Large\n')
		pdflog.writeline(f'Automated evaluation report')
		pdflog.rawwrite('\\noindent\n')
		pdflog.rawwrite('\\begin{tabular}{@{} l l}\n')
		pdflog.rawwrite(f'Generated on: & {now}\\\\\n')
		pdflog.rawwrite(f'Source file:  & \\Verb^{srcfile}^\\\\\n')
		pdflog.rawwrite(f'Source sha1:  & \\Verb^{sha1}^\\\\\n')
		pdflog.rawwrite(f'Source author:& \\Verb^{author}^\\\\\n')
		pdflog.rawwrite(f'Score:        & \\ref*{{txt:score}}\\\\\n')
		pdflog.rawwrite('\\end{tabular}\n')
		pdflog.rawwrite('\\normalsize\n')
	#end def


	__rxAuthor = re.compile(r'@?auth?or\s*:\s*([^\n]+)\n', re.I)
	@staticmethod
	def findAuthor(src):
		m = Evaluator.__rxAuthor.search(src)
		if not m:
			return '(Not specified)'
		return m.group(1).strip()

	#end def

#end class
