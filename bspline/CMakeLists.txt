project("Basic Spline")

set(CMAKE_CXX_FLAGS "--std=c++11 -O3 -Wall -Wextra") 

add_executable(bspline_main readin.cpp bspline.cpp bspline_main.cpp)
add_executable(find_r0 find_r0.cpp readin.cpp bspline.cpp zbrent.cpp)
add_executable(find_r1 find_r1.cpp readin.cpp bspline.cpp zbrent.cpp)
add_library(bspline_py SHARED readin.cpp bspline.cpp bspline_py.cpp bspline_main.cpp)

target_link_libraries(bspline_main -lgsl -lgslcblas -lm)
target_link_libraries(find_r0 -lgsl -lgslcblas -lm)
target_link_libraries(find_r1 -lgsl -lgslcblas -lm)
target_link_libraries(bspline_py -lgsl -lgslcblas -lm)
