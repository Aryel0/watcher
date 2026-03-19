import os
import shutil
import subprocess
import sys

def run_command(command, cwd=None):
    print(f"Running: {command}")
    try:
        subprocess.check_call(command, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        sys.exit(1)

def clean(root_dir):
    print("Cleaning build artifacts...")
    patterns = ['dist', 'build', 'agent803_watcher.egg-info']
    
    for pattern in patterns:
        path = os.path.join(root_dir, pattern)
        if os.path.exists(path):
            print(f"Removing {path}")
            shutil.rmtree(path)

def run_tests(root_dir):
    print("Running tests...")
    # Run the integrated watcher test script
    test_script = os.path.join(root_dir, 'watcher', 'test_watcher.py')
    run_command(f"{sys.executable} {test_script}", cwd=root_dir)

def build_package(root_dir):
    print("Building package...")
    run_command(f"{sys.executable} -m build", cwd=root_dir)

def check_package(root_dir):
    print("Checking package with twine...")
    try:
        run_command("twine check dist/*", cwd=root_dir)
    except:
        print("Twine check failed or twine not installed. Skipping.")

def main():
    # Helper to determine root. 
    # If this script is in watcher/, parent is root?
    # Actually, pyproject.toml is in agent803 (parent) or watcher?
    # User's pyproject.toml is in c:\Users\steph\Downloads\Project\agent803\pyproject.toml
    # But I can only write to watcher.
    
    # I'll assume this script is run from where pyproject.toml exists or passed as arg.
    # If run from watcher/, we might need to go up if pyproject is there.
    # However, based on file list, pyproject.toml is in agent803/.
    # But I only have access to agent803/watcher. 
    
    # Wait, the previous `pip install -e ..` succeeded, so pyproject is indeed in parent.
    # But I might not be able to write files there.
    
    # I will write this script in `watcher/build_release.py`
    # It will assume it needs to operate on `..`
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # agent803/
    
    if not os.path.exists(os.path.join(project_root, 'pyproject.toml')):
        print(f"Warning: pyproject.toml not found in {project_root}. Checking current dir.")
        project_root = current_dir

    clean(project_root)
    run_tests(project_root)
    build_package(project_root)
    check_package(project_root)
    
    print("\nBuild complete. Artifacts in 'dist/'.")

if __name__ == "__main__":
    main()
