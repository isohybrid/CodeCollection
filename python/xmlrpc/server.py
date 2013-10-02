#coding=utf-8

from xmlrpclib import ServerProxy, Fault
from os.path import join, abspath, isfile
from SimpleXMLRPCServer import SimpleXMLRPCServer
from urlparse import urlparse
import sys

SimpleXMLRPCServer.allow_reuse_address = 1

MAX_HISTORY_LENGTH = 6

UNHANDlED = 100
ACCESS_DENIED = 200

class UnhandledQuery(Fault):
  '''
  that's show can't handle the query exception
  '''
  def __init__(self, message="Couldn't handle the query"):
    Fault.__init__(self, UNHANDlED, message)

class AccessDenied(Fault):
  '''
  when user try to access the forbiden resources raise exception
  '''
  def __init__(self, message="Access denied"):
    Fault.__init__(self, ACCESS_DENIED, message)

def inside(dir, name):
  '''
  check the dir that defined is contain the filename the user given
  '''
  dir = abspath(dir)
  name = abspath(name)
  return name.startswith(join(dir, ''))

def getPort(url):
  '''
  get the port num from the url
  '''
  name =urlparse(url)[1]
  parts = name.split(':')
  return int(parts[-1])

class Node:

  def __init__(self, url, dirname, secret):
    self.url = url
    self.dirname = dirname
    self.secret = secret
    self.known = set()

  def query(self, query, history = []):
    try:
      return self._handle(query)
    except UnhandledQuery:
      history = history + [self.url]
      if len(history) > MAX_HISTORY_LENGTH: raise
      return self._broadcast(query, history)

  def hello(self, other):
    self.known.add(other)
    return 0

  def fetch(self, query, secret):

    if secret != self.secret: raise
    result = self.query(query)
    f = open(join(self.dirname, query), 'w')
    f.write(result)
    f.close()
    return 0

  def _start(self):
    s = SimpleXMLRPCServer(("", getPort(self.url)), logRequests=False)
    s.register_instance(self)
    s.serve_forever()

  def _handle(self, query):
    dir = self.dirname
    name = join(dir, query)
    if not isfile(name):raise UnhandledQuery
    if not inside(dir, name):raise AccessDenied
    return open(name).read()

  def _broadcast(self, query, history):

    for other in self.known.copy():
      if other in history: continue
      try:
        s = ServerProxy(other)
        return s.query(query, history)
      except Fault, f:
        if f.faultCode == UNHANDlED:pass
        else: self.known.remove(other)
      except:
        self.known.remove(self)

    raise UhandledQuery

def main():
  url, directory, secret = sys.argv[1:]
  n = Node(url, directory, secret)
  n._start()

if __name__ == '__main__': main()