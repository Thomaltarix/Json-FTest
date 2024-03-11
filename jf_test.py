#!/usr/bin/python3

from subprocess import Popen, PIPE
from enum import Enum
from sys import argv
from junit_xml import TestSuite, TestCase
from os import path, remove, getcwd
from json import load

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

    def __init__(self, testName, binaryPath, arguments, commandLineInputs, expectedReturnCode, expectedStdoutOutput, expectedStderrOutput):
        self.testName = testName
        self.binaryPath = binaryPath
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
        self.tests = {}
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
    if test.arguments:
        commandLine.extend(test.arguments)
    try:
        # subprocess.run
        process = Popen(commandLine,
                    cwd=getcwd(),
                    stdout=PIPE,
                    stderr=PIPE,
                    stdin=PIPE,
                    universal_newlines=True)
    except FileNotFoundError:
        test.state = State.CRASH
        test.result = f"Test \"{test.testName}\" failed: The binary path \"{test.binaryPath}\" is invalid"
        return
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

def runTests(arguments):
    """
    Runs every test in every test files
    """

    for testArray in arguments.tests.items():
        for test in testArray[1]:
            runTest(test)

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
    testSuite = []
    for testArray in arguments.tests.items():
        testCases = []
        for test in testArray[1]:
            testCases.append(TestCase(test.testName, classname="",
            stdout=test.stdout, stderr=test.stderr,
            elapsed_sec=0.0, status=test.state))
        testSuite.append(TestSuite(testArray[0], testCases))
    with open("jf_test.xml", "w") as file:
        TestSuite.to_file(file, testSuite, prettyprint=True)

def deleteFile(arguments):
    """
    Deletes the .xml file if the --delete/-d option is on
    """

    if arguments.delete:
        if path.exists("jf_test.xml"):
            remove("jf_test.xml")

def createTest(test):
    """
    Creates a Test object from a dictionary
    """

    return Test(
        test["testName"],
        test["binaryPath"],
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
        if (filePath[0] == '-'):
            raise ValueError
        with open(filePath, "r") as file:
            arguments.tests[path.basename(filePath)] = []
            data = load(file)
            for test in data:
                arguments.tests[path.basename(filePath)].append(createTest(test))
    except FileNotFoundError:
        arguments.setError(f"File {filePath} not found")
    except ValueError:
        arguments.setError(f"Invalid option {filePath}")

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

    koTests, crashTests, okTests, testNb = 0, 0, 0, 0

    for testArray in arguments.tests.values():
        for test in testArray:
            testNb += 1
            if test.state == State.KO:
                koTests += 1
            if test.state == State.CRASH:
                crashTests += 1
            if test.state == State.OK:
                okTests += 1
            if test.state == State.OK and not arguments.verbose:
                continue
            print(test.result)

    if koTests > 0 or crashTests > 0:
        arguments.exitCode = Error.ERROR

    print(f"[====] Synthesis: Tested: {testNb}"
        + f" | Passing: {okTests} | Failing: {koTests} | Crashing: {crashTests}")
    return (koTests, crashTests)

def printUsage(exitCode):
    """
    Prints the usage of the script
    """

    print("Usage:\n\
        ./jf_test.py [options] [test_files.json] ...\n\
        \n\tOptions:\n\
        \t--help, -h: Display this help\n\
        \t--verbose, -v: Display the result of passed tests\n\
        \t--delete, -d: Do not generate the .xml file and delete it if it exists\n\
        \n\tTest files:\n\
        \tTest files must be a .json files\n\
        \tTest files must contain an array of tests\n\
        \tEach test must contain the following keys:\n\
        \t\ttestName: The name of the test\n\
        \t\tbinaryPath: The path to the binary to test\n\
        \t\targuments: An array of arguments to pass to the binary\n\
        \t\tcommandLineInputs: An array of command line inputs\n\
        \t\texpectedReturnCode: The expected return code of the program\n\
        \t\texpectedStdoutOutput: The expected stdout output of the program\n\
        \t\texpectedStderrOutput: The expected stderr output of the program")
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
    if len(argv) == 1:
        return
    if arguments.help:
        printUsage(arguments.exitCode)
    if arguments.error:
        printError(arguments.errorString, arguments.exitCode)
    runTests(arguments)
    (koTests, crashedTests) = printResults(arguments)
    generateFile(arguments)
    deleteFile(arguments)
    if koTests > 0 or crashedTests > 0:
        exit(Error.ERROR.value)
    exit(0)

if __name__ == "__main__":
    main()
