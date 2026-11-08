
cmake_minimum_required(VERSION 3.10)
project(robo_arm)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(my_arm_pid src/my_arm_pid.cpp)

ament_target_dependencies(my_arm_pid
  rclcpp
  sensor_msgs
)

install(TARGETS
  my_arm_pid
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

