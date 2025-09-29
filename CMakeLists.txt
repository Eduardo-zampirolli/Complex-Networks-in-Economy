cmake_minimum_required(VERSION 3.10)
project(MyOGDFProject)

find_package(OGDF REQUIRED)
add_executable(dynamic dynamic_wrong.cpp)
target_link_libraries(dynamic OGDF)
