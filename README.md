# Zeta_Question3 : Banking API

**FastAPI** service for debiting an account and concurrent safety. 

## Structure
- `src/main.py`        — Load artifacts, expose `POST /accounts/{account_id}/debit`

## Quickstart

```bash
# 1. Clone & cd
git clone https://github.com/diyaverma1967/Zeta_Question3.git
cd Zeta_Question3

# 2. Set up Conda env
conda create -n Zeta_Question3 python=3.11 -y
conda activate Zeta_Question3

# 3. Start API
uvicorn src.main:app --reload
