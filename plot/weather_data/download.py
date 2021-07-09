import urllib.request
import gzip
import sys

urls = [
    f'https://gml.noaa.gov/aftp/data/radiation/baseline/spo/2021/spo21{i:03}.dat' for i in range(70, 188)
]

with gzip.open('weather.dat.gz', 'wb') as gzf:
    for i, url in enumerate(urls):
        print(f'{i:3}/{len(urls)}', url)
        with urllib.request.urlopen(url) as dl:
            if i != 0:
                dl.readline()
                dl.readline()
            gzf.write(dl.read())
