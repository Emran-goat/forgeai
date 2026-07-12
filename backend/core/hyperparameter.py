"""Optuna hyperparameter tuning for the optimization pipeline.

Tunes distillation, pruning, and quantization hyperparameters using
Bayesian optimization with early stopping and constraint handling.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Callable

    from backend.models.schemas import CandidateInfo, ConstraintSet

logger = logging.getLogger(__name__)


class HyperparameterConfig(BaseModel):
    """Configuration for hyperparameter tuning.

    Attributes:
        n_trials: Maximum number of Optuna trials.
        timeout_seconds: Wall-clock timeout for tuning.
        objective_weights: Weights for accuracy, latency, vram objectives.
        constraints: Hardware constraints to respect.
        hardware_target: Target hardware identifier.
    """

    n_trials: int = 50
    timeout_seconds: int = 3600
    objective_weights: dict[str, float] = Field(
        default_factory=lambda: {"accuracy": 1.0, "latency": 0.5, "vram": 0.3}
    )
    constraints: ConstraintSet = Field(default_factory=lambda: ConstraintSet())
    hardware_target: str = "mi300x"


class TrialInfo(BaseModel):
    """Information about a single Optuna trial.

    Attributes:
        trial_number: Optuna trial number.
        params: Hyperparameters sampled in this trial.
        value: Objective value returned by the trial.
        state: Trial state (COMPLETE, PRUNED, FAIL).
        duration_s: Wall-clock duration of the trial.
    """

    trial_number: int
    params: dict[str, Any]
    value: float
    state: str
    duration_s: float


class TuningResult(BaseModel):
    """Result of hyperparameter tuning.

    Attributes:
        best_params: Best hyperparameter combination found.
        best_value: Best objective value achieved.
        n_trials_completed: Total trials that finished.
        pruned_trials: Trials pruned by early stopping.
        convergence_trial: Trial index where best was first found.
        all_trials: Information for every trial run.
    """

    best_params: dict[str, Any] = Field(default_factory=dict)
    best_value: float = 0.0
    n_trials_completed: int = 0
    pruned_trials: int = 0
    convergence_trial: int = 0
    all_trials: list[TrialInfo] = Field(default_factory=list)


class HyperparameterTuner:
    """Optuna-based hyperparameter tuner for the optimization pipeline.

    Tunes distillation temperature, distillation alpha, pruning ratio,
    quantization bits, learning rate, and batch size. Uses MedianPruner
    for early stopping and enforces hardware constraints.

    Attributes:
        config: Tuning configuration.
    """

    def __init__(self, config: HyperparameterConfig) -> None:
        """Initialize the tuner.

        Args:
            config: Hyperparameter tuning configuration.
        """
        self.config = config

    def create_study(self) -> Any:
        """Create and return an Optuna study.

        Returns:
            Configured optuna.Study with MedianPruner.
        """
        import optuna

        pruner = optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=10,
        )

        study = optuna.create_study(
            direction="maximize",
            pruner=pruner,
            study_name="forgeai_hyperparameter_tuning",
        )
        return study

    async def run_trials(
        self,
        candidates: list[CandidateInfo],
        progress_callback: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> TuningResult:
        """Run Optuna trials to find optimal hyperparameters.

        Executes distillation + pruning + quantization with each trial's
        hyperparameters and returns a weighted objective score. Stops after
        n_trials, timeout, or no improvement for 10 consecutive trials.

        Args:
            candidates: Candidate architectures to tune on.
            progress_callback: Optional async callback for progress updates.

        Returns:
            TuningResult with best parameters and trial history.
        """
        import optuna

        study = self.create_study()
        start_time = time.time()
        best_stale_count = 0
        no_improvement_limit = 10

        for trial_idx in range(self.config.n_trials):
            if time.time() - start_time > self.config.timeout_seconds:
                logger.info("Tuning timeout reached at trial %d", trial_idx)
                break

            if best_stale_count >= no_improvement_limit:
                logger.info(
                    "No improvement for %d trials, stopping at trial %d",
                    no_improvement_limit,
                    trial_idx,
                )
                break

            trial_start = time.time()

            def objective(trial: Any) -> float:
                return self._objective(trial, candidates)

            try:
                study.optimize(
                    objective,
                    n_trials=1,
                    timeout=max(1, self.config.timeout_seconds - (time.time() - start_time)),
                )
            except optuna.exceptions.OptunaError:
                logger.exception("Optuna error at trial %d", trial_idx)
                continue

            elapsed_trial = time.time() - trial_start
            best_trial = study.best_trial
            prev_best = study.best_value if len(study.trials) > 1 else float("-inf")

            if best_trial.value > prev_best:
                best_stale_count = 0
            else:
                best_stale_count += 1

            if progress_callback:
                await progress_callback("hyperparameter_trial", {
                    "trial": trial_idx + 1,
                    "total_trials": self.config.n_trials,
                    "best_value": round(study.best_value, 4),
                    "best_params": study.best_params,
                    "elapsed_s": round(elapsed_trial, 2),
                })

        completed = sum(
            1 for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE
        )
        pruned = sum(
            1 for t in study.trials if t.state == optuna.trial.TrialState.PRUNED
        )

        convergence_trial = 0
        if study.trials:
            best_val = float("-inf")
            for i, t in enumerate(study.trials):
                if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None:
                    if t.value > best_val:
                        best_val = t.value
                        convergence_trial = i

        all_trial_infos = [
            TrialInfo(
                trial_number=t.number,
                params=t.params,
                value=t.value if t.value is not None else 0.0,
                state=t.state.name,
                duration_s=0.0,
            )
            for t in study.trials
        ]

        return TuningResult(
            best_params=study.best_params,
            best_value=study.best_value,
            n_trials_completed=completed,
            pruned_trials=pruned,
            convergence_trial=convergence_trial,
            all_trials=all_trial_infos,
        )

    def _objective(self, trial: Any, candidates: list[CandidateInfo]) -> float:
        """Optuna objective function.

        Samples hyperparameters, runs the optimization pipeline on the first
        candidate, and returns a weighted score. Respects constraints by
        returning -inf for violating trials.

        Args:
            trial: Optuna trial object for sampling hyperparameters.
            candidates: Candidate architectures to evaluate on.

        Returns:
            Weighted objective score (higher is better).
        """
        import torch

        from backend.core.architecture_search import build_model_from_config
        from backend.core.distillation import DistillationConfig, KnowledgeDistiller
        from backend.core.pruning import structured_pruning
        from backend.core.quantization import ModelQuantizer, QuantizationConfig

        temperature = trial.suggest_float("distillation_temperature", 1.0, 10.0)
        alpha = trial.suggest_float("distillation_alpha", 0.1, 0.9)
        pruning_ratio = trial.suggest_float("pruning_ratio", 0.1, 0.7)
        quantization_bits = trial.suggest_categorical("quantization_bits", [4, 8, 16])
        learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
        batch_size = trial.suggest_categorical("batch_size", [8, 16, 32, 64])

        candidate = candidates[0] if candidates else None
        if candidate is None:
            return 0.0

        try:
            arch_config = {
                "architecture_type": candidate.architecture,
                "variant": candidate.architecture,
                "input_size": 224 * 224 * 3,
            }
            model = build_model_from_config(arch_config)
            teacher = build_model_from_config(arch_config)

            distill_config = DistillationConfig(
                temperature=temperature,
                alpha=alpha,
                epochs=getattr(self.config, "distillation_epochs", 2),
                learning_rate=learning_rate,
            )
            distiller = KnowledgeDistiller(distill_config)

            inputs = torch.randn(batch_size, 224 * 224 * 3)
            labels = torch.randint(0, 1000, (batch_size,))
            from torch.utils.data import DataLoader, TensorDataset

            train_loader = DataLoader(
                TensorDataset(inputs, labels), batch_size=batch_size
            )
            val_loader = DataLoader(
                TensorDataset(inputs, labels), batch_size=batch_size
            )

            distill_result = distiller.distill(
                teacher=teacher,
                student=model,
                train_loader=train_loader,
                val_loader=val_loader,
            )

            pruned_result = structured_pruning(model, pruning_ratio)

            mode_map = {4: "int4", 8: "int8", 16: "fp16"}
            q_config = QuantizationConfig(mode=mode_map[quantization_bits], use_qat=False)
            quantizer = ModelQuantizer(q_config)
            quantizer.quantize(model)

            accuracy = distill_result.val_accuracy
            latency_ms = 100.0 * (1.0 - pruned_result.sparsity) * (quantization_bits / 32)
            vram_gb = candidate.params_m * (quantization_bits / 32) * 0.004

        except Exception:
            logger.exception("Trial %d failed", trial.number)
            return 0.0

        weights = self.config.objective_weights
        score = (
            weights.get("accuracy", 1.0) * accuracy
            - weights.get("latency", 0.5) * (latency_ms / 1000.0)
            - weights.get("vram", 0.3) * vram_gb
        )

        constraints = self.config.constraints
        if constraints.max_latency_ms is not None and latency_ms > constraints.max_latency_ms:
            return float("-inf")
        if constraints.max_memory_gb is not None and vram_gb > constraints.max_memory_gb:
            return float("-inf")
        if constraints.min_accuracy is not None and accuracy < constraints.min_accuracy:
            return float("-inf")

        return score

