cmake_minimum_required(VERSION 3.10)
project(simple_mandelbrot)

set(CMAKE_CXX_STANDARD 17)

include_directories(${PROJECT_SOURCE_DIR})
include_directories(${PROJECT_SOURCE_DIR}/model)

FILE(GLOB MODELFILES ${PROJECT_SOURCE_DIR}/model/*.cpp)

set(CMAKE_CXX_FLAGS "-ffast-math")

# MAIN

add_executable(example main.cpp ${MODELFILES})

find_package(PNG REQUIRED)
include_directories(${PNG_INCLUDE_DIR})
target_link_libraries(example ${PNG_LIBRARY})

find_package(JPEG REQUIRED)
include_directories(${JPEG_INCLUDE_DIR})
target_link_libraries(example ${JPEG_LIBRARY})

find_package(Threads REQUIRED)
target_link_libraries(example ${CMAKE_THREAD_LIBS_INIT})

target_link_libraries(example ${CMAKE_DL_LIBS})

add_definitions(-DTHREADS -D_REENTRANT -DPNG_ENABLED -DJPG_ENABLED)

# FRACT_STDLIB

add_library(fract_stdlib SHARED
    ${PROJECT_SOURCE_DIR}/fract_stdlib.cpp
    ${PROJECT_SOURCE_DIR}/model/colorutils.cpp
    ${PROJECT_SOURCE_DIR}/model/colormap.cpp
    ${PROJECT_SOURCE_DIR}/model/image.cpp)

set_target_properties(fract_stdlib PROPERTIES PREFIX "")
set_target_properties(fract_stdlib PROPERTIES SUFFIX ".so")

# FORMULA LIB

add_library(formula SHARED
    ${PROJECT_SOURCE_DIR}/formula.c)
set_target_properties(formula PROPERTIES SUFFIX ".so")
set_target_properties(formula PROPERTIES PREFIX "")
