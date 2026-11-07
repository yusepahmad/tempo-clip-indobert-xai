"""Unit and gradient flow verification for E49 TaskRoutedMMoE."""
import torch
from model import TaskRoutedMMoE, E49Config, TASKS

def test_model_checks():
    nc = {'task1_issue': 10, 'task2_domain_sumber': 7, 'task3_primary_entity_type': 8}
    cfg = E49Config()
    model = TaskRoutedMMoE(nc, cfg)

    bsz = 4
    v = torch.randn(bsz, 1536)
    t = torch.randn(bsz, 768)

    model.train()
    logits = model(v, t)
    for task in TASKS:
        assert logits[task].shape == (bsz, nc[task]), f"Mismatch in {task} shape"

    # Test gradient flow to shared experts from each task individually
    for task in TASKS:
        model.zero_grad()
        loss = logits[task].sum()
        loss.backward(retain_graph=True)
        for i, expert in enumerate(model.experts):
            grad_norm = sum(p.grad.norm().item() for p in expert.parameters() if p.grad is not None)
            assert grad_norm > 1e-6, f"Expert {i} received no gradient from {task}"
            print(f"Task {task} -> Expert {i} gradient norm: {grad_norm:.4f}")

    print("ALL E49 MODEL GRADIENT FLOW AND ARCHITECTURE CHECKS PASSED!")

if __name__ == '__main__':
    test_model_checks()
