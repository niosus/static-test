py_binary(
  name = "compile_static_test",
  srcs = ["compile_static_test.py"],
  testonly = True,
  visibility = ["//visibility:public"]
)

cc_library(
  name = "static_test",
  hdrs = ["static_test.h"],
  data = [
    ":compile_static_test",
  ],
  testonly = True,
  visibility = ["//visibility:public"]
)
