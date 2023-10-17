import numpy as np
import torch
import torch.nn.functional as F
from tqdm.auto import tqdm
from utils import Config
from torch.utils.tensorboard import SummaryWriter

from modules import Baseline
from dataset import ContrastiveDataset
from torch.utils.data import DataLoader, random_split

def main(model, train_loader, val_loader, criterion, optimizer, epochs):
    print('---------Train on: ' + Config.DEVICE + '----------')

    # Create model
    model = model.to(Config.DEVICE)
    best_score = 0
    writer = SummaryWriter(log_dir=Config.LOG_DIR)  # for TensorBoard

    for epoch in range(epochs):

        # train
        train_batch_loss, train_batch_acc = train(model, train_loader, optimizer, criterion, epoch, epochs)
        # validate
        val_batch_loss, val_batch_acc = validate(model, val_loader, criterion, epoch, epochs)

        if val_batch_acc > best_score:
            print(f"model improved: score {best_score:.5f} --> {val_batch_acc:.5f}")
            best_score = val_batch_acc
            # Save the best weights if the score is improved
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'train_loss': train_batch_loss,
                'val_acc': val_batch_acc
            }, Config.MODEL_DIR)
        else:
            print(f"no improvement: score {best_score:.5f} --> {val_batch_acc:.5f}")

        # Write loss and score to TensorBoard
        writer.add_scalar("Training Loss", train_batch_loss, epoch)
        writer.add_scalar("Training Score", train_batch_acc, epoch)
        writer.add_scalar("Validation Loss", val_batch_loss, epoch)
        writer.add_scalar("Validation Score", val_batch_acc, epoch)

    writer.close()


def train(model, train_loader, optimizer, criterion, epoch, epochs):
    model.train()
    train_loss_lis = np.array([])
    correct_predictions = 0
    total_samples = 0
    negative_pairs_below_margin = 0  # Count of negative pairs with distances below the margin
    total_negative_pairs = 0

    for batch in tqdm(train_loader):
        vols_1, vols_2, labels = batch['volume1'], batch['volume2'], batch['label']
        vols_1, vols_2, labels = vols_1.to(Config.DEVICE), vols_2.to(Config.DEVICE), labels.to(Config.DEVICE)

        optimizer.zero_grad()
        embedding_1, embedding_2 = model(vols_1, vols_2)
        loss = criterion(embedding_1, embedding_2, labels)
        loss.backward()
        optimizer.step()

        # Record the batch loss
        train_loss_lis = np.append(train_loss_lis, loss.item())

        # Compute pairwise distance using F.pairwise_distance
        dists = F.pairwise_distance(embedding_1, embedding_2)

        # Use the criterion's margin as the threshold for predictions
        threshold = criterion.margin
        predictions = (dists < threshold).float()
        correct_predictions += (predictions == labels.float()).sum().item()
        total_samples += labels.size(0)

        # Update the count of negative pairs below the margin
        negative_pair_mask = (labels == 0).float()  # 0 for negative pair
        total_negative_pairs += negative_pair_mask.sum().item()
        negative_dists_below_margin = (dists < criterion.margin).float() * negative_pair_mask
        negative_pairs_below_margin += negative_dists_below_margin.sum().item()

    train_loss = sum(train_loss_lis) / len(train_loss_lis)
    accuracy = correct_predictions / total_samples

    # Adjust the margin if too many negative pairs are below it
    proportion_negative_below_margin = negative_pairs_below_margin / (total_negative_pairs + 1e-10)
    if proportion_negative_below_margin > 0.3:  # Example threshold, adjust as needed
        criterion.margin *= 0.95  # Reduce the margin by 5%

    # Print the information.
    print(
        f"[ Train | {epoch + 1:03d}/{epochs:03d} ] margin = {criterion.margin}, acc = {accuracy:.5f}, loss = {train_loss:.5f}")
    return train_loss, accuracy


def validate(model, val_loader, criterion, epoch, epochs):
    model.eval()
    total_loss = 0.0
    correct_predictions = 0
    total_samples = 0

    with torch.no_grad():
        for batch in tqdm(val_loader):
            vols_1, vols_2, labels = batch['volume1'], batch['volume2'], batch['label']
            vols_1, vols_2, labels = vols_1.to(Config.DEVICE), vols_2.to(Config.DEVICE), labels.to(Config.DEVICE)
            embedding_1, embedding_2 = model(vols_1, vols_2)
            loss = criterion(embedding_1, embedding_2, labels)

            total_loss += loss.item()

            # Compute pairwise distance
            dists = F.pairwise_distance(embedding_1, embedding_2)
            threshold = criterion.margin
            predictions = (dists < threshold).float()
            correct_predictions += (predictions == labels.float()).sum().item()
            total_samples += labels.size(0)

    average_loss = total_loss / len(val_loader)
    val_acc = correct_predictions / total_samples

    # Print the information.
    print(
        f"[ Validation | {epoch + 1:03d}/{epochs:03d} ] margin = {criterion.margin:.5f}, acc = {val_acc:.5f}, loss = {average_loss:.5f}")

    return average_loss, val_acc


class ContrastiveLoss(torch.nn.Module):
    def __init__(self, margin=2.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin  # margin specifies how far apart the embeddings of dissimilar pairs should be

    def forward(self, embedding1, embedding2, label):
        euclidean_distance = F.pairwise_distance(embedding1, embedding2)
        loss_contrastive = torch.mean((1 - label) * torch.pow(euclidean_distance, 2) +
                                      label * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2))
        return loss_contrastive


if __name__ == '__main__':
    model = Baseline()

    full_train_dataset = ContrastiveDataset(Config.TRAIN_DIR)
    # Split the full training dataset into train and val sets
    train_size = int(0.8 * len(full_train_dataset))
    val_size = len(full_train_dataset) - train_size
    dataset_tr, dataset_val = random_split(full_train_dataset, [train_size, val_size])

    dataloader_tr = DataLoader(
        dataset=dataset_tr,
        shuffle=True,
        batch_size=3,
        num_workers=1,
        drop_last=True
    )
    dataloader_val = DataLoader(
        dataset=dataset_val,
        shuffle=True,
        batch_size=3,
        num_workers=1,
        drop_last=True
    )

    criterion = ContrastiveLoss()

    lr = 0.005
    weight_decay = 1e-5
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    epochs = 50

    main(model, dataloader_tr, dataloader_val, criterion, optimizer, epochs)




"""
# test
if __name__ == '__main__':
    model = Baseline()


    def generate_random_tensors(channels, height, width):
        return torch.rand(channels, height, width)

    # Generate random tensors with the desired shape
    random_batch_size = 3
    random_channels = 20
    random_height = 256
    random_width = 240
    random_input1 = generate_random_tensors(random_channels, random_height, random_width)
    random_input2 = generate_random_tensors(random_channels, random_height, random_width)
    random_labels = torch.randint(0, 2, (3, 1))

    random_dataset = [{'volume1': random_input1,
                       'volume2': random_input2,
                       'label': label} for label in random_labels]
    dataloader = DataLoader(
        dataset=random_dataset,
        shuffle=True,
        batch_size=3,
        num_workers=1,
        drop_last=True
    )
    
    criterion = ContrastiveLoss()

    lr = 0.005
    weight_decay = 1e-5
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    epochs = 5

    main(model, dataloader, dataloader, criterion, optimizer, epochs)
"""
