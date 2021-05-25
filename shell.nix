# Copyright (c) 2021, Cisco Systems, Inc. and/or its affiliates
# Licensed under the MIT License, see the "LICENSE" file accompanying this file.

# This Nix shell configuration can be safely ignored by non-Nix users, it is just used to stabilize a local testing
# environment and automate various chores.
{ pkgs ? import <nixpkgs> { }, python ? pkgs.python39 }:
let
  python-env = python.withPackages
    (py: [ py.flake8 py.pip py.requests py.setuptools py.urllib3 ]);
in pkgs.mkShell {
  name = "orbital-api-shell";
  nativeBuildInputs = [ python-env ];
}
