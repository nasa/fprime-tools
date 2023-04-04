#####
# '{{cookiecutter.deployment_name}}' Deployment:
#
# This sets up the build for the '{{cookiecutter.deployment_name}}' Application, including custom
# components. In addition, it imports FPrime.cmake, which includes the core F Prime components.
#
#####

###
# Basic Project Setup
###
cmake_minimum_required(VERSION 3.13)
cmake_policy(SET CMP0048 NEW)
project({{cookiecutter.deployment_name}} VERSION 1.0.0 LANGUAGES C CXX)

###
# F' Core Setup
# This includes all of the F prime core components, and imports the make-system.
###
include("${FPRIME_FRAMEWORK_PATH}/cmake/FPrime.cmake")
# NOTE: register custom targets between these two lines
include("${FPRIME_FRAMEWORK_PATH}/cmake/FPrime-Code.cmake")

###
# Components and Topology
###
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Top/")

set(SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/Main.cpp")
set(MOD_DEPS ${PROJECT_NAME}/Top)

register_fprime_deployment()
