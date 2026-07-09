"""Architecture search for student model generation.

Generates diverse student architecture candidates from a configurable search space.
Supports ViT variants, ResNet, and timm-based auto-discovery.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Any

import torch.nn as nn

from backend.models.schemas import SearchSpace  # noqa: TC001


@dataclass(frozen=True)
class StudentArchitecture:
    """A candidate student architecture for knowledge distillation.

    Attributes:
        name: Unique model identifier (e.g., "vit_tiny_patch16_224").
        architecture_type: Family of architecture ("vit", "resnet", "small_transformer").
        params_m: Estimated parameter count in millions.
        config: Architecture-specific configuration dictionary.
    """

    name: str
    architecture_type: str
    params_m: float
    config: dict[str, Any] = field(default_factory=dict)


_VIT_EMBED_DIMS: list[int] = [192, 256, 384, 512, 768]
_VIT_NUM_HEADS: list[int] = [3, 4, 6, 8, 12]
_VIT_DEPTHS: list[int] = [6, 8, 12, 24]
_VIT_PATCH_SIZES: list[int] = [8, 16, 32]
_VIT_IMAGE_SIZE: int = 224

_RESNET_VARIANTS: list[str] = ["resnet18", "resnet34", "resnet50", "resnet101"]

_SMALL_TRANSFORMER_CONFIGS: list[dict[str, Any]] = [
    {"embed_dim": 128, "num_heads": 2, "depth": 4, "mlp_ratio": 4.0},
    {"embed_dim": 256, "num_heads": 4, "depth": 6, "mlp_ratio": 4.0},
    {"embed_dim": 384, "num_heads": 6, "depth": 8, "mlp_ratio": 3.0},
]


def _estimate_vit_params(
    embed_dim: int, _num_heads: int, depth: int, patch_size: int, image_size: int
) -> float:
    """Estimate ViT parameter count in millions.

    Uses the standard ViT formula:
        params = embed^2 * (depth * 4 + 2) + embed * 3 * patch^2 * channels
    where channels defaults to 3 for RGB input.

    Args:
        embed_dim: Hidden embedding dimension.
        _num_heads: Number of attention heads (unused in estimation).
        depth: Number of transformer layers.
        patch_size: Patch size for tokenization.
        image_size: Input image resolution.

    Returns:
        Estimated parameter count in millions.
    """
    channels = 3

    qkv_params = embed_dim * 3 * embed_dim * depth
    attention_params = embed_dim * embed_dim * depth
    mlp_params = embed_dim * embed_dim * 4 * 2 * depth
    layer_norm_params = embed_dim * 2 * depth
    patch_embed_params = channels * patch_size * patch_size * embed_dim
    cls_token_params = embed_dim
    head_params = embed_dim * 1000

    total = (
        qkv_params
        + attention_params
        + mlp_params
        + layer_norm_params
        + patch_embed_params
        + cls_token_params
        + head_params
    )
    return round(total / 1_000_000, 2)


def _generate_vit_candidates() -> list[StudentArchitecture]:
    """Generate diverse ViT architecture candidates.

    Produces combinations of embedding dims, heads, depths, and patch sizes
    to cover a wide range of model sizes from tiny (~5M) to base (~86M).

    Returns:
        List of ViT StudentArchitecture instances.
    """
    candidates: list[StudentArchitecture] = []
    for embed_dim, num_heads, depth, patch_size in itertools.product(
        _VIT_EMBED_DIMS, _VIT_NUM_HEADS, _VIT_DEPTHS, _VIT_PATCH_SIZES
    ):
        if embed_dim % num_heads != 0:
            continue

        params_m = _estimate_vit_params(
            embed_dim, num_heads, depth, patch_size, _VIT_IMAGE_SIZE
        )
        name = f"vit_d{embed_dim}_h{num_heads}_l{depth}_p{patch_size}_{_VIT_IMAGE_SIZE}"
        config: dict[str, Any] = {
            "embed_dim": embed_dim,
            "num_heads": num_heads,
            "depth": depth,
            "patch_size": patch_size,
            "image_size": _VIT_IMAGE_SIZE,
        }
        candidates.append(
            StudentArchitecture(
                name=name,
                architecture_type="vit",
                params_m=params_m,
                config=config,
            )
        )
    return candidates


def _generate_resnet_candidates() -> list[StudentArchitecture]:
    """Generate ResNet architecture candidates.

    Returns:
        List of ResNet StudentArchitecture instances with estimated params.
    """
    resnet_params: dict[str, float] = {
        "resnet18": 11.7,
        "resnet34": 21.8,
        "resnet50": 25.6,
        "resnet101": 44.5,
    }
    candidates: list[StudentArchitecture] = []
    for variant in _RESNET_VARIANTS:
        params_m = resnet_params.get(variant, 25.0)
        candidates.append(
            StudentArchitecture(
                name=variant,
                architecture_type="resnet",
                params_m=params_m,
                config={"variant": variant},
            )
        )
    return candidates


def _generate_small_transformer_candidates() -> list[StudentArchitecture]:
    """Generate small custom transformer candidates.

    Returns:
        List of SmallTransformer StudentArchitecture instances.
    """
    candidates: list[StudentArchitecture] = []
    for i, config in enumerate(_SMALL_TRANSFORMER_CONFIGS):
        embed_dim = config["embed_dim"]
        depth = config["depth"]
        params_m = round(
            (embed_dim**2 * depth * 4 + embed_dim * 3 * 16 * 3) / 1_000_000, 2
        )
        candidates.append(
            StudentArchitecture(
                name=f"small_transformer_{i}",
                architecture_type="small_transformer",
                params_m=params_m,
                config=config,
            )
        )
    return candidates


def generate_candidates(
    search_space: SearchSpace, num_candidates: int = 10
) -> list[StudentArchitecture]:
    """Generate candidate student architectures from the search space.

    Produces a diverse set of architectures filtered by the search space
    configuration. Uses random sampling when the total pool exceeds
    num_candidates to ensure diversity across sizes.

    Args:
        search_space: Defines allowed architectures, pruning ratios, and
            quantization modes.
        num_candidates: Maximum number of candidates to return.

    Returns:
        Diverse list of StudentArchitecture candidates, sorted by params_m.

    Raises:
        ValueError: If num_candidates is less than 1.
    """
    if num_candidates < 1:
        raise ValueError(f"num_candidates must be >= 1, got {num_candidates}")

    allowed_archs = set(search_space.student_architectures)
    pool: list[StudentArchitecture] = []

    if "auto" in allowed_archs or "vit" in allowed_archs:
        pool.extend(_generate_vit_candidates())
    if "auto" in allowed_archs or "resnet" in allowed_archs:
        pool.extend(_generate_resnet_candidates())
    if "auto" in allowed_archs or "small_transformer" in allowed_archs:
        pool.extend(_generate_small_transformer_candidates())

    if not pool:
        pool = _generate_vit_candidates()

    if len(pool) <= num_candidates:
        return sorted(pool, key=lambda c: c.params_m)

    sampled = random.sample(pool, min(num_candidates, len(pool)))
    return sorted(sampled, key=lambda c: c.params_m)


def estimate_params(architecture: StudentArchitecture) -> float:
    """Estimate parameter count for a given architecture.

    Delegates to the appropriate estimation function based on architecture type,
    falling back to the stored params_m if estimation is not available.

    Args:
        architecture: The student architecture to estimate.

    Returns:
        Estimated parameter count in millions.
    """
    if architecture.architecture_type == "vit":
        cfg = architecture.config
        return _estimate_vit_params(
            embed_dim=cfg.get("embed_dim", 384),
            _num_heads=cfg.get("num_heads", 6),
            depth=cfg.get("depth", 12),
            patch_size=cfg.get("patch_size", 16),
            image_size=cfg.get("image_size", 224),
        )
    return architecture.params_m


def build_model_from_config(config: dict[str, Any]) -> nn.Module:
    """Build a PyTorch model from an architecture configuration dictionary.

    Uses timm for known architectures (ViT, ResNet) and falls back to a
    simple MLP for unknown configs.

    Args:
        config: Architecture configuration dictionary. Expected keys vary
            by architecture type:
            - vit: embed_dim, depth, patch_size, image_size
            - resnet: variant (e.g., "resnet50")
            - small_transformer: embed_dim, num_heads, depth
            - fallback: input_size, hidden_size, output_size

    Returns:
        Instantiated PyTorch model.
    """
    arch_type = config.get("architecture_type", config.get("type", ""))

    if arch_type == "resnet" or "variant" in config:
        variant = config.get("variant", "resnet50")
        try:
            import timm
            return timm.create_model(variant, pretrained=False, num_classes=1000)
        except Exception:
            from torchvision import models as tv_models  # type: ignore[import-untyped]
            model_fn = getattr(tv_models, variant, tv_models.resnet50)
            return model_fn(num_classes=1000)

    if arch_type == "vit" or "embed_dim" in config:
        embed_dim = config.get("embed_dim", 384)
        depth = config.get("depth", 12)
        patch_size = config.get("patch_size", 16)
        image_size = config.get("image_size", 224)
        num_classes = config.get("num_classes", 1000)
        try:
            import timm
            model_name = f"vit_{_patch_to_timm_name(patch_size)}_patch{patch_size}_{image_size}"
            return timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        except Exception:
            return _build_vit_fallback(embed_dim, depth, patch_size, image_size, num_classes)

    if arch_type == "small_transformer" or "embed_dim" in config:
        embed_dim = config.get("embed_dim", 256)
        depth = config.get("depth", 6)
        patch_size = config.get("patch_size", 16)
        image_size = config.get("image_size", 224)
        num_classes = config.get("num_classes", 1000)
        return _build_vit_fallback(embed_dim, depth, patch_size, image_size, num_classes)

    input_size = config.get("input_size", 224 * 224 * 3)
    hidden_size = config.get("hidden_size", 512)
    output_size = config.get("num_classes", 1000)
    return nn.Sequential(
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, output_size),
    )


def _patch_to_timm_name(patch_size: int) -> str:
    """Map a patch size to a timm ViT model name prefix."""
    if patch_size <= 8:
        return "tiny"
    if patch_size <= 16:
        return "small"
    return "base"


def _build_vit_fallback(
    embed_dim: int,
    depth: int,
    patch_size: int,
    image_size: int,
    num_classes: int,
) -> nn.Module:
    """Build a simplified ViT when timm is unavailable.

    Constructs a minimal Vision Transformer with patch embedding,
    positional encoding, transformer encoder blocks, and a classification
    head.

    Args:
        embed_dim: Hidden embedding dimension.
        depth: Number of transformer encoder layers.
        patch_size: Patch size for tokenization.
        image_size: Input image resolution.
        num_classes: Number of output classes.

    Returns:
        A minimal ViT model as nn.Module.
    """
    channels = 3
    num_patches = (image_size // patch_size) ** 2

    class FallbackViT(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.patch_embed = nn.Conv2d(
                channels, embed_dim, kernel_size=patch_size, stride=patch_size
            )
            self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim))
            self.pos_embed = nn.Parameter(torch.randn(1, num_patches + 1, embed_dim))
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=embed_dim, nhead=min(embed_dim // 64, 12), batch_first=True
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=depth)
            self.head = nn.Linear(embed_dim, num_classes)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            B = x.shape[0]
            x = self.patch_embed(x).flatten(2).transpose(1, 2)
            cls = self.cls_token.expand(B, -1, -1)
            x = torch.cat([cls, x], dim=1)
            x = x + self.pos_embed[:, : x.size(1), :]
            x = self.encoder(x)
            return self.head(x[:, 0])

    import torch
    return FallbackViT()
