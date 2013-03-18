#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

# This Class is an example of an Scheduler module
# Here for the configuration phase AND running one
"""
Write scheduler log in flat file
"""
import time
import datetime
import socket

from shinken.basemodule import BaseModule
from shinken.log import logger
from shinken.scheduler import Scheduler

properties = {
    'daemons': ['scheduler'],
    'type': 'send_socket_log',
    'external': False,
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("Get a Simple log broker for plugin %s" % plugin.get_name())
    # Catch errors
    instance = Send_socket_log(plugin)
    return instance


# Module write file log
# 
class Send_socket_log(BaseModule):

    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        
        
    def init(self):
        """
        Called by Scheduler to say 'let's prepare yourself guy'
        """
        logger.info("Initialization of the send_socket_log module")
        self.checkstemp_file={}
        
    def hook_get_socket_log(self, daemon):
        """
        main function that is called in the retention creation pass
        """
        logger.debug("[Send_socket_log] Get data ...")
        #name of local dict
        currentdict = self.checkstemp_file
        # temp dict lenght
        if currentdict == {}:
            self.temp_dict_lenght = 1
        if self.temp_dict_lenght == 0:
            self.temp_dict_lenght = 1
        if self.temp_dict_lenght > 1:
            self.temp_dict_lenght=max(currentdict.keys())
        # copy checks in checks_temp       
        for k,v in Scheduler.gchecks.items():
            if self.temp_dict_lenght > 1:
                self.temp_dict_lenght=max(currentdict.keys())
            self.temp_dict_lenght = self.temp_dict_lenght + 1
            currentdict.update({self.temp_dict_lenght:v})
        return True

    ## Should return if it succeed in the retention load or not
    def hook_send_socket_log(self, daemon):
        try:
            # Open the connexion
            rcvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rcvsocket.connect(('127.0.0.1', 1235))
        except IOError, exp:
            logger.error("Open file failed, %s" % str(exp))
            return
        logger.debug("Sending to socket")
        # local stats var and global reset
        nb_scheduled = 0
        nb_inpoller = 0
        nb_zombies = 0
        nb_checks_total = 0
        #time
        now = time.time()
        # number of poller
        a = len(Scheduler.gpollers)
        b = str(Scheduler.gpollers)
        x = 0
        # will get stats for each poller_tags
        try:
            while x < a:
                p = Scheduler.gpollers[x]['poller_tags']
                #decode unicode
                p=repr(p)
                p=p[3:-2]
                # start stats count
                for c in self.checkstemp_file.values():
                    if c.status == 'scheduled' and c.poller_tag == p:
                        nb_scheduled +=1
                    if c.status == 'inpoller' and c.poller_tag == p:
                        nb_inpoller +=1
                    if c.status == 'zombie' and c.poller_tag == p:
                        nb_zombies +=1
                    if c.poller_tag == p:
                        nb_checks_total += 1
                rcvsocket.send("%d %s Total check %s \n" % (now, p, nb_checks_total))        
                rcvsocket.send("%d %s nb_scheduled %s \n%d %s nb_inpoller %s \n%d %s nb_zombies %s \n" % (now, p, nb_scheduled, now, p, nb_inpoller, now, p, nb_zombies))
                #reset stats by poller
                nb_checks_total = 0
                nb_scheduled = 0
                nb_inpoller = 0
                nb_zombies = 0
                x = x+1 
        except IOError, e:
            if e.errno != 32:
                raise
        # clear temp dict
        self.checkstemp_file.clear()
        #return True
