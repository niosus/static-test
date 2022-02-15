TEST_SOURCES = [
  "test_foo.cpp"
]

filegroup(
  name = "sources",
  srcs = TEST_SOURCES
)

cc_library(
  name = "foo",
  hdrs = ["foo.h"],
  visibility = ["//visibility:public"]
)

cc_test(
  name = "test_foo",
  srcs = TEST_SOURCES,
  deps = [
    ":foo",
    "//static_test:static_test",
    "@gtest//:gtest",
    "@gtest//:gtest_main",
  ],
  data = [":sources"],
  visibility = ["//visibility:public"]
)
