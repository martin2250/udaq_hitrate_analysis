#include <pybind11/pybind11.h>

uint16_t fletcher_16(pybind11::bytes input) {
    pybind11::buffer_info info(pybind11::buffer(input).request());
    uint8_t sum1 = 0, sum2 = 0;
    uint8_t *data = (uint8_t*)info.ptr;
    for (ssize_t i = 0; i < info.size; i++) {
        sum1 = ((sum1 + data[i]) % 255);
        sum2 = ((sum2 + sum1) % 255);
    }
    return (sum1 << 8) | sum2;
}

PYBIND11_MODULE(checksum_fletcher, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("fletcher_16", &fletcher_16, "fletcher_16");
}