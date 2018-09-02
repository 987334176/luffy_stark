from django.test import TestCase

# Create your tests here.
'''
info = {'k1':'v1','k2':'v2'}
'''
from urllib.parse import urlencode
info = {'k1':'v1','k2':'v2'}
print(urlencode(info))

'''
def __deepcopy__(self, memo):
    result = self.__class__('', mutable=True, encoding=self.encoding)
    memo[id(self)] = result
    for key, value in six.iterlists(self):
        result.setlist(copy.deepcopy(key, memo), copy.deepcopy(value, memo))
    return result
'''