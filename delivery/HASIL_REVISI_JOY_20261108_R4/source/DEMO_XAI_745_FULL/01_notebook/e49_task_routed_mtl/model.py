"""E49: Task-Routed Multi-Gate Mixture of Experts (MMoE) Joint MTL Model.

Single joint graph for Task 1, Task 2, and Task 3:
- Shared multimodal input: CLIP visual (1536) + IndoBERT text (768) = 2304 dim
- Shared expert networks (E experts)
- Task-specific softmax gating networks
- Dedicated task-specific towers
- Joint optimization with positive task loss weights
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

TASKS = ('task1_issue', 'task2_domain_sumber', 'task3_primary_entity_type')

@dataclass
class E49Config:
    num_experts: int = 4
    expert_hidden: int = 192
    tower_dim: int = 96
    dropout: float = 0.2
    visual_scale: float = 1.5
    text_scale: float = 1.0
    lr: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 60
    batch_size: int = 32
    loss_weights: Tuple[float, float, float] = (1.0, 1.5, 1.5)
    class_weight_power: float = 0.5  # Square-root inverse frequency
    label_smoothing: float = 0.05
    seed: int = 49

def compute_effective_class_weights(y_task: np.ndarray, num_classes: int, power: float = 0.5) -> torch.Tensor:
    """Compute smoothed inverse frequency weights to balance imbalanced classes."""
    counts = np.bincount(y_task, minlength=num_classes).astype(np.float32)
    weights = np.zeros(num_classes, dtype=np.float32)
    total = len(y_task)
    for c in range(num_classes):
        if counts[c] > 0:
            weights[c] = (total / (counts[c] * num_classes)) ** power
        else:
            weights[c] = 0.0
    # Normalize weights so mean weight = 1.0
    active = weights[weights > 0]
    if len(active) > 0:
        weights = weights / np.mean(active)
    return torch.tensor(weights, dtype=torch.float32)

class TaskRoutedMMoE(nn.Module):
    def __init__(self, num_classes: Dict[str, int], config: E49Config):
        super().__init__()
        self.config = config
        self.num_classes = num_classes
        in_dim = 1536 + 768  # 2304

        # Shared Experts
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(in_dim, config.expert_hidden),
                nn.BatchNorm1d(config.expert_hidden),
                nn.GELU(),
                nn.Dropout(config.dropout)
            )
            for _ in range(config.num_experts)
        ])

        # Task-specific Gating Networks
        self.gates = nn.ModuleDict({
            t: nn.Sequential(
                nn.Linear(in_dim, config.num_experts)
            )
            for t in TASKS
        })

        # Task-specific Towers (specialized task adaptation)
        self.towers = nn.ModuleDict({
            t: nn.Sequential(
                nn.Linear(config.expert_hidden, config.tower_dim),
                nn.BatchNorm1d(config.tower_dim),
                nn.GELU(),
                nn.Dropout(config.dropout)
            )
            for t in TASKS
        })

        # Task Heads
        self.heads = nn.ModuleDict({
            t: nn.Linear(config.tower_dim, num_classes[t])
            for t in TASKS
        })

    def forward(self, visual: torch.Tensor, text: torch.Tensor) -> Dict[str, torch.Tensor]:
        # Feature normalization and scaling
        v_norm = F.normalize(visual.float(), p=2, dim=-1) * self.config.visual_scale
        t_norm = F.normalize(text.float(), p=2, dim=-1) * self.config.text_scale
        x = torch.cat([v_norm, t_norm], dim=-1)  # (batch_size, 2304)

        # Expert outputs: shape (batch_size, num_experts, expert_hidden)
        expert_outputs = torch.stack([expert(x) for expert in self.experts], dim=1)

        logits = {}
        for t in TASKS:
            # Gating weights: shape (batch_size, num_experts, 1)
            gate_weights = F.softmax(self.gates[t](x), dim=-1).unsqueeze(-1)
            # Weighted sum over experts: shape (batch_size, expert_hidden)
            task_rep = (expert_outputs * gate_weights).sum(dim=1)
            # Tower specialization
            tower_rep = self.towers[t](task_rep)
            # Classification logits
            logits[t] = self.heads[t](tower_rep)

        return logits
