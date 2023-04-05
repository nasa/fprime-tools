import os

# os.chdir("{{cookiecutter.project_name}}")

# Adding F' as a submodule
os.system("git init")
os.system("git submodule add -b {{cookiecutter.fprime_branch}} https://github.com/nasa/fprime.git")


print("""

###########################################################
Congrats!!! You have successfully created a new F' project!

Next recommended steps:

-- OPTIONAL: Select your F' version --
cd fprime
git checkout tags/vX.X.X


-- Generate a new component --
fprime-util new --component

-- Generate a new deployment --
fprime-util new --deployment
fprime-util generate
fprime-util build

""")
