#! /bin/bash
#PJM -L rscgrp=share
#PJM -L gpu=1
#PJM -g ge43
#PJM -j
set -x
source /etc/profile.d/modules.sh
module load gcc/12.2.0
module load cuda/12.1
source .venv/bin/activate

ratarmount ~/fairseq/corpus/hq-youtube.tar /dev/shm/hq-youtube_mount
cd examples
HYDRA_FULL_ERROR=1 python3 train_u2s.py u2s=xvector u2s/datamodule=wisteria_xvector.yaml
