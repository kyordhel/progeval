#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/__main__.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################

import os
import sys
import argparse
from .specs import     from_xml as specs_from_xml
from .evaluator import from_specs as evaluator_from_specs
from .pdflog import encrypt_pdf, build as pdf_build


def fetch_args():
	parser = argparse.ArgumentParser(prog='evaluator', description='Evaluates an application written in C/C++ or python.')

	parser.add_argument('-t', '--test-xml', metavar='path', type=str, nargs=1,
	                    help='the path to an XML specification file to load and test')

	test_xml(parser)

	parser.add_argument('specs_file', type=str,
	                    help='the XML evaluation file that specifies how to build and evaluate the program')

	parser.add_argument('-o', '--output', metavar='path', type=str, nargs=1,
	                    help='the path of the output file with evaluation results')

	parser.add_argument('source', type=str,
	                    help='the source code of the program to be evaluated')

	# parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2],
	#                     help='sets the increase output verbosity')

	# parser.add_argument('dir', metavar='d', type=str,
	#                     help='A path containing the set of programs to verify')

	# parser.add_argument('--sum', dest='accumulate', action='store_const',
	#                     const=sum, default=max,
	#                     help='sum the integers (default: find the max)')
	return parser.parse_args()
#end def


def test_xml(parser):
	options, remainder = parser.parse_known_args()
	if options.test_xml and len(options.test_xml) > 0:
		try:
			s = specs_from_xml(options.test_xml[0])
			print(f'Successfully loaded {len(s.testbeds)} testbeds from {options.test_xml[0]}')
			for t in s.testbeds:
				print(f'\t{ t }: {len(t.testruns)} testruns, {t.score} points')
			sys.exit(0)
		except Exception as err:
			print(f'Unexpected {err=}, {type(err)=}', file=sys.stderr)
			sys.exit(-1)
		sys.exit(0)
#end def


def main():
	args = fetch_args()
	print(args)
	s = specs_from_xml(args.specs_file)
	# print(s.__dict__)
	e = evaluator_from_specs(s)
	e.evaluate(args.source)
	report = pdf_build()
	# print(f'args: {args}')
	if not report:
		print('Failed to generate report file.', file=sys.stderr)
		print('Aborted.', file=sys.stderr)
		sys.exit(-1)

	print('Evaluation complete')
	print('Encrypting...')
	encrypt_pdf(report)

	if args.output and len(args.output) > 0:
		print(f'Moving {report} to {args.output[0]}')
		os.rename(report, args.output[0])
		report = args.output[0]

	print(report)

if __name__ == '__main__':
	main()
