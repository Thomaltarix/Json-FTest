#!/usr/bin/python3

from subprocess import Popen, PIPE
from enum import Enum
import os
from sys import argv
from junit_xml import TestSuite, TestCase

# Define the tests

class State(Enum):
    """
    Enum to represent the state of a test
    """

    OK = 0
    KO = 1
    CRASH = 2

class Error(Enum):
    """
    Enum to represent the state of the program
    """
    HELP = 0
    VERBOSE = 1
    NONE = 2
    DELETE = 3
    UNKNOWN = 84

def printResult(test, result, return_code, print_details):
    """
    Analyzes the result of a test and prints it (only if --verbose or -v is on)
    The function returns the state of the test (OK, KO, CRASH)
    If the test failed, the function will anyways print the result
    All the error codes are not implemented yet, you can add them if you want
    """

    expectedStdoutOutput = test["expectedStdoutOutput"]
    exceptedStderrOutput = test["expectedStderrOutput"]
    expectedReturnCode = test["expectedReturnCode"]

    if return_code == 139:
        print(
            f"Test \"{test['testName']}\" failed: the program crashed with signal {return_code}")
        return State.CRASH
    if result != expectedStdoutOutput:
        print(
            f"Test \"{test['testName']}\" failed: expected output is \n{expectedStdoutOutput}\nactual output is \n{result}\n")
        return State.KO
    else:
        if return_code != expectedReturnCode:
            print(
                f"Test \"{test['testName']}\" failed: expected return code is {expectedReturnCode}, actual return code is {return_code}")
            return State.KO
        else:
            if print_details == Error.VERBOSE:
                print(f"Test '{test['testName']}' passed")
            return State.OK


def runTest(test, print_details):
    """
    Runs a given command with given arguments and returns the result
    The function will also print the result if --verbose or -v is on

    ! WARNING !
    ! You must implement a command that stops the command line input
    ! if you don't do this, the process will be stuck in the while loop
    ! since you can't CTRL+D or CTRL+C the process.
    ! WARNING !
    """

    result = ""
    command = test["binaryPath"]
    for arg in test["arguments"]:
        command += " " + arg
    if test["fileInput"] != "":
        process = Popen(command,
                        cwd=os.getcwd(),
                        stdout=PIPE,
                        stderr=PIPE,
                        stdin=PIPE,
                        universal_newlines=True)
    while process.poll() is None:
        for command in test["commandLineInputs"]:
            process.stdin.write(command + "\n")
        process.stdin.flush()
        child_output = process.stdout.readline()
        result += child_output

    process.stdin.close()
    process.stdout.close()
    print(child_output)
    return printResult(test, result, process.returncode, print_details)

def generateFile(result):
    """
    Generates a .xml file with the results of the tests.
    The file will be named f_test.xml
    The file will be generated in the same directory as the script
    The file will be generated in JUnit format, so it can be read by Jenkins
    The script do not handle the elapsed time of the tests
    """

    test_cases = []
    for i, test in enumerate(tests):
        test_cases.append(TestCase(test["testName"], classname="", stdout=result[i].name, stderr="", elapsed_sec=0.0, status=result[i].name))
    test_suite = [TestSuite("nanotekspice", test_cases)]
    with open("f_test.xml", "w") as f:
        TestSuite.to_file(f, test_suite)

def handleArgsErrors():
    """
    Handles the errors of the arguments
    The function will return 0 if the user asked for help
    The function will return 1 if the user used the --verbose, -v or no flag
    The function will return 3 if the user used the --delete or -d flag
    The function will return 84 if the user used an unknown flag
    """
    if len(argv) > 1:
        for i in range (1, len(argv)):
            if (argv[i] == "--delete" or argv[i] == "-d"):
                return Error.DELETE
            if (argv[i] == "--help" or argv[i] == "-h"):
                print("Usage: ./f_test.py [--verbose|-v]")
                return Error.HELP
            elif (argv[i] == "--verbose" or argv[i] == "-v"):
                return Error.VERBOSE
            else:
                print("Usage: ./f_test.py [--verbose|-v]")
                return Error.UNKNOWN
    return Error.NONE

def main():
    """
    Main function of the script
    The function will run the tests and print the results
    The function will generate a .xml file with the results of the tests
    The function will return 0 if everything went well
    The function will return 0 if the user used the --help or -h flag
    The function will return 84 if the user used an unknown flag
    """

    test_nb = len(tests)
    result = []
    print_details = handleArgsErrors()
    if print_details == Error.DELETE:
        os.remove("f_test.xml")
        return 0

    if print_details != Error.VERBOSE and print_details != Error.NONE and print_details != Error.DELETE:
        return print_details.value
    result = [runTest(test, print_details) for test in tests]
    print(f"[====] Synthesis: Tested: {test_nb}\
        | Passing: {result.count(State.OK)}\
        | Failing: {result.count(State.KO)}\
        | Crashing: {result.count(State.CRASH)}")
    generateFile(result)
    return 0

if __name__ == "__main__":
    main()
