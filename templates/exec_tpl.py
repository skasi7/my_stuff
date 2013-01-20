#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
  <title>: <description>
  Authors = Rafael Treviño <skasi.7@gmail.com>
  Date = 
"""

# Imports externals

# Imports internals
from App import App


# Main entry point
if __name__ == '__main__':
  app = App('')
  # Exmaple of custom parameters
  # app.add_option('-c', dest='custom',
  #     help='custom parameter',
  #     default='')
  (params, args) = app.parse_args()
  
  # ...

