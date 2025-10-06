cmake_minimum_required(VERSION 3.10)
project(MyOGDFProject)

# If installed globally, this will find OGDF automatically
find_package(OGDF REQUIRED)

add_executable(test static.cpp)
target_link_libraries(test OGDF)
