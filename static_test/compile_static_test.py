import sys
import argparse
import re
import json
import subprocess
from copy import copy
from typing import Any, List, Tuple

from pathlib import Path

# TODO(igor): we should also care about namespaces I guess.
_STATIC_CPP_FILE = """\
{original_cleaned_up_file}

int main() {{
{test}
return 0;
}}
"""


class StaticTestCode:
    def __init__(
            self: "StaticTestCode",
            code: str,
            starting_line: int,
            line_under_test: int = None,
            expected_error: str = None):
        self.code = code
        self.starting_line = starting_line
        self.line_under_test = line_under_test
        self.expected_error = expected_error


def run_command(command: str,
                cwd: str,
                shell: bool = False,
                stdin: Any = None,
                default: str = None) -> Tuple[str, int]:
    """Run a generic command in a subprocess.
    Args:
        command (str): command to run
        stdin: The standard input channel for the started process.
        default (str): The default return value in case run fails.
    Returns:
        str: raw command output or default value
    """
    output_text = default
    return_code = 0
    try:
        startupinfo = None
        output = subprocess.check_output(
            command,
            stdin=stdin,
            stderr=subprocess.STDOUT,
            shell=shell,
            cwd=cwd,
            startupinfo=startupinfo,
        )
        output_text = "".join(map(chr, output))
        return_code = 0
    except subprocess.CalledProcessError as e:
        output_text = e.output.decode("utf-8")
        return_code = 1
    except OSError:
        output_text = "Executable file not found executing: {}".format(command)
        return_code = 2
    return output_text, return_code


def find_line(query_pos: int, text: str) -> int:
    """Get the 0-indexed number of the line that contains the query_pos."""
    return text.count('\n', 0, query_pos)


def remove_all_static_tests(file_content: str) -> str:
    modified_content = copy(file_content)
    while True:
        start, end = find_static_test(modified_content)
        if not start or not end:
            break
        modified_content = modified_content[:start] + modified_content[end:]
    return modified_content


def find_static_test(
        file_content: str, name: str = r"\w+", full: bool = True) -> Tuple[int, int]:
    static_test_regex = r"(STATIC_TEST\({}\))".format(name)
    found_test = re.search(static_test_regex, file_content)
    if not found_test:
        return None, None
    found_curly_braces_count = None
    for pos in range(found_test.start(), len(file_content)):
        if found_curly_braces_count == 0:
            if full:
                return found_test.start(), pos
            else:
                opening_bracket_pos = file_content.find('{', found_test.end())
                return opening_bracket_pos + 1, pos - 1
        if file_content[pos] == "{":
            if found_curly_braces_count is None:
                found_curly_braces_count = 1
                continue
            found_curly_braces_count += 1
        if file_content[pos] == "}":
            found_curly_braces_count -= 1
    return None, None


def get_static_test_code(file_content: str, name: str) -> StaticTestCode:
    start, end = find_static_test(file_content, name, full=False)
    line_of_test = find_line(start, file_content) + 1  # We need a 1-indexed number.
    return StaticTestCode(code=file_content[start:end], starting_line=line_of_test)


def generate_individual_tests(static_test_code: StaticTestCode) -> List[StaticTestCode]:
    should_not_compile_regex = r"(?:SHOULD_NOT_COMPILE\((.*)\));|" + \
        r"(?:SHOULD_NOT_COMPILE_WITH_MESSAGE)*\((.*)(?:,\s*\"(?P<message>.*)\")\);"
    all_matches = re.findall(should_not_compile_regex, static_test_code.code)
    separate_tests = []
    for i in range(len(all_matches)):
        new_test_code = copy(static_test_code.code)
        # Remove all already processed macros
        if i > 0:
            new_test_code = re.sub(should_not_compile_regex, r"", new_test_code, count=i)
        # Replace the current macro
        match = re.search(should_not_compile_regex, new_test_code)
        line_of_test = find_line(match.start(), new_test_code)
        new_test_code =\
            new_test_code[:match.start()] + match.expand(r"\1\2;") + new_test_code[match.end():]
        # Remove all the other macros
        new_test_code = re.sub(should_not_compile_regex, r"", new_test_code)
        separate_tests.append(StaticTestCode(code=new_test_code,
                                             starting_line=static_test_code.starting_line,
                                             line_under_test=line_of_test,
                                             expected_error=match.group("message")))
    return separate_tests


def generate_static_test_cpp(file_content: str, name: str) -> List[StaticTestCode]:

    static_test_code = get_static_test_code(file_content, name)
    individual_tests = generate_individual_tests(static_test_code)
    file_without_static_tests = remove_all_static_tests(file_content)
    test_cpp_files = []
    for test in individual_tests:
        test_cpp_files.append(
            StaticTestCode(
                code=_STATIC_CPP_FILE.format(
                    original_cleaned_up_file=file_without_static_tests,
                    test=test.code),
                starting_line=test.starting_line,
                line_under_test=test.line_under_test,
                expected_error=test.expected_error))
    return test_cpp_files


def run_static_test(args):
    file_content = None
    file = Path(args.file)
    with open(file, "r") as f:
        file_content = f.read()
    test_cpp_files = generate_static_test_cpp(file_content, args.name)

    # Find the compilation database file.
    # TODO(igor): actually find it, not just set to a hardcoded relative path.
    compilation_database = file.resolve().parent.parent / "compile_commands.json"
    database_entry_list = None
    with open(compilation_database, "r") as f:
        contents = f.read()
        most_of_content, after_last_comma = contents.rsplit(",", 1)
        if len(after_last_comma) < 4:
            # We found a trailing comma. We can have a better check for this later.
            contents = most_of_content + after_last_comma
        database_entry_list = json.loads(contents)

    error_code = 0
    for entry in database_entry_list:
        if entry["file"] == args.file:
            directory = entry["directory"]
            new_file = Path(directory) / "my_static_test.cpp"
            for test in test_cpp_files:
                with open(new_file, "w") as f:
                    f.write(test.code)
                command = entry["command"][: -len(args.file)] + new_file.name
                output, return_code = run_command(command=command, cwd=directory, shell=True)
                if return_code == 0:
                    # The code compiled successfully which is not expected here.
                    print("ERROR: {file}:{line}:"
                          .format(file=args.file, line=test.starting_line + test.line_under_test),
                          "must fail to compile but instead compiled without error.")
                    error_code = 1
                    continue
                if test.expected_error and test.expected_error not in output:
                    print("ERROR: {file}:{line}: message '{error}'"
                          .format(file=args.file,
                                  line=test.starting_line + test.line_under_test,
                                  error=test.expected_error),
                          "not found in compilation error: \n{}".format(output))
                    error_code = 2
    return error_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile a static test")
    parser.add_argument(
        "--name", type=str, help="Name of the static test within the test file"
    )
    parser.add_argument("--file", type=str, help="A path to the test file")

    args = parser.parse_args()
    sys.exit(run_static_test(args))
