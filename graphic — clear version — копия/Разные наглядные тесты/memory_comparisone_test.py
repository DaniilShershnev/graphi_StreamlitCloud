import sys
import numpy
n=10000000
a = []
for i in range(n):
    a.append(float(i))
numpy_array = numpy.array(a , dtype = numpy.float64)
list_size = sys.getsizeof(a)+sum(sys.getsizeof(x) for x in a)
numpy_size = numpy_array.nbytes
print(f'Список питон {list_size / 1024 / 1024 : 2f} Мб' )
print(f'Список нампай {numpy_size / 1024 / 1024 : 2f} Мб' )
