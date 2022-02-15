#include <gtest/gtest.h>
#include <type_traits>

#include "foo/foo.h"
#include "static_test/static_test.h"

template <typename T> struct Float {
  static_assert(std::is_floating_point<T>::value, "Must be floating point");
  T number;
};

TEST(Foo, foo) {
  Foo foo;
  foo.bar();
}

STATIC_TEST(foo) {
  Foo foo;
  foo.bar();
  SHOULD_NOT_COMPILE(foo.stuff());
  SHOULD_NOT_COMPILE_WITH_MESSAGE(foo.stuff(), "has no member named 'stuff'");
}

STATIC_TEST(FooNonExistingMethods) {
  Foo foo;
  foo.bar();
  EXPECT_EQ(1, 1);
  SHOULD_NOT_COMPILE(foo.blah());
  SHOULD_NOT_COMPILE_WITH_MESSAGE(foo.blah_blah_blah(), "has no member named 'blah_blah_blah'");
}

STATIC_TEST(FooMixedCorrectAndWrongTest) {
  Foo foo;
  foo.foo();
  SHOULD_NOT_COMPILE(foo.foo());
  SHOULD_NOT_COMPILE(foo.baz());
  foo.bar();
  SHOULD_NOT_COMPILE(foo.bar());
}

STATIC_TEST(FooWrongStaticTest) {
  Foo foo;
  foo.bar();
  EXPECT_EQ(1, 1);
  SHOULD_NOT_COMPILE(foo.baz());
  SHOULD_NOT_COMPILE_WITH_MESSAGE(foo.blah_blah(), "Wrong message");
}

STATIC_TEST(FloatTest) {
  SHOULD_NOT_COMPILE(Float<int> f);
  SHOULD_NOT_COMPILE_WITH_MESSAGE(Float<char> f, "static assertion failed: Must be floating point");
  SHOULD_NOT_COMPILE_WITH_MESSAGE(Float<char> f, "Wrong message");
}
