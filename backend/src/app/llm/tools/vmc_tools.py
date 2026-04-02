import pandas as pd
from langchain_core.tools import tool


@tool
def summarize_vmc_csv(path: str) -> str:
    """
    Load a VMC training CSV and return basic info (columns, row count,
    and a simple energy summary if available).

    TODO: extend this with real physics analysis (Hubbard / TFIM convergence).
    """
    df = pd.read_csv(path)
    info = {
        "path": path,
        "columns": list(df.columns),
        "num_rows": int(len(df)),
    }

    if {"epoch", "Energy_Re"}.issubset(df.columns):
        tail = df.tail(200)
        info["mean_energy_last_200"] = float(tail["Energy_Re"].mean())

    return str(info)
