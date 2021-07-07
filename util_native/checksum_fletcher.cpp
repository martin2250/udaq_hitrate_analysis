#include <pybind11/pybind11.h>

uint16_t fletcher16_wikipedia(const uint8_t *data, size_t len) {
	uint32_t c0, c1;

	/*  Found by solving for c1 overflow: */
	/* n > 0 and n * (n+1) / 2 * (2^8-1) < (2^32-1). */
	for (c0 = c1 = 0; len > 0; ) {
		size_t blocklen = len;
		if (blocklen > 5002) {
			blocklen = 5002;
		}
		len -= blocklen;
		do {
			c0 = c0 + *data++;
			c1 = c1 + c0;
		} while (--blocklen);
		c0 = c0 % 255;
		c1 = c1 % 255;
   }
   return (c1 << 8 | c0);
}

uint16_t fletcher_16(pybind11::buffer input) {
    pybind11::buffer_info info = input.request();

    return fletcher16_wikipedia((uint8_t*)info.ptr, (size_t)info.size);
}

uint16_t fletcher_16_basic(pybind11::bytes input) {
    pybind11::buffer_info info(pybind11::buffer(input).request());

    uint8_t sum1 = 0, sum2 = 0;
    uint8_t *data = (uint8_t*)info.ptr;
    for (ssize_t i = 0; i < info.size; i++) {
        sum1 = ((sum1 + data[i]) % 255);
        sum2 = ((sum2 + sum1) % 255);
    }
    return (sum2 << 8) | sum1;
}

PYBIND11_MODULE(checksum_fletcher, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("fletcher_16", &fletcher_16, "fletcher_16");
    m.def("fletcher_16_basic", &fletcher_16_basic, "fletcher_16_basic");
}