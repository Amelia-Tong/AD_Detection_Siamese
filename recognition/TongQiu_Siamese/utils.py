import torch
from pathlib import Path


class Config:

    # # run on local machine
    # TRAIN_DIR = Path("/Users/tongqiu/Desktop/COMP3710_Report/AD_NC/train")
    # TEST_DIR = Path("/Users/tongqiu/Desktop/COMP3710_Report/AD_NC/test")
    # DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
    # LOG_DIR = Path("/Users/tongqiu/Desktop/COMP3710_Report/log/Contrastive_0")
    # MODEL_DIR = "/Users/tongqiu/Desktop/COMP3710_Report/Contrastive_0.pth"

    # # run on Rangepur
    # TRAIN_DIR = Path("~/comp3710/report/AD_NC/train")
    # TEST_DIR = Path("~/comp3710/report/AD_NC/test")
    # DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    # LOG_DIR = Path("~/comp3710/report/log/Contrastive_0")
    # MODEL_DIR = "~/comp3710/report/model/Contrastive_0.pth"

    # colab
    TRAIN_DIR = Path("/content/drive/MyDrive/Colab_Notebooks/COMP_3710/Siamese/AD_NC/train")
    TEST_DIR = Path("/content/drive/MyDrive/Colab_Notebooks/COMP_3710/Siamese/AD_NC/test")
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    LOG_DIR = Path("/content/drive/MyDrive/Colab_Notebooks/COMP_3710/Siamese/log/Contrastive_0")
    MODEL_DIR = "/content/drive/MyDrive/Colab_Notebooks/COMP_3710/Siamese/Contrastive_0.pth"




