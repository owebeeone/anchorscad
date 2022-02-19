'''
Created on 14 Jan 2021

@author: gianni
'''

from dataclasses import dataclass
import unittest

@dataclass
class AssertionException(Exception):
    depth: tuple
    ex: object
    
class IterableAssert(Exception):
    '''Exception in iterable_assert'''
    
    
def is_iterable(v):
    try:
        gen = (d for d in v)
        return (gen,)
    except:
        pass
    return ()

def _iterable_assert(expect_fun, va, vb, depth=()):
    ii_va = is_iterable(va)
    ii_vb = is_iterable(vb)

    try:
        both_true = ii_va and ii_vb
    except BaseException as ex:
        raise AssertionException(depth, ex)
    
    if both_true:
        try:
            assert len(va) == len(vb), (
                f'Lengths different depth={depth} len(va)={len(va)} != len(vb)={len(vb)}')
            for i, evab in enumerate(zip(va, vb)):
                eva, evb = evab
                _iterable_assert(expect_fun, eva, evb, depth + (i,))
        except AssertionException:
            raise
        except BaseException as ex:
            raise AssertionException(depth, ex)
    else:
        try:
            assert not ii_va and not ii_vb
            expect_fun(va, vb)
        except AssertionException:
            raise
        except (BaseException, AssertionError) as ex:
            raise AssertionException(depth, ex)

def iterable_assert(expect_fun, va, vb):
    try:
        _iterable_assert(expect_fun, va, vb)
    except AssertionException as e:
        msg = f'depth={e.depth!r}\nva={va!r}\nvb={vb!r}\n{e.ex}\n'
        raise IterableAssert(msg)

