'''test_cellprofiler - test the CellProfiler command-line interface

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2014 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''

import datetime
import dateutil.parser
import os
import unittest
from cStringIO import StringIO
import shutil
import subprocess
import sys
import tempfile
from cellprofiler.modules.tests import \
     example_images_directory, maybe_download_example_images

import CellProfiler

if hasattr(sys, 'frozen'):
    ARGLIST_START = ["CellProfiler.py"]
else:
    ARGLIST_START = ["CellProfiler.py", "-b"]

class TestCellProfiler(unittest.TestCase):
    def test_01_01_html(self):
        path = tempfile.mkdtemp()
        try:
            CellProfiler.main(ARGLIST_START + ["--html","-o",path])
            filenames = os.listdir(path)
            self.assertTrue("index.html" in filenames)
        finally:
            shutil.rmtree(path)
            
    def test_01_02_code_statistics(self):
        old_stdout = sys.stdout
        fake_stdout = StringIO()
        sys.stdout = fake_stdout
        try:
            CellProfiler.main(ARGLIST_START + ["--code-statistics"])
        finally:
            sys.stdout = old_stdout
        fake_stdout.seek(0)
        found_module_stats = False
        found_setting_stats = False
        found_lines_of_code = False
        for line in fake_stdout.readlines():
            if line.startswith("# of built-in modules"):
                found_module_stats = True
            elif line.startswith("# of settings"):
                found_setting_stats = True
            elif line.startswith("# of lines of code"):
                found_lines_of_code = True
        self.assertTrue(found_module_stats)
        self.assertTrue(found_setting_stats)
        self.assertTrue(found_lines_of_code)
        
    def test_01_03_version(self):
        import cellprofiler.utilities.version as V
        if hasattr(sys, "frozen"):
            args = [sys.argv[0], "--version"]
            output = subprocess.check_output(args)
        else:
            test_dir = os.path.dirname(__file__)
            cellprofiler_dir = os.path.dirname(test_dir)
            root_dir = os.path.dirname(cellprofiler_dir)
            self.assertTrue(os.path.isfile(os.path.join(
                root_dir, "CellProfiler.py")))
            args = [sys.executable, "CellProfiler.py", "--version"]
            output = subprocess.check_output(args, cwd=root_dir)
        output = subprocess.check_output(args)
        version = dict([tuple(line.strip().split(" "))
                        for line in output.split("\n")
                        if " " in line])
        self.assertEqual(version["CellProfiler"], V.dotted_version)
        self.assertEqual(version["Git"], V.git_hash)
        self.assertEqual(int(version["Version"][:8]), 
                         int(V.version_number / 1000000))
        built = dateutil.parser.parse(version["Built"])
        self.assertLess(built.date(), datetime.date.today())
        
    def test_02_01_run_headless(self):
        output_directory = tempfile.mkdtemp()
        temp_directory = os.path.join(output_directory, "temp")
        os.mkdir(temp_directory)
        try:
            #
            # Run with a .cp file
            #
            input_directory = maybe_download_example_images(
                ["ExampleHT29"],
                ['AS_09125_050116030001_D03f00d0.tif', 
                 'AS_09125_050116030001_D03f00d1.tif', 
                 'AS_09125_050116030001_D03f00d2.tif', 
                 'ExampleHT29.cp', 'k27IllumCorrControlv1.mat'])
            pipeline_file = os.path.join(input_directory, "ExampleHT29.cp")
            measurements_file = os.path.join(output_directory, "Measurements.h5")
            done_file = os.path.join(output_directory, "Done.txt")
            args = ARGLIST_START + ["-c", "-r", 
                                    "-i", input_directory,
                                    "-o", output_directory,
                                    "-p", pipeline_file,
                                    "-d", done_file,
                                    "-t", temp_directory,
                                    measurements_file]
            CellProfiler.main(args)
            import cellprofiler.preferences as cpprefs
            self.assertTrue(os.path.exists(measurements_file))
            self.assertTrue(os.path.exists(done_file))
            self.assertEqual(temp_directory, cpprefs.get_temporary_directory())
            #
            # Re-run using the measurements file.
            #
            m2_file = os.path.join(output_directory, "M2.h5")
            args = ARGLIST_START + ["-c", "-r", 
                                    "-i", input_directory,
                                    "-o", output_directory,
                                    "-p", measurements_file,
                                    m2_file]
            CellProfiler.main(args)
            self.assertTrue(os.path.exists(m2_file))
        finally:
            shutil.rmtree(output_directory)
            
