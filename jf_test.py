#!/usr/bin/python3

from subprocess import Popen, PIPE
from enum import Enum
from sys import argv
from junit_xml import TestSuite, TestCase
import os
import json

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

# Array that define every Arguments class function to call for earch options
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

def setResult(test):
    """
    Sets the result of a test
    The result contains the state of the test and the result of the test
    """

    if test.stdout == " Hello World\n":
        print("test")

    if test.returnCode == 139:
        test.state = State.CRASH
        test.result = f"Test \"{test.testName}\" failed: the program crashed with signal {test.returnCode}"
    elif test.stdout != test.expectedStdoutOutput:
        test.state = State.KO
        test.result = f"Test \"{test.testName}\" failed: Expected output is:\
        \n{test.expectedStdoutOutput}\nActual output is: \n{test.stdout}"
    elif test.stderr != test.expectedStderrOutput:
        test.state = State.KO
        test.result = f"Test \"{test.testName}\" failed: Expected error output is:\
        \n{test.expectedStderrOutput}\nActual error output is: \n{test.stderr}"
    else:
        if test.returnCode != test.expectedReturnCode:
            test.state = State.KO
            test.result = f"Test \"{test.testName}\" failed: Expected return code is:\
            {test.expectedReturnCode}, Actual return code is: {test.returnCode}"
        else:
            test.state = State.OK
            test.result = f"Test \"{test.testName}\" passed"

def runTest(test):
    """
    Runs a given command with given arguments and returns the result
    The function will also print the result if --verbose or -v is on

    ! WARNING !
    ! You must implement a command that stops the command line input
    ! if you don't do this, the process will be stuck in the while loop
    ! since you can't CTRL+D or CTRL+C the process.
    ! WARNING !
    """

    commandLine = [test.binaryPath]
    if test.fileInput:
        commandLine.append(test.fileInput)
    if test.arguments:
        commandLine.extend(test.arguments)
    process = Popen(commandLine,
                    cwd=os.getcwd(),
                    stdout=PIPE,
                    stderr=PIPE,
                    stdin=PIPE,
                    universal_newlines=True)
    while process.poll() is None:
        for clInput in test.commandLineInputs:
            if clInput[len(clInput) - 1] != '\n':
                clInput += '\n'
            process.stdin.write(clInput)
        process.stdin.flush()
        child_output = process.stdout.readline()
        test.stdout += child_output
        child_error = process.stderr.readline()
        test.stderr += child_error

    process.stdin.close()
    process.stdout.close()
    process.stderr.close()
    test.returnCode = process.returncode
    setResult(test)

def generateFile(arguments):
    """
    Generates a .xml file with the results of the tests.
    The file will be named f_test.xml
    The file will be generated in the same directory as the script
    The file will be generated in JUnit format, so it can be read by Jenkins
    The script do not handle the elapsed time of the tests
    """

    if arguments.delete:
        return
    testCases = []
    for i in range(len(arguments.tests)):
        testCases.append(TestCase(arguments.tests[i].testName, classname="",
        stdout=arguments.tests[i].stdout, stderr=arguments.tests[i].stderr,
        elapsed_sec=0.0, status=arguments.tests[i].result))
    testSuite = TestSuite("jf_test", testCases)
    with open("jf_test.xml", "w") as file:
        TestSuite.to_file(file, [testSuite], prettyprint=True)

def createTest(test):
    """
    Creates a Test object from a dictionary
    """

    return Test(
        test["testName"],
        test["binaryPath"],
        test["fileInput"],
        test["arguments"],
        test["commandLineInputs"],
        test["expectedReturnCode"],
        test["expectedStdoutOutput"],
        test["expectedStderrOutput"]
    )

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

def printResults(arguments):
    """
    Prints the results of the tests
    """

    koTests, crashTests, okTests = 0, 0, 0

    for test in arguments.tests:
        if test.state == State.KO:
            koTests += 1
        elif test.state == State.CRASH:
            crashTests += 1

    if koTests > 0 or crashTests > 0:
        arguments.exitCode = Error.ERROR
    for test in arguments.tests:
        if test.state == State.OK and not arguments.verbose:
            continue
        print(test.result)

    print(f"[====] Synthesis: Tested: {len(arguments.tests)}"
        + f" | Passing: {okTests} | Failing: {koTests} | Crashing: {crashTests}")
    return (koTests, crashTests)

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
    for i in range(len(arguments.tests)):
        runTest(arguments.tests[i])
    (koTests, crashedTests) = printResults(arguments)
    generateFile(arguments)
    if arguments.delete:
        if os.path.exists("jf_test.xml"):
            os.remove("jf_test.xml")
    if koTests > 0 or crashedTests > 0:
        exit(Error.ERROR.value)
    exit(0)

if __name__ == "__main__":
    main()
