'''
Created on 16 May 2020

@author: gianni
'''

class W(object):
    '''
    classdocs
    '''
    
    class I:
        X = 1
        
        @classmethod
        def f(cls):
            def e(v):
                print(cls.X, ' -- ', v)
            return e
        
    Q = I.f()
