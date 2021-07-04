#include <pybind11/pybind11.h>
#include <tuple>
#include <iostream>

const uint8_t OBJECT_CODE_PPS_SECOND  = 0xe0;
const uint8_t OBJECT_CODE_PPS_YEAR    = 0xe4;
const uint8_t OBJECT_CODE_TRIG_CONFIG = 0xe5;
const uint8_t OBJECT_CODE_DATA_FORMAT = 0xe6;

std::tuple<int, int> analyze_hitbuf(pybind11::bytes input) {
    pybind11::buffer_info info(pybind11::buffer(input).request());
    int seconds = 0, hits = 0;
    // all byte objects seem to be aligned to 16 bits
    uint32_t *data = (uint32_t *)info.ptr;
    std::size_t count = info.size / sizeof(uint32_t);
    for (size_t i = 0; i < count; i++) {
        uint32_t header = data[i];
        uint8_t type = static_cast<uint8_t>(header >> 24);
        switch (type) {
            case OBJECT_CODE_PPS_SECOND: {
                seconds++;
                break;
            }
            case OBJECT_CODE_TRIG_CONFIG: {
                i++; // skip one word
                if (i > count) {
                    throw pybind11::value_error("incomplete frame");
                }
                break;
            }
            case OBJECT_CODE_PPS_YEAR:
            case OBJECT_CODE_DATA_FORMAT: {
                break; // do nothing
            }
            default: {
                hits++;
                i++; // next word contains number of ADCs
                if (i >= count) {
                    throw pybind11::value_error("incomplete frame");
                }
                std::size_t adc_count = (data[i] >> 28) & 0xf;
                std::size_t extra_words = adc_count / 2;
                i += extra_words;
                if (i > count) {
                    throw pybind11::value_error("incomplete frame");
                }
                break;
            }
        }
    }
    return std::make_tuple(seconds, hits);
}

PYBIND11_MODULE(analyze_hitbuf, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("analyze_hitbuf", &analyze_hitbuf, "analyze_hitbuf");
}
