cmake_minimum_required(VERSION 2.8.12)

project(mutate)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)
message(STATUS "Using ClangConfig.cmake in ${Clang_DIR}")

include_directories(${CLANG_INCLUDE_DIRS})
include_directories(${LLVM_INCLUDE_DIRS})

link_directories(${LLVM_LIBRARY_DIRS})

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address  -fsanitize-recover=address -fno-stack-protector -fno-omit-frame-pointer")
set(CLANG_LIBS
    clangAST
    clangBasic
    clangFrontend
    clangParse
    clangLex
    clangRewrite
)

add_executable(mutates 
    Mutator.cpp
    AddUnusedVar.h
    AddUnusedVar.cpp
    RewriteUtils.h
    RewriteUtils.cpp
)

target_link_libraries(mutates
    asan
    LLVM
    ${CLANG_LIBS}
)