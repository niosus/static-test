# Static test playground

⚠️ The code is just an experiment. Compiles and runs on Ubuntu 20.04. Work with other systems is not guaranteed. ⚠️

## What is a static test

If we want to _check_ that some code does not compile there is no way to write a test for it.

This repo aims at solving this problem.

## How it looks to the user

The proposal for the user interface for this feature is to piggyback on GTest pipeline as follows:

```c++
#include <gtest/gtest.h>
#include "static_test.h"

STATIC_TEST(foo) {
  Foo foo;
  foo.bar();
  SHOULD_NOT_COMPILE(foo.stuff());
  SHOULD_NOT_COMPILE_WITH_MESSAGE(foo.stuff(), "has no member named 'stuff'");
}
```

The user is able to write a code to check that some code should not compile. All the code outside of
the `SHOULD_NOT_COMPILE` or `SHOULD_NOT_COMPILE_WITH_MESSAGE` macros is compiled and run as
expected. The compiler will happily report any errors back to the user if they should make any
within the `STATIC_TEST` scope. If the code under `SHOULD_NOT_COMPILE` ends up actually compiling a
runtime error will be issued with a description of this.

This test can be run within this repo as:
```
./bazelisk test --test_output=all //foo:test_foo
```

The approximate output of this test if nothing fails would be smth like this:

```
[----------] 1 test from StaticTest__foo
[ RUN      ] StaticTest__foo.foo
[ COMPILE STATIC TEST ] foo
[                  OK ] foo
[       OK ] StaticTest__foo.foo (966 ms)
[----------] 1 test from StaticTest__foo (966 ms total)

```

If there _is_ a failure, the line that causes the failure will be printed like so:

```
[----------] 1 test from StaticTest__FooMixedCorrectAndWrongTest
[ RUN      ] StaticTest__SomeTest.SomeTest
[ COMPILE STATIC TEST ] SomeTest
ERROR: foo/test_foo.cpp:35: must fail to compile but instead compiled without error.
foo/test_foo.cpp:0: Failure
Some of the static tests failed. See above for error.
[              FAILED ] SomeTest
[  FAILED  ] StaticTest__SomeTest.SomeTest (1403 ms)
[----------] 1 test from StaticTest__SomeTest (1403 ms total)

```

Currently, the code expects to have a compilation database with at the root of the project. This can
be generated from a bazel build using the following repository:
https://github.com/grailbio/bazel-compilation-database. Just download it anywhere and call the
`generate.sh` script in the folder of this project.

Eventually, we might want to plug this into the build system to make sure we have everything at hand
when running the test.


## How to check that something fails to compile

We obviously cannot write a normal unit test for this, as if we write code that does not compile it,
well, does not compile. The only way I can think of here is to run an external tool.

So the `STATIC_TEST` macro would expand into a class that will do work in its constructor. It will
essentially call an external tool providing it with the name of the static test and a path to the
current file utilizing `__FILE__`. If we know the compilation flags for this file we can write a new
temporary cpp file with the contents:

```cpp
#include <gtest/gtest.h>

#include "foo/foo.h"
#include "static_test/static_test.h"

int main()
{
  Foo foo;
  foo.bar();
  foo.stuff();
  foo.baz();
  return 0;
}
```

We can then compile this file using all the same compilation flags and check if there is an error
that matches the error message regex provided into the message. If there is an error, then we pass
the test. If there is no error that matches, we fail the test.

