"""Knowledge distillation engine for teacher-to-student model compression.

Implements soft-target distillation with configurable temperature, alpha weighting,
and optional intermediate feature-level distillation between compatible architectures.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.utils.hooks import RemovableHandle


@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation.

    Attributes:
        temperature: Softmax temperature for logit scaling. Higher values produce
            softer probability distributions from teacher logits.
        alpha: Weight for KD loss vs task loss. 1.0 = pure distillation,
            0.0 = pure supervised training.
        learning_rate: Optimizer learning rate for student training.
        epochs: Number of training epochs.
        batch_size: Mini-batch size.
        feature_loss_weight: Weight for intermediate feature distillation loss.
            Set to 0.0 to disable feature-level distillation.
    """

    temperature: float = 4.0
    alpha: float = 0.7
    learning_rate: float = 1e-4
    epochs: int = 10
    batch_size: int = 32
    feature_loss_weight: float = 0.3


@dataclass
class DistillationResult:
    """Result of a knowledge distillation run.

    Attributes:
        student_model: The trained student model.
        train_loss: Final training loss after all epochs.
        val_accuracy: Validation accuracy of the trained student.
        epochs_trained: Number of epochs actually completed.
        training_time_s: Wall-clock training time in seconds.
    """

    student_model: nn.Module
    train_loss: float
    val_accuracy: float
    epochs_trained: int
    training_time_s: float


@dataclass
class _FeatureHooks:
    """Container for forward-hook handles and captured activations."""

    handles: list[RemovableHandle] = field(default_factory=list)
    teacher_features: dict[str, torch.Tensor] = field(default_factory=dict)
    student_features: dict[str, torch.Tensor] = field(default_factory=dict)


def create_soft_targets(
    teacher: nn.Module,
    batch: torch.Tensor,
    temperature: float,
) -> torch.Tensor:
    """Generate soft probability distribution from teacher logits.

    Args:
        teacher: Teacher model in eval mode.
        batch: Input tensor of shape (N, *input_shape).
        temperature: Scaling factor for logits. Higher values yield
            softer distributions.

    Returns:
        Soft probability distribution tensor of shape (N, num_classes).
    """
    teacher.eval()
    with torch.no_grad():
        logits = teacher(batch)
    return F.softmax(logits / temperature, dim=-1)


def compute_kd_loss(
    student_logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    temperature: float,
) -> torch.Tensor:
    """Compute KL-divergence loss between softened student and teacher distributions.

    The loss is scaled by T^2 to compensate for the gradient magnitude reduction
    caused by temperature scaling (as per Hinton et al., 2015).

    Args:
        student_logits: Raw logits from the student model, shape (N, C).
        teacher_logits: Raw logits from the teacher model, shape (N, C).
        temperature: Temperature used for softening distributions.

    Returns:
        Scalar KD loss tensor.
    """
    student_log_probs = F.log_softmax(student_logits / temperature, dim=-1)
    teacher_probs = F.softmax(teacher_logits / temperature, dim=-1)
    kl_div = F.kl_div(
        student_log_probs,
        teacher_probs,
        reduction="batchmean",
    )
    return kl_div * (temperature**2)


def _find_common_layers(
    teacher: nn.Module,
    student: nn.Module,
) -> list[tuple[str, str]]:
    """Find matching intermediate layer names between teacher and student.

    Attempts to align layers by exact name match first, then by sequential
    index as a fallback for architectures with different naming conventions.

    Args:
        teacher: Teacher model.
        student: Student model.

    Returns:
        List of (teacher_layer_name, student_layer_name) pairs.
    """
    teacher_names = {name for name, _ in teacher.named_modules()}
    student_names = {name for name, _ in student.named_modules()}
    common = sorted(teacher_names & student_names)
    if common:
        return [(n, n) for n in common]

    teacher_children = list(teacher.named_children())
    student_children = list(student.named_children())
    pairs: list[tuple[str, str]] = []
    for i, (t_name, t_mod) in enumerate(teacher_children):
        if i < len(student_children):
            s_name, s_mod = student_children[i]
            if type(t_mod) is type(s_mod):
                pairs.append((t_name, s_name))
    return pairs


class KnowledgeDistiller:
    """Knowledge distillation orchestrator.

    Trains a student model to mimic a frozen teacher's soft outputs,
    optionally with intermediate feature alignment.
    """

    def __init__(self, config: DistillationConfig) -> None:
        """Initialize the distiller with a configuration.

        Args:
            config: Distillation hyperparameters.
        """
        self.config = config

    def distill(
        self,
        teacher: nn.Module,
        student: nn.Module,
        train_loader: DataLoader[torch.Tensor],
        val_loader: DataLoader[torch.Tensor],
    ) -> DistillationResult:
        """Run knowledge distillation from teacher to student.

        Args:
            teacher: Pre-trained teacher model (weights will be frozen).
            student: Student model to be trained.
            train_loader: DataLoader yielding (inputs, labels) tuples.
            val_loader: DataLoader yielding (inputs, labels) tuples for evaluation.

        Returns:
            Trained student model with training metrics.

        Raises:
            ValueError: If config.alpha is not in [0.0, 1.0].
        """
        if not 0.0 <= self.config.alpha <= 1.0:
            raise ValueError(f"alpha must be in [0.0, 1.0], got {self.config.alpha}")

        device = next(teacher.parameters()).device
        student = student.to(device)

        teacher.eval()
        for param in teacher.parameters():
            param.requires_grad = False

        optimizer = torch.optim.Adam(
            student.parameters(), lr=self.config.learning_rate
        )

        feature_pairs = _find_common_layers(teacher, student)
        hooks = self._register_feature_hooks(teacher, student, feature_pairs)

        start_time = time.monotonic()
        last_train_loss = 0.0

        for _epoch in range(self.config.epochs):
            student.train()
            epoch_loss = 0.0
            num_batches = 0

            for batch_inputs, batch_labels in train_loader:
                batch_inputs = batch_inputs.to(device)
                batch_labels = batch_labels.to(device)

                student_logits = student(batch_inputs)
                with torch.no_grad():
                    teacher_logits = teacher(batch_inputs)

                kd_loss = compute_kd_loss(
                    student_logits, teacher_logits, self.config.temperature
                )
                task_loss = F.cross_entropy(student_logits, batch_labels)
                combined_loss = self.config.alpha * kd_loss + (
                    1 - self.config.alpha
                ) * task_loss

                if self.config.feature_loss_weight > 0.0 and hooks.teacher_features:
                    feat_loss = self._compute_feature_loss(hooks)
                    combined_loss += self.config.feature_loss_weight * feat_loss

                optimizer.zero_grad()
                combined_loss.backward()  # type: ignore[no-untyped-call]
                optimizer.step()

                epoch_loss += combined_loss.item()
                num_batches += 1
                hooks.teacher_features.clear()
                hooks.student_features.clear()

            last_train_loss = epoch_loss / max(num_batches, 1)

        training_time = time.monotonic() - start_time
        self._remove_hooks(hooks)

        val_accuracy = self._evaluate(student, val_loader, device)

        return DistillationResult(
            student_model=student,
            train_loss=last_train_loss,
            val_accuracy=val_accuracy,
            epochs_trained=self.config.epochs,
            training_time_s=training_time,
        )

    def _register_feature_hooks(
        self,
        teacher: nn.Module,
        student: nn.Module,
        feature_pairs: list[tuple[str, str]],
    ) -> _FeatureHooks:
        """Attach forward hooks to capture intermediate activations.

        Args:
            teacher: Teacher model.
            student: Student model.
            feature_pairs: List of (teacher_layer, student_layer) name pairs.

        Returns:
            Container with hook handles and activation storage.
        """
        hooks = _FeatureHooks()

        def _make_teacher_hook(name: str) -> Callable[..., None]:
            def hook(
                module: nn.Module, inp: torch.Tensor, output: torch.Tensor
            ) -> None:
                hooks.teacher_features[name] = output.detach()
            return hook

        def _make_student_hook(name: str) -> Callable[..., None]:
            def hook(
                module: nn.Module, inp: torch.Tensor, output: torch.Tensor
            ) -> None:
                hooks.student_features[name] = output.detach()
            return hook

        for t_name, s_name in feature_pairs:
            teacher_module = dict(teacher.named_modules())[t_name]
            student_module = dict(student.named_modules())[s_name]
            hooks.handles.append(
                teacher_module.register_forward_hook(_make_teacher_hook(t_name))
            )
            hooks.handles.append(
                student_module.register_forward_hook(_make_student_hook(s_name))
            )

        return hooks

    @staticmethod
    def _compute_feature_loss(hooks: _FeatureHooks) -> torch.Tensor:
        """Compute MSE loss between teacher and student intermediate features.

        Features are flattened to align dimensions before comparison.

        Args:
            hooks: Feature hooks container with captured activations.

        Returns:
            Scalar feature alignment loss.
        """
        total_loss = 0.0
        for name in hooks.teacher_features:
            if name not in hooks.student_features:
                continue
            t_feat = hooks.teacher_features[name].flatten(1)
            s_feat = hooks.student_features[name].flatten(1)
            min_dim = min(t_feat.shape[-1], s_feat.shape[-1])
            loss = F.mse_loss(s_feat[..., :min_dim], t_feat[..., :min_dim])
            total_loss = total_loss + loss.item()
        device = next(iter(hooks.teacher_features.values())).device
        return torch.tensor(total_loss, device=device)

    @staticmethod
    def _remove_hooks(hooks: _FeatureHooks) -> None:
        """Remove all registered forward hooks.

        Args:
            hooks: Feature hooks container to clean up.
        """
        for handle in hooks.handles:
            handle.remove()
        hooks.handles.clear()

    @staticmethod
    def _evaluate(
        model: nn.Module,
        val_loader: DataLoader[torch.Tensor],
        device: torch.device,
    ) -> float:
        """Evaluate model accuracy on a validation set.

        Args:
            model: Model to evaluate.
            val_loader: Validation DataLoader yielding (inputs, labels) tuples.
            device: Device to run inference on.

        Returns:
            Top-1 accuracy as a float in [0.0, 1.0].
        """
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                outputs = model(inputs)
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        return correct / total if total > 0 else 0.0
