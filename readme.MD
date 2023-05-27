# ProgEval

Automated utility to automate testing of student programs.

ProgEval takes a source-code file, builds it if necessary, and tests it using all the parameters defined in an XML configuration file, generating a PDF file with the execution summary.

Applications are executed as a standalone POSIX programs, meaning a set of command-line arguments will be given to the application expecting an output to be yield directly after execution to the standard output streams `stdout` and/or `stderr` with the proper return code.
Furthermore, the maximum execution time for a program is limited to 5 seconds after which the process is terminated and the run considered as unsuccessful.

ProgEval does not support interactive applications and there are no plans to add this feature in the future (or ever).
The output of the applications is not analyzed and no data is written to the standard input stream `stdin`.
This means that functions that interact with `stdin` such as `input()`, `gets()` and `scanf()` will wait indefinitely, thus leading to the termination of the process.
Likewise there are no plans to add file-analysis support to this tool, such as when dumping results of matrix multiplication to a text file.

ProgEval will test an application against all the applicable test defined in the XML configuration file, which are grouped and organized in *testbeds* that are run in order.
Each *testbed* grant a score and the overall mark is the sum of the scores granted by the passed testbeds, either in whole or proportional to the passed tests, as it was configured.



## Installation and test
1. Clone or download the repository
2. Enter the subdirectory
3. Create a virtual environment with `pipenv`

    ```bash
    pipenv install
    ```

4. Ecxecute with `pipenv`. The first parameter must be the testconf XML file and the second parameter is the sourcecode file to test.

    ```bash
    pipenv run evaluator testconf.xml myfile.c
    ```

## `testconf` XML files
These are the configuration files that allow the evaluator to test, evaluate and score a sourcecode file.
The structure of these files is explained below.

The root tag `testconf` requires an attribute `language` whose values can be any of `C`, `C++` or `Python` (case insensitive).

The `build` tag of `testconf` is used to pass parameters to the compiler (using the `flags` tag) such as `-lm` to build programs using `math.h` or `-lpthread` to link against PThreads.
The `score` attribute allows to set a base score when a program builds successfully.
The default building tools are `gcc` for programs written in C, `g++` for programs written in C++, and `python3` for Python scripts.
At this point it is **not** possible to define a custom building tool such as cmake.

The `interpreter` tag of `testconf` is used to specify the interpreter used in scripting languages such as Python.
When omitted the default value is `python3` but other interpreters such as `python2,7` or `python3.5` can be specified.

The `testbeds` tag  of `testconf` is a container for the testbeds used to evaluate the application built.
Testbeds are evaluated in order.
This tag is required.

Each `testbed` tag inside `testbeds` specifies a testbed with several test (`testrun`s).
The `score` attribute is required and specifies the score granted by the testbed. Two additional attributes modify the behavior of the evaluator and hence affect the scoring:

- **`type`**: Specifies the type of evaluation to use. Possible values are `normal` and `proportional`.
    - `normal`: Default. Score is all or nothing. Full mark is granted only if all testruns are passed, scoring zero otherwise.
    - `proportional`: Granted score is proportional to the number of testruns passed.

- **`onerror`**: Tells the evaluator what to do in case of errors, i.e. when the result obtained when executing a tesrtun is rejected.
Possible values are `abort`, `halt`, `skip`, and `continue`.
    - `abort`:    Stops the evaluation of this and all pending testbeds.
    - `halt`:     Default. Stops the evaluation after finishing the current testbed.
    - `skip`:     Stops the evaluation of the current testbed and jumps to the next one.
    - `continue`: Continues evaluating this testbed. Pending testbeds will be evaluated normally.

These values can be better understood with the following table:

| Value      | Run next testrun | Run next testbed |
|:----------:|:----------------:|:----------------:|
| `abort`    |        No        |        No        |
| `halt`     |        Yes       |        No        |
| `skip`     |        No        |        Yes       |
| `continue` |        Yes       |        Yes       |


Each `testrun` tag inside `testbed` specifies a test for the application.
The `args` attribute provides the arguments for the program as they would be typed in the command line (i.e. received through `char** argv` in C/C++ or via `sys.args` in Python).
The `cout` and `cerr` attributes contain the expected values or the evaluating functions with which the standard output streams *cout* and *cerr* will be matched against.
The `retcode` attribute specifies the expected return code for the application or an evaluating function to match against.
The `timeout` attribute specifies the amount of time, in seconds, ProgEval will wait for the program to finish (default is 5).
If the `cout`, `cerr`, or `retcode` attributes are missing, the streams are ignored.

### Evaluating functions
ProgEval has the following functions to evaluate the output streams and return code of the applications:

- **`equals(s)`**:
Default. The returned text string must be identical to `s`.


- **`different(s)`**:
The returned text string must must **NOT** be identical to `s`.

- **`between(x, y)`**:
el valor devuelto (numérico) debe estar en el intervalo cerrado [x, y]

- **`minlength(n)`**:
The returned text string must be at least `n` characters long.

- **`maxlength(n)`**:
The returned text string must be at most `n` characters long.

- **`lt(x)`**:
The returned value (numeric) must be lesser than `x`

- **`leq(x)`**:
The returned value (numeric) must be lesser or equal to `x`

- **`gt(x)`**:
The returned value (numeric) must be greater or equal to `x`

- **`geq(x)`**:
The returned value (numeric) must be greater than `x`

- **`contains(s)`**:
The returned text string must contain the substring `s`

- **`anyof(s1, s2, ..., sn)`**:
The returned text string must be any from the set *{s1, s2, ..., sn}*

- **`matches(rx)`**:
Evaluates the returned text string against the regular expression `rx`


### Example `testconf` XML file
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
	Tests a program that sums n times 1/n
		./a.out r n
	Yields
		for(int i=0; i < n; ++i) r+= 1.0/n;
//-->
<testconf language="C">

	<build score="5">
		<flags>-lm</flags>
	</build>
	<testbeds>
		<testbed score="1" type="normal" onerror="halt">
			<testrun     args="1000 0" cout="between(0.8, 1.2)" />
		</testbed>

		<testbed score="3" type="proportional" onerror="halt">
			<testrun    args="10000 0" cout="between(0.8, 1.2)" />
			<testrun   args="100000 0" cout="between(0.8, 1.2)" />
			<testrun  args="1000000 0" cout="between(0.8, 1.2)" />
			<testrun args="10000000 0" cout="between(0.8, 1.2)" />

			<testrun     args="1000    999" cout="between(   998.7, 1001.2)" />
			<testrun    args="10000  -1000" cout="between( -1001.2, -998.7)" />
			<testrun   args="100000   2000" cout="2000" />
			<testrun  args="1000000  10000" cout="10000" />
			<testrun args="10000000 100000" cout="100000" />
		</testbed>

		<testbed score="1" type="proportional" onerror="continue">
			<testrun     args="" cerr="minlength(15)" />
			<testrun     args="" retcode="different(0)" />
		</testbed>

		<!-- Extra point -->
		<testbed name="Extra" score="1" type="proportional" onerror="continue">
			<testrun     args="100000000" cerr="minlength(15)" />
			<testrun     args="100000000" retcode="different(0)" />
		</testbed>
	</testbeds>
</testconf>
```

## Acknowledgements
Developed with support of PAPIME PE106922

