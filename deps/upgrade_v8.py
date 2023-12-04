#!/usr/bin/env python

import urllib.request
import sys
import json
import subprocess
import os
import fnmatch
import pathlib
import shutil

vendor_file_template = """// Generated by deps/upgrade_v8.py, DO NOT REMOVE/EDIT MANUALLY.
// Package %s is required to provide support for vendoring modules
package %s
"""

include_vendor_file_template = """// Generated by deps/upgrade_v8.py, DO NOT REMOVE/EDIT MANUALLY.
// Package include is required to provide support for vendoring modules
package include

import (
	%s
)
"""

CHROME_VERSIONS_URL = "https://chromiumdash.appspot.com/all.json?os=linux&channel=stable"
V8_VERSION_FILE = "v8_version"

deps_path = os.path.dirname(os.path.realpath(__file__))
v8go_path = os.path.abspath(os.path.join(deps_path, os.pardir))
env = os.environ.copy()
v8_path = os.path.join(deps_path, "v8")
v8_include_path = os.path.join(v8_path, "include")
deps_include_path = os.path.join(deps_path, "include")

def get_directories_names(path):
  flist = []
  for p in pathlib.Path(path).iterdir():
    if p.is_dir():
        flist.append(p.name)
  return sorted(flist)

def package_name(package, index, total):
  name = f'_ "rogchap.com/v8go/deps/include/{package}"'
  if (index + 1 == total):
    return name
  else:
    return name + '\n'

def create_include_vendor_file(src_path, directories):
  package_names = []
  total_directories = len(directories)

  for index, directory_name in enumerate(directories):
    package_names.append(package_name(directory_name, index, total_directories))

  with open(os.path.join(src_path, 'vendor.go'), 'w') as temp_file:
      temp_file.write(include_vendor_file_template % ('  '.join(package_names)))

def create_vendor_files(src_path):
  directories = get_directories_names(src_path)

  create_include_vendor_file(src_path, directories)

  for directory in directories:
    directory_path = os.path.join(src_path, directory)

    vendor_go_file_path = os.path.join(directory_path, 'vendor.go')

    if os.path.isfile(vendor_go_file_path):
      continue

    with open(os.path.join(directory_path, 'vendor.go'), 'w') as temp_file:
      temp_file.write(vendor_file_template % (directory, directory))

def update_v8_version_file(src_path, version):
  with open(os.path.join(src_path, V8_VERSION_FILE), "w") as v8_file:
    v8_file.write(version)

def read_v8_version_file(src_path):
  v8_version_file = open(os.path.join(src_path, V8_VERSION_FILE), "r")
  return v8_version_file.read().strip()

def get_latest_v8_info():
  with urllib.request.urlopen(CHROME_VERSIONS_URL) as response:
   json_response = response.read()

  return json.loads(json_response)

# Current version
current_v8_version_installed = read_v8_version_file(deps_path)

# Get latest version
latest_v8_info = get_latest_v8_info()

latest_stable_v8_version = latest_v8_info[0]["versions"][0]["v8_version"]

if current_v8_version_installed != latest_stable_v8_version:
  subprocess.check_call(["git", "fetch", "origin", latest_stable_v8_version],
                        cwd=v8_path,
                        env=env)
  # checkout latest stable commit
  subprocess.check_call(["git", "checkout", latest_stable_v8_version],
                        cwd=v8_path,
                        env=env)

  shutil.rmtree(deps_include_path)
  shutil.copytree(v8_include_path, deps_include_path, dirs_exist_ok=True)
  create_vendor_files(deps_include_path)
  update_v8_version_file(deps_path, latest_stable_v8_version)
