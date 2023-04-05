import os

print(os.system("pwd"))
# os.chdir("{{cookiecutter.project_name}}")
os.system("git init")
os.system("git submodule add -b {{cookiecutter.fprime_branch}} https://github.com/nasa/fprime.git")
