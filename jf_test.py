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
    DELETE = 2
    NONE = 3
    ERROR = 84

class Test:
    """
    Class to represent a test
    """

    def __init__(self, testName, binaryPath, fileInput, arguments, commandLineInputs, expectedReturnCode, expectedStdoutOutput, expectedStderrOutput):
        self.testName = testName
        self.binaryPath = binaryPath
        self.fileInput = fileInput
        self.arguments = arguments
        self.commandLineInputs = commandLineInputs
        self.expectedReturnCode = expectedReturnCode
        self.expectedStdoutOutput = expectedStdoutOutput
        self.expectedStderrOutput = expectedStderrOutput
        self.stdout = ""
        self.stderr = ""
        self.result = ""
        self.returnCode = 0
        self.state = State.OK

class Arguments:
    """
    Class to represent the arguments of the program
    """

    def __init__(self):
        self.help = False
        self.verbose = False
        self.delete = False
        self.error = False
        self.exitCode = 0
        self.tests = []
        self.errorString = ""

    def setHelp(self):
        self.help = True
        self.exitCode = Error.HELP

    def setVerbose(self):
        self.verbose = True

    def setDelete(self):
        self.delete = True

    def setError(self, errorString):
        self.error = True
        self.errorString = errorString
        self.exitCode = Error.ERROR

    def addTest(self, test):
        self.tests.append(test)

options = [
    ("--help", Arguments.setHelp),
    ("-h", Arguments.setHelp),
    ("--verbose", Arguments.setVerbose),
    ("-v", Arguments.setVerbose),
    ("--delete", Arguments.setDelete),
    ("-d", Arguments.setDelete),
]

# Array that define what a test should contain
testKeys = [
    "testName",
    "binaryPath",
    "fileInput",
    "arguments",
    "commandLineInputs",
    "expectedReturnCode",
    "expectedStdoutOutput",
    "expectedStderrOutput"
]

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

def parseTest(arguments, filePath):
    """
    Parses the test file
    """

    try:
        with open(filePath, "r") as file:
            data = json.load(file)
            for test in data:
                arguments.addTest(createTest(test))
    except FileNotFoundError:
        arguments.setError(f"File {filePath} not found")

def parseArgs(arguments, argv):
    """
    Parses the arguments of the program
    """

    for i in range(1, len(argv)):
        if arguments.error:
            return
        found = False
        for option in options:
            if argv[i] == option[0]:
                option[1](arguments)
                found = True
                break
        if not found:
            parseTest(arguments, argv[i])

def printUsage(exitCode):
    """
    Prints the usage of the script
    """

    print("Usage:\n\
        ./jf_test.py [options] [test_file.json]\n\
        \n\tOptions:\n\
        \t--help, -h: Display this help\n\
        \t--verbose, -v: Display the result of each test\n\
        \t--delete, -d: Delete the generated .xml file at the end\n\
        \n\tTest file:\n\
        \tThe test files must be a .json file\n\
        \tThe test files must contain an array of tests\n\
        \tEach test must contain the following keys:\n\
        \t\ttestName: The name of the test\n\
        \t\tbinaryPath: The path to the binary to test\n\
        \t\tfileInput: The path to the file to use as input\n\
        \t\targuments: An array of arguments to pass to the binary\n\
        \t\tcommandLineInputs: An array of command line inputs\n\
        \t\texpectedReturnCode: The expected return code of the binary\n\
        \t\texpectedStdoutOutput: The expected stdout output of the binary\n\
        \t\texpectedStderrOutput: The expected stderr output of the binary")
    exit(exitCode.value)

def printError(errorString, exitCode):
    """
    Prints an error message
    """

    print(f"Error: {errorString}")
    exit(exitCode.value)

def main():
    """
    Main function of the script
    """

    arguments = Arguments()
    parseArgs(arguments, argv)

    if arguments.help:
        printUsage(arguments.exitCode)
    if arguments.error:
        printError(arguments.errorString, arguments.exitCode)
        | Passing: {result.count(State.OK)}\
        | Failing: {result.count(State.KO)}\
        | Crashing: {result.count(State.CRASH)}")
    generateFile(result)
    return 0

if __name__ == "__main__":
    main()
