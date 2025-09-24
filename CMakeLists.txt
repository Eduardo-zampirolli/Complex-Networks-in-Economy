cmake_minimum_required(VERSION 3.10)
project(MyOGDFProject)

find_package(OGDF REQUIRED)
add_executable(jk teste.cpp)
target_link_libraries(jk OGDF)

