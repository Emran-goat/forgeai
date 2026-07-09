"""Model export to ONNX, TorchScript, and JIT formats."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of model export.

    Attributes:
        file_path: Path to the exported model file.
        format: Export format used.
        file_size_bytes: Size of the exported file.
    """

    file_path: Path  # noqa: TC003
    format: str
    file_size_bytes: int


def export_to_onnx(
    model: Any,
    output_path: Path,  # noqa: TC003
    input_shape: tuple[int, ...] = (1, 3, 224, 224),
) -> ExportResult:
    """Export model to ONNX format.

    Args:
        model: PyTorch model to export.
        output_path: Path for the output .onnx file.
        input_shape: Input tensor shape.

    Returns:
        ExportResult with file path and metadata.

    Raises:
        RuntimeError: If ONNX export fails.
    """
    try:
        import torch

        output_path.parent.mkdir(parents=True, exist_ok=True)

        dummy_input = torch.randn(*input_shape)
        torch.onnx.export(
            model,
            dummy_input,  # type: ignore[arg-type]
            str(output_path),
            export_params=True,
            opset_version=17,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
        )

        file_size = output_path.stat().st_size
        logger.info("Exported ONNX model to %s (%d bytes)", output_path, file_size)

        return ExportResult(
            file_path=output_path,
            format="onnx",
            file_size_bytes=file_size,
        )
    except Exception as e:
        logger.exception("ONNX export failed")
        raise RuntimeError(f"ONNX export failed: {e}") from e


def export_to_torchscript(
    model: Any,
    output_path: Path,  # noqa: TC003
    input_shape: tuple[int, ...] = (1, 3, 224, 224),
) -> ExportResult:
    """Export model to TorchScript format.

    Args:
        model: PyTorch model to export.
        output_path: Path for the output .pt file.
        input_shape: Input tensor shape.

    Returns:
        ExportResult with file path and metadata.

    Raises:
        RuntimeError: If TorchScript export fails.
    """
    try:
        import torch

        output_path.parent.mkdir(parents=True, exist_ok=True)

        model.eval()
        dummy_input = torch.randn(*input_shape)
        traced_model = torch.jit.trace(model, dummy_input)  # type: ignore[no-untyped-call]
        traced_model.save(str(output_path))

        file_size = output_path.stat().st_size
        logger.info("Exported TorchScript model to %s (%d bytes)", output_path, file_size)

        return ExportResult(
            file_path=output_path,
            format="torchscript",
            file_size_bytes=file_size,
        )
    except Exception as e:
        logger.exception("TorchScript export failed")
        raise RuntimeError(f"TorchScript export failed: {e}") from e


def export_model(
    model: Any,
    output_dir: Path,  # noqa: TC003
    format: str,  # noqa: A002
    input_shape: tuple[int, ...] = (1, 3, 224, 224),
) -> ExportResult:
    """Export model to the specified format.

    Args:
        model: PyTorch model to export.
        output_dir: Directory for the output file.
        format: Export format ("onnx" or "torchscript").
        input_shape: Input tensor shape.

    Returns:
        ExportResult with file path and metadata.

    Raises:
        ValueError: If format is not supported.
    """
    if format == "onnx":
        output_path = output_dir / "model.onnx"
        return export_to_onnx(model, output_path, input_shape)
    elif format == "torchscript":
        output_path = output_dir / "model.pt"
        return export_to_torchscript(model, output_path, input_shape)
    else:
        raise ValueError(f"Unsupported export format: {format}")
