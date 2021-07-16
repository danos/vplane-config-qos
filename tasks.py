#!/usr/bin/env python3
# Copyright (c) 2021, AT&T Intellectual Property. All rights reserved.
# SPDX-License-Identifier: GPL-2.0-only

import sys
import re
import subprocess
import datetime
from typing import List
import magic
from invoke import task
from invoke import Collection

# ***************************************************
# Helper functions used by multiple stages
# ***************************************************


def get_files_by_types(files: List, types: List[str]) -> List:
    """Return a subset of 'files' based of the file type. Use python-magic rather simply
        looking at the file extension because some of the scripts do not have any file extension"""

    files_by_types = []
    for file in files:
        file_type = magic.from_file(file)
        if any(specified_type in file_type for specified_type in types):
            files_by_types.append(file)
        # python-magic does not recognise yang files so find them using their file extension
        else:
            if "Yang" in types:
                file_extension = file.split('.').pop()
                if file_extension == "yang":
                    files_by_types.append(file)

    return files_by_types


def get_all_files() -> List:
    """Return every file in this repository"""

    all_files = []
    # TODO: get all files
    return all_files


def get_changed_files(commits: str) -> List:
    """Return all the files that have changed"""

    git_command = f"git diff --diff-filter=rd --find-renames=100% --name-only --format=format:'' {commits}"
    result = subprocess.check_output(git_command, shell=True).decode("utf-8")
    changed_files = result.splitlines()

    print(f"Files to check {changed_files}\n")
    return changed_files

# ***************************************************
# Stages of the pipeline
# ***************************************************


@task
def licence(context, commits="master...HEAD"):
    """Check all source code files contain an up to date version of the AT&T licence and
        the spdx licence."""

    def check_att_licence(source_files: List[str]) -> bool:
        for file in source_files:
            year = datetime.datetime.now().year
            pattern = rf"Copyright \(c\) .*{year}.* AT&T Intellectual Property"
            error = False

            with open(file) as f:
                for line in f:
                    match = re.search(pattern, line)
                    if match:
                        break
                else:
                    print(f"Failed: File {file} does not contain AT&T licence for the current year ({year})")
                    error = True
        return error

    def check_spdx_licence(source_files: List[str]) -> bool:
        error = False
        for file in source_files:
            pattern = r"SPDX-License-Identifier:"
            with open(file) as f:
                if pattern not in f.read():
                    print(f"Failed: File {file} does not contain SPDX licence")
                    error = True
        return error

    files = get_changed_files(commits)
    code_files = get_files_by_types(files, ["Python", "Perl", "Bourne-Again shell", "Yang"])
    att_error = check_att_licence(code_files)
    spdx_error = check_spdx_licence(code_files)
    if att_error or spdx_error:
        return True
    return False


@task
def yang(context, commits="master...HEAD"):
    """Run dram and check yang address"""
    def check_yang_address(yang_files: List[str]) -> bool:

        pattern = r"Postal: 208 S\. Akard Street\n\s*Dallas\, TX 75202, USA\n\s*Web: www.att.com"
        error = False
        for file in yang_files:
            with open(file) as f:
                yang = f.read()
                match = re.search(pattern, yang)
                if not match:
                    print(f"Failed: Yang file {file} does not contain correct address")
                    error = True
        return error

    # TODO: if invoked via jenkins for PR, then raise dram request and post link on PR page
    def run_dram(yang_files: List[str]) -> bool:

        filenames = []
        platform_yang = []

        # TODO: seperate yang files into different folders, eg. platform folder, deviation folder, etc
        for file in yang_files:
            if "deviation" in file:
                platform_yang.append(file)
            else:
                filenames.append(file)

        filenames = ",".join(filenames)
        platform_yang = ",".join(platform_yang)

        dram_command = "dram --username jenkins --suppress"
        if filenames:
            dram_command += f" --filenames {filenames}"
        if platform_yang:
            dram_command += f"--platform-yang {platform_yang}"

        return context.run(dram_command, echo=True)

    files = get_changed_files(commits)
    yang_files = get_files_by_types(files, ["Yang"])
    # If there are no yang changes then can skip this
    if yang_files:
        addr_error = check_yang_address(yang_files)
        dram_error = run_dram(yang_files)
        if addr_error or dram_error:
            return True
    return False


@task
def flake8(context, commits="master...HEAD"):
    """Run flake8 over changed files"""
    files = get_changed_files(commits)
    python_files = get_files_by_types(files, ["Python"])
    if python_files:  # Only run flake8 if there are files to check (otherwise it will run it over the directory)
        python_files = " ".join(python_files)
        return context.run(f"python3 -m flake8 --count {python_files}", echo=True)

@task
def mypy(context, commits="master...HEAD"):
    """Run python static type checker"""
    files = get_changed_files(commits)
    python_files = get_files_by_types(files, ["Python"])
    if python_files:  # Only run mypy if there are files to check (otherwise it will run it over the directory)
        python_files = " ".join(python_files)
        return context.run(f"mypy {python_files}", echo=True)

@task
def pytest(context):
    """Run the unit test suite"""
    return context.run("coverage run --source . -m pytest", echo=True)

@task(pre=[pytest])
def coverage(context):
    """Run the unit test suite"""
    context.run("coverage html", echo=True)
    return context.run("coverage report", echo=True)


@task
def gitlint(context, commits="master...HEAD"):
    """Run the unit test suite"""
    # context.run() fails for gitlint. Possibly because of https://github.com/fabric/fabric/issues/1812
    # So invoke gitlint using subprocess.run rather than invokes context.run
    command = f"gitlint --commits {commits}"
    print(f"Running: {command}", flush=True)
    output = subprocess.run(command, shell=True)
    if output.returncode:
        sys.exit(output.returncode)

@task(pre=[licence, pytest, flake8, gitlint, yang])
def all(context, commits="master...HEAD"):
    """Run all stages in the pipeline. Use invoke pre tasks to invoke all stages"""
    pass
