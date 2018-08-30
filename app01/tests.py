from django.test import TestCase

# Create your tests here.
'''

'''
class User(object):
    pass

class Role(object):
    pass

class Bar(object):
    def __init__(self,b):
        self.b = b

_registry = {
    User:Bar(User),
    Role:Bar(Role),
}


for k,v in _registry.items():
    print(k, v.b)