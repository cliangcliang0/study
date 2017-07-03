#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 在 Burp 中利用 Bing 服务

from burp import IBurpExtender
from burp import IContextMenuFactory

from javax.swing import JMenuItem
from java.util import List, ArrayList
from java.net import URL

import socket
import urllib
import json
import re
import base64
import threading

# https://azure.microsoft.com/zh-tw/marketplace/partners/bing/search/
# https://datamarket.azure.com/account/keys
bing_api_key = "KEY"

class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None

        # We set up our extension
        callbacks.setExtensionName("BHP Bing")
        callbacks.registerContextMenuFactory(self)

        return

    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Send to Bing", actionPerformed=self.bing_menu))

        return menu_list

    def bing_menu(self,event):
        # Grab the details of what the user clicked
        http_traffic = self.context.getSelectedMessages()
        print "%d requests highlighted" % len(http_traffic)

        for traffic in http_traffic:
            http_service = traffic.getHttpService()
            host = http_service.getHost()
            print "User selected host: %s" % host
            self.bing_search(host)
        return

    def bing_search(self, host):
        # Check if we have an IP or hostname
        is_ip = re.match("[0-9]+(?:\.[0-9]+){3}", host)
        
        if is_ip:
            ip_address = host
            domain = False
        else:
            ip_address = socket.gethostbyname(host)
            domain = True

        bing_query_string = "'ip:%s'" % ip_address
        thread = threading.Thread(target=self.bing_query, args=(bing_query_string,))
        thread.start()
        
        if domain:
            bing_query_string = "'domain:%s'" % host
            thread = threading.Thread(target=self.bing_query, args=(bing_query_string,))
            thread.start()
    
    def bing_query(self, bing_query_string): 
        print "Performing Bing search: %s" % bing_query_string
        
        # Encode our query
        quoted_query = urllib.quote(bing_query_string)
        
        http_request = "GET https://api.datamarket.azure.com/Bing/Search/Web?$format=json&$top=20&Query=%s HTTP/1.1\r\n" % quoted_query
        http_request += "Host: api.datamarket.azure.com\r\n"
        http_request += "Connection: close\r\n"
        http_request += "Authorization: Basic %s\r\n" % base64.b64encode(":%s" % bing_api_key)
        http_request += "User-Agent: Blackhat Python\r\n\r\n"
        
        json_body = self._callbacks.makeHttpRequest("api.datamarket.azure.com", 443, True, http_request).tostring()
        json_body = json_body.split("\r\n\r\n", 1)[1]
        
        try:
            r = json.loads(json_body)
        
            if len(r["d"]["results"]):
                for site in r["d"]["results"]:
                    print "*" * 100
                    print site['Title']
                    print site['Url']
                    print site['Description']
                    print "*" * 100
                    j_url = URL(site['Url'])
              
                    if not self._callbacks.isInScope(j_url):
                        print "Adding to Burp scope"
                        self._callbacks.includeInScope(j_url)
        except:
            print "No results from Bing"
            pass
        
        return