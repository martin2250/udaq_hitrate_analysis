SUFFIX := $(shell python3-config --extension-suffix)
INCLUDES := $(shell python3 -m pybind11 --includes)

MODULES := checksum_fletcher$(SUFFIX) analyze_hitbuf$(SUFFIX)

.PHONY: all
all: $(MODULES)

%$(SUFFIX): %.cpp
	c++ -O3 -Wall -shared -std=c++17 -fPIC $(INCLUDES) $< -o $@