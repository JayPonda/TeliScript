#!/bin/bash

source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate tenv

python ~/Personals/teliscript/main.py

conda deactivate