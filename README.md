# fprime-tools

A package containing tools to work with F´. Installation can be done using:

```
pip install fprime-tools
```

See also: https://nasa.github.io/fprime to see the F´ framework.

## Developer Installation

In order to install a branch not released on PIP, follow these steps:

1. Clone this repo or the developer fork containing the desired branch
2. Checkout the desired branch
3. Remove previous installation with `pip uninstall fprime-tools`
4. Install local checkout with `pip install .`

Developers can add the `-e` flag when local changes need to affect the tool install immediately.  `-e` links the current directory into the PIP
install rather than copying the files over thus allowing local edits to affect the installed tools. This is commonly done during the development cycle.

**Installing `devel`**

These instructions will install the devel branch without allowing local edits to affect the installation.

```
git clone https://github.com/fprime-community/fprime-tools.git
cd fprime-tools
git checkout devel
pip uninstall fprime-tools
pip install .
```


## Black Formatter

To automatically format code, the Black Formatter can be installed with:
```pip install black```

Then it can be run on the project using:
```
black ./
```
