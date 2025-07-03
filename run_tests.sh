#!/bin/bash
set -e
echo "Current directory before cd: $(pwd)"
cd pm_system-main/project-management_system
echo "Current directory after cd: $(pwd)"
python -m unittest tests.test_project_startup
echo "Test execution finished."
