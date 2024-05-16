#File: speedy/imports_ds.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except:
    pass
__all__ = ['pd', 'np', 'plt', 'torch', 'nn', 'F']
# print('Imported pd, np, plt, torch, nn, F, glob')