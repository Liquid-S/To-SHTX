# -*- coding: utf-8 -*-

################################################################################
# Copyright © 2016-2017 Yukinogatari
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To But It's Not My Fault Public
# License, Version 1, as published by Ben McGinnes. See the COPYING file
# for more details.
################################################################################

import os
import math
import shutil

from PyQt4 import QtGui, Qt
from PyQt4.QtGui import QImage, qRed, qGreen, qBlue, qAlpha
from PyQt4.QtCore import QProcess, QString

from util import *

WORKING_DIR = os.path.dirname(os.path.realpath(__file__))

SHTX_MAGIC   = "SHTX"
SHTXFS_MAGIC = "SHTXFS"
TEMP_FILE    = os.path.join(WORKING_DIR, "_temp.png")
QUANT_PATH   = os.path.join(WORKING_DIR, "pngquant")

def to_shtx(filename, out_file = None):
  
  if out_file == None:
    out_file = os.path.splitext(filename)[0] + ".btx"
  
  try:
    os.makedirs(TEMP_DIR)
  except:
    pass
  
  # Convert to indexed.
  process = QProcess()
  options = ["--force", "--speed", "1", "256", "--output", TEMP_FILE, filename]
  process.start(QUANT_PATH, options)
  process.waitForFinished(-1)
  
  # If it didn't output anything, the image is already indexed.
  if not os.path.isfile(TEMP_FILE):
    temp_file = filename
  else:
    temp_file = TEMP_FILE
  
  img = QImage(temp_file)
  
  if not img.format() == QImage.Format_Indexed8:
    print "Couldn't convert image to indexed."
    return False
  
  if img.colorCount() <= 16:
    data = to_shtx_4bit(img)
  
  else:
    data = to_shtx_8bit(img)
  
  if os.path.isfile(TEMP_FILE):
    os.remove(TEMP_FILE)
  
  if data:
    with open(out_file, "wb") as f:
      f.write(data)
  
    return True
  
  return False

def to_shtx_8bit(img):
  
  data = bytearray(SHTXFS_MAGIC)
  
  width  = img.width()
  height = img.height()
  
  data.extend(from_u16(width))
  data.extend(from_u16(height))
  data.append(int(math.ceil(math.log(width, 2))))
  data.append(int(math.ceil(math.log(height, 2))))
  
  pal = img.colorTable()
  if len(pal) < 256:
    pal.extend([0] * (256 - len(pal)))
  
  for color in pal:
    data.append(qRed(color))
    data.append(qGreen(color))
    data.append(qBlue(color))
    data.append(qAlpha(color))
  
  data.extend(img.constBits().asstring(width * height))
  
  return data

def to_shtx_4bit(img):
  
  data = bytearray(SHTX_MAGIC)
  
  width  = img.width()
  height = img.height()
  
  data.extend(from_u16(width))
  data.extend(from_u16(height))
  data.extend("\x04\x00\x10\x00\x00\x00\x00\x00") # ???
  
  pal = img.colorTable()
  if len(pal) < 16:
    pal.extend([0] * (16 - len(pal)))
  
  for color in pal:
    data.append(qRed(color))
    data.append(qGreen(color))
    data.append(qBlue(color))
    data.append(qAlpha(color))
  
  pixels = bytearray(img.constBits().asstring(width * height))
  
  for i in range(0, len(pixels), 2):
    b1, b2 = pixels[i : i + 2]
    b = b1 | (b2 << 4)
    data.append(b)
  
  return data
  
if __name__ == "__main__":
  import argparse
  
  print
  print "**********************************************"
  print "* SHTX converter, written by Yukinogatari.    "
  print "**********************************************"
  print
  
  parser = argparse.ArgumentParser(description = "Convert PNG images to SHTX/FS.")
  parser.add_argument("input", metavar = "<input file|dir>", nargs = "+", help = "An input file or directory.")
  parser.add_argument("-o", "--output", metavar = "<output dir>", help = "The output directory.")
  args = parser.parse_args()
  
  for in_path in args.input:
    
    if os.path.isdir(in_path):
      base_dir = os.path.normpath(in_path)
      files = list_all_files(base_dir)
    elif os.path.isfile(in_path):
      base_dir = os.path.dirname(in_path)
      files = [in_path]
    else:
      continue
    
    if args.output:
      out_dir = os.path.normpath(args.output)
    else:
      out_dir = base_dir
  
    for filename in files:
      if not os.path.splitext(filename)[1].lower() == ".png":
        continue
      
      out_file = os.path.join(out_dir, filename[len(base_dir) + 1:] if base_dir else filename)
      out_file = os.path.splitext(out_file)[0] + ".btx"
      
      try:
        if to_shtx(filename, out_file):
          print filename
          print " -->", out_file
          print
      
      except:
        # print "Failed to convert", filename
        raise
  
  print
  raw_input("Press Enter to exit.")

### EOF ###