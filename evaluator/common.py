# -*- coding: utf-8 -*-
#
# ## ###############################################################
# evaluator/common.py
#
# Author:  Mauricio Matamoros
# License: MIT
#
# ## ###############################################################

import os
import re
import sys
import subprocess as sp

def error(s):
	eprint(s)
	sys.exit(1)
# end def

def warn(s):
	eprint(s)
# end def

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)
# end def

def delete(file):
	if not isinstance(file, str):
		return
	if os.path.exists(file):
		os.remove(file)
# end def

def pyver():
	return int(sys.version_info[0]) + 0.1 * int(sys.version_info[1])
# end def

def cbuild(buildtool, srcfile, flags=[], outfile=None):
	if not outfile:
		outfile = srcfile[:-2]
	if isinstance(flags, str):
		flags = re.split(r'\s+', flags)
	args = [buildtool]
	args.extend([srcfile, '-x', 'c', '-o', outfile])
	args.extend(flags)
	print(args)
	if pyver() > 3.6:
		cp = sp.run(args, capture_output=True)
	else:
		cp = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
	if cp.returncode != 0:
		delete(outfile)
		return None
	return outfile
# end def

def cppbuild(buildtool, srcfile, flags=[], outfile=None):
	if not outfile:
		outfile = srcfile[:-2]
	if isinstance(flags, str):
		flags = re.split(r'\s+', flags)
	args = [buildtool]
	args.extend([srcfile, '-x', 'c++', '-o', outfile])
	args.extend(flags)
	print(args)
	if pyver() > 3.6:
		cp = sp.run(args, capture_output=True)
	else:
		cp = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
	if cp.returncode != 0:
		delete(outfile)
		return None
	return outfile
# end def

def pybuild(buildtool, srcfile, flags=[], outfile=None):
	return None
# end def


def execute(exefile, args=[], timeout=15, addpath=True):
	eargs = [os.path.abspath(exefile)] if addpath else [exefile]
	eargs.extend([str(a) for a in args])
	proc = sp.Popen(eargs, stdout=sp.PIPE, stderr=sp.PIPE)
	try:
		out, err = proc.communicate(timeout=timeout)
		out = out.decode("utf-8")
		err = err.decode("utf-8")
	except sp.TimeoutExpired:
		log.warning("Timeout! Process didn't finish within {:.2f} seconds".format(float(timeout)))
		proc.kill()
		out, err = proc.communicate(timeout=timeout)
		return None, None, None
	except:
		out = None
		err = None
	return out, err, proc
	# if retcode is not None and proc.returncode != retcode:
	# 	return False
# end def
