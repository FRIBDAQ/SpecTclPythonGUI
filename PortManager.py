#!/usr/bin/env python



#    This software is Copyright by the Board of Trustees of Michigan
#    State University (c) Copyright 2013.
#
#    You may use this software under the terms of the GNU public license
#    (GPL).  The terms of this license are described at:
#
#     http://www.gnu.org/licenses/gpl.txt
#
#    Author:
#            Ron Fox
#            NSCL
#            Michigan State University
#            East Lansing, MI 48824-1321

##
# @file   PortManager.py
# @brief  Python API for the port manager.
# @author <fox@nscl.msu.edu>

import socket
import getpass
import tkinter as Tkinter


#   Below is a Tcl interpreter object that is used by all connection objects
#   to parse the returned lists.

_tcl = Tkinter.Tcl()

##
# @class PortManager
#
#    This class provides an interface to a port manager running on a specified
#    system.  Port managers allow you to:
#    *  Allocate ports for use as server listener ports from a pool of managed ports.
#    *  Determine which services have allocated which ports.
#
# @note Naturally you can only allocate a port from the local port manager.
#       The port manager itself enforces that restriction
class PortManager:
    ##
    # _init__
    #   Constructor for the object.  A connection is made to the specified
    #   port manager.   The connection is maintained until the object is destroyed.
    #   note that if you allocate a port you must maintain the connection to the
    #   port manager while you use that port as the drop of that connection
    #   is what releases the port.
    #
    # @param host - Host name/IP of the port manager.
    # @param port - The port on which the port manager itself is listening
    #               for connections.  By default this is 30000 but this can
    #               be overidden in non-standard configurations.
    # @throw various from socket and connect.
    #
    def __init__(self, host, port=30000):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    ##
    # getPort
    #   Given a service name returns a port from the connected port manager.
    #   On error, a RuntimError is raised, that is the error message
    #   from the server.
    #
    # @param service - The service we want to advertise.
    #
    # @return integer - The port that has been allocated.
    #
    # @throw RuntimeError - for errors from the port manager.
    # @throw other        - From socket operations.
    #
    def getPort(self, service):
        username = getpass.getuser()
        message = "GIMME %s %s\n" % (service, username)
        
        self.socket.sendall(bytearray(message, 'utf-8'))
        reply = self.socket.recv(10000)
        
        #  The reply should be  string of one of the following forms:
        #  *  OK 1234   (1234 the port allocated).
        #  *  FAIL {error message}
        #  In the second case, the connection to the server is closed and
        #  *  All ports we have acquired are released.
        #  *  This object becomes useless and should be destroyed.
        
        
        status = _tcl.call('lindex', reply, '0')
        data   = _tcl.call('lindex', reply, '1')
        
        if status == 'OK':
            return int(data)
        else:
            raise RuntimeError(data)
    ##
    # listPorts
    #    Produce a list of all the ports that are allocated on the
    #    system.
    #
    # @return list - each element of the list is a dict with the following
    #                keys:
    #                * port - Value is the port on which the service
    #                         is listening (integer)
    #                * service - Value is the name of the service.
    #                * user    - Value is the username for the service.
    #
    def listPorts(self):
        self.socket.sendall(bytearray("LIST\n", 'utf-8'))
        
        # We do the makefile so that we can use readline and do line based
        # processing.
        
        fd     = self.socket.makefile()
        info   = fd.readline()
        
        status = _tcl.call('lindex', info, 0)
        data   = _tcl.call('lindex', info, 1)
        result = []
        lines = int(data)
        for l in range(0, lines):
            l = fd.readline()
            port = int(_tcl.call('lindex', l, 0))
            serv = _tcl.call('lindex', l, 1)
            user = _tcl.call('lindex', l, 2)
            
            result.append({'port' : port, 'service': serv, 'user' : user})
        
        return result
    
    ##
    # find
    #   Produce a list of ports that match some set of criteria.
    #
    # @param **criteria - A dict of criteria that can be matched against.
    #                    this can be any set of:
    #                    * service    - Service exactly matches.
    #                    * beginswith - Service begins with a string
    #                      (e.g. 'a' matches 'a_1' too)
    #                    * user       - Service is advertised by the specified
    #                                   username.
    # @return list of maps as defined in listPorts above.
    #
    def find(self, **criteria):
        
        searchKeys = set(criteria.keys())
        legalKeys  = set(['service', 'beginswith', 'user'])
        badKeys    = searchKeys - legalKeys
        if len(badKeys) > 0:
            raise RuntimeError('Invalid search key(s) supplied to PortManager.find')
        
        # Strategy is to list te ports and filter them down as directed:
        
        ports = self.listPorts()
        
        #  If service is present filter for all those that match the filter:
        
        if 'service' in criteria.keys():
            svcname = criteria['service']
            ports = filter(lambda port: port['service'] == svcname, ports)
        
        
        # If beginswith is present, filter for all those whose services
        # match that.
        
        if 'beginswith' in criteria.keys():
            prefix = criteria['beginswith']
            ports  = filter(lambda port: port['service'][0:len(prefix)] == prefix, ports)
        
        # If user is present filter onthose services that  match the user:
        
        if 'user' in criteria.keys():
            user = criteria['user']
            ports = filter(lambda port: port['user'] == user, ports)
        
        return list(ports)
        
