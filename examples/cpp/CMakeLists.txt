cmake_minimum_required(VERSION 3.10)
project(simple_mandelbrot)

set(CMAKE_CXX_STANDARD 17)

# add some debug information: elapsed time and compiler information
set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CMAKE_COMMAND} -E time")
set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK "${CMAKE_COMMAND} -E time")
set(CMAKE_VERBOSE_MAKEFILE on)
message("Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")

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

get_filename_component(FORMULA_FILE $ENV{formula_source} NAME)

add_library(formula SHARED
        ${PROJECT_SOURCE_DIR}/${FORMULA_FILE})

if("$ENV{gmp_support}" STREQUAL "1")
    message("gmp support enabled")

    # https://github.com/symengine/symengine/blob/master/cmake/LibFindMacros.cmake
    find_library(MPFR_LIBRARIES NAMES mpfr)
    find_library(GMP_LIBRARIES NAMES gmpxx)

    find_path(MPFR_INCLUDES NAMES mpfr.h)
    find_path(GMP_INCLUDE_DIR NAMES gmpxx.h)

    include_directories(${GMP_INCLUDE_DIR})
    target_link_libraries(formula ${GMP_LIBRARIES})
    include_directories(${MPFR_INCLUDES})
    target_link_libraries(formula ${MPFR_LIBRARIES})

else()
    message("gmp support disabled")

endif()

set_target_properties(formula PROPERTIES SUFFIX ".so")
set_target_properties(formula PROPERTIES PREFIX "")
