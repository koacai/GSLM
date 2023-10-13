from lightning.pytorch import LightningDataModule
from lightning.pytorch.utilities.types import EVAL_DATALOADERS
from omegaconf import DictConfig
from torch.utils.data import DataLoader
from torch.nn.utils.rnn import pad_sequence
import random
import torch
import hydra


class u2sDataModule(LightningDataModule):
    def __init__(self,cfg:DictConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.train_dataset = hydra.utils.instantiate(
            self.cfg.train_dataset
        )
        self.val_dataset = hydra.utils.instantiate(
            self.cfg.val_dataset
        )

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.cfg.data.train_batch_size,
            collate_fn=lambda batch: self.collate_fn(
                batch, self.cfg.data.segment_size.train
            ),
            num_workers=20,
        )
    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.cfg.data.val_batch_size,
            collate_fn=lambda batch: self.collate_fn(
                batch, self.cfg.data.segment_size.val
            ),
            num_workers=20,
        )
    @torch.no_grad()
    def collate_fn(self, batch, segment_size: int = -1):
        batch = [
            {
                'resampled_speech.pth': b[0],
                'input_feature': b[1],
                '__key__': b[2],
            } for b in batch
        ]

        outputs = dict()
        if segment_size != -1:
            cropped_speeches = []
            input_features = []
            for sample in batch:
                wav = sample["resampled_speech.pth"]
                input_feature= sample[self.cfg.data.target_feature.key]
                feature_len = input_feature.size(0)
                if feature_len > (segment_size+1):
                    feature_start = random.randint(
                        0, feature_len - segment_size - 1
                    )
                    feature_end = segment_size + feature_start
                    speech_start_sec = feature_start / self.cfg.data.target_feature.samples_per_sec + self.cfg.data.target_feature.bias
                    speech_end_sec = (feature_start + segment_size) / self.cfg.data.target_feature.samples_per_sec + self.cfg.data.target_feature.bias
                    cropped_speeches.append(
                        wav.squeeze()[
                            int(speech_start_sec * self.cfg.sample_rate) : int(speech_end_sec * self.cfg.sample_rate)
                        ]
                    )
                    input_features.append(
                        input_feature[
                            feature_start:feature_end
                        ]
                    )
                else:
                    cropped_speeches.append(wav.squeeze())
                    input_features.append(
                        input_feature
                    )
            outputs["resampled_speech.pth"] = pad_sequence(
                cropped_speeches, batch_first=True
            )
            outputs["input_feature"] = pad_sequence(
                input_features, batch_first=True
            )
        else:
            outputs["resampled_speech.pth"] = pad_sequence(
                [b["resampled_speech.pth"].squeeze() for b in batch], batch_first=True
            )
            outputs["input_feature"] = pad_sequence(
                [b["input_feature"] for b in batch], batch_first=True
            )
        
        outputs["wav_lens"] = torch.tensor(
            [b["resampled_speech.pth"].size(0) for b in batch]
        )

        outputs["filenames"] = [b["__key__"] for b in batch]
        return outputs