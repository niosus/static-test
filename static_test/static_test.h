#include <gtest/gtest.h>
#include <iostream>
#include <string>

#define STATIC_TEST(NAME)                                                      \
  class StaticTest__##NAME : public StaticTest {                               \
  public:                                                                      \
    StaticTest__##NAME() noexcept : StaticTest{#NAME, __FILE__} {}             \
  };                                                                           \
  /* Create a test that uses this fixture.*/                                   \
  TEST_F(StaticTest__##NAME, NAME)

#define SHOULD_NOT_COMPILE(IGNORED_CODE)
#define SHOULD_NOT_COMPILE_WITH_MESSAGE(IGNORED_CODE, IGNORED_MESSAGE)

class StaticTest : public ::testing::Test {
public:
  StaticTest() = default;
  StaticTest(const std::string &name, const std::string &file)
      : name_{name}, file_{file} {
    std::cerr << "[ COMPILE STATIC TEST ] " << name << std::endl;
    std::string cmd =
        std::string("python3 static_test/compile_static_test.py") + " --name " +
        name_ + " --file " + file_;
    const auto exit_status = std::system(cmd.c_str());
    if (exit_status == 0) {
      std::cerr << "[                  OK ] " << name << std::endl;
    } else {
      GTEST_MESSAGE_AT_(file_.c_str(), 0,
                        "Some of the static tests failed. See above for error.",
                        ::testing::TestPartResult::kNonFatalFailure);
      std::cerr << "[              FAILED ] " << name << std::endl;
    }
  }

private:
  std::string name_{};
  std::string file_{};
};
