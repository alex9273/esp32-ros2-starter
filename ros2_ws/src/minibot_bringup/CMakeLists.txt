cmake_minimum_required(VERSION 3.10)
project(minibot_bringup)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch config worlds DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/drive_test.py DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)
  ament_add_pytest_test(test_model_matches_config test/test_model_matches_config.py)
  ament_add_pytest_test(test_drive_test_math test/test_drive_test_math.py)
  # Starts Gazebo headless and drives the robot. Skip it with: colcon test --ctest-args -E sim_drive
  add_launch_test(test/test_sim_drive.py TARGET test_sim_drive TIMEOUT 180)
endif()

ament_package()
