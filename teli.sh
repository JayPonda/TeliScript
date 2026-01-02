#!/bin/bash

cd ~/Personals/teliscript/TeliBelly/server

source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate tenv

python main.py

conda deactivate