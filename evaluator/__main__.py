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
import argparse
from . import specs
from . import evaluator
from . import pdflog


def fetch_args():
	parser = argparse.ArgumentParser(prog='evaluator', description='Evaluates an application.')

	parser.add_argument('specs_file', type=str,
	                    help='the XML evaluation file that specifies how to build and evaluate the program')

	parser.add_argument('--output', metavar='path', type=str, nargs=1,
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


def main():
	args = fetch_args()
	# print(args)
	s = specs.from_xml(args.specs_file)
	# print(s.__dict__)
	e = evaluator.from_specs(s)
	e.evaluate(args.source)
	report = pdflog.build()
	# print(f'args: {args}')
	print('Evaluation complete')
	print('Encrypting...')
	pdflog.encrypt_pdf(report)

	if args.output and len(args.output) > 0:
		print(f'Moving {report} to {args.output[0]}')
		os.rename(report, args.output[0])
		report = args.output[0]

	print(report)

if __name__ == '__main__':
	main()
