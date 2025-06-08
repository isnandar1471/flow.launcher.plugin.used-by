# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join
from sys import path

parent_folder_path = abspath(dirname(__file__))
path.append(parent_folder_path)
path.append(join(parent_folder_path, 'lib'))
path.append(join(parent_folder_path, 'plugin'))

from plugin import UsedBy

if __name__ == '__main__':
    UsedBy()
