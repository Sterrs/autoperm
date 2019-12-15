#!/usr/bin/env sh

# vim: ts=4 sw=0 sts=-1 et ai tw=80

# this whole enterprise is a dumb hack to do all the tests I want in one go, in
# a silly sort of home-brewed continuous integration way

set -eu

pylint_output=.pylint_output

# just hack PYTHONPATH into doing what I want. I have no idea what I'm doing,
# I've never seen a package before in my life
this_dir="$(realpath "$(dirname "$0")")"
cd "$this_dir"
export PYTHONPATH="$PYTHONPATH:$this_dir/autoperm"

for py_exe in pypy3 python3; do
    if >/dev/null 2>&1 command -v "$py_exe"; then
        py_cmd="$py_exe"
        break
    fi
done

if [ -z "$py_cmd" ]; then
    >&2 echo "No suitable Python executable found"
    exit
else
    echo "Running $py_cmd -m unittest..."
    "$py_cmd" -m unittest
fi

if >/dev/null 2>&1 command -v pylint; then
    echo "Linting..."
    # probably not POSIX, but this script is written exclusively for Arch
    # users so it's OK
    find . -name "*.py" -exec pylint --rcfile=.pylintrc {} + || true
    { find . -name "*.py" -exec pylint \
            --rcfile=.pylintrc --disable=fixme {} + || true; } \
    > "$pylint_output"
    if >/dev/null 2>&1 grep 'Your code has been rated at 10\.00/10' \
                            "$pylint_output"; then
        echo "OK - just fixmes"
    else
        >&2 echo "------------------------------------"
        >&2 echo "Please address the non-FIXME errors:"
        cat "$pylint_output"
        exit 1
    fi
else
    echo "Pylint not found"
fi

if >/dev/null 2>&1 command -v shellcheck; then
    echo "Linting shell scripts..."
    find . -name "*.sh" -exec shellcheck {} +
    echo "OK"
else
    echo "Shellcheck not found"
fi
