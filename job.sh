#! /bin/bash

set -x
cd examples
HYDRA_FULL_ERROR=1 python3 train_u2s.py u2s=xvector u2s/datamodule=wisteria_xvector
