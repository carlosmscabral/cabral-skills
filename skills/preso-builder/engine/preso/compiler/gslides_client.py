"""Google Slides CLI Client Wrapper.

Provides a robust, type-safe Python client interface for the
`/google/bin/releases/gemini-agents-gslides/gslides` CLI binary, supporting
presentation cloning, blank creation, atomic single-pass batch executions,
thumbnail export, slide inspection, and hermetic dry-run/mock execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Optional, Union

# =============================================================================
# Constants & Defaults
# =============================================================================

DEFAULT_GSLIDES_BINARY: str = "/google/bin/releases/gemini-agents-gslides/gslides"
DEFAULT_TEMPLATE_ID: str = "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"
DEFAULT_TIMEOUT_SECONDS: int = 120


# =============================================================================
# Exceptions
# =============================================================================


class GSlidesError(Exception):
    """Base exception for all Google Slides CLI errors."""


class GSlidesNotFoundError(GSlidesError):
    """Raised when the gslides CLI binary cannot be located or executed."""


class GSlidesCLIError(GSlidesError):
    """Raised when a gslides CLI command execution returns a non-zero exit code."""

    def __init__(
        self,
        cmd: list[str],
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> None:
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        cmd_str = " ".join(cmd)
        message = (
            f"gslides CLI command failed with exit code {exit_code}.\n"
            f"Command: {cmd_str}\n"
            f"STDERR:\n{stderr.strip()}\n"
            f"STDOUT:\n{stdout.strip()}"
        )
        super().__init__(message)


class GSlidesTimeoutError(GSlidesError):
    """Raised when a gslides CLI command execution exceeds the timeout limit."""

    def __init__(self, cmd: list[str], timeout: float) -> None:
        self.cmd = cmd
        self.timeout = timeout
        cmd_str = " ".join(cmd)
        super().__init__(
            f"gslides CLI command timed out after {timeout} seconds: {cmd_str}"
        )


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class BatchExecutionResult:
    """Structured result returned from executing an atomic batch update."""

    presentation_id: str
    operations_count: int = 0
    api_requests: int = 0
    created_slides: list[str] = field(default_factory=list)
    created_tables: list[str] = field(default_factory=list)
    resolved_ids: dict[str, str] = field(default_factory=dict)
    raw_response: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Converts result to standard dictionary."""
        return {
            "presentation_id": self.presentation_id,
            "operations": self.operations_count,
            "api_requests": self.api_requests,
            "created_slides": self.created_slides,
            "created_tables": self.created_tables,
            "resolved_ids": self.resolved_ids,
            "dry_run": self.dry_run,
            "raw_response": self.raw_response,
        }


# =============================================================================
# GSlides Client
# =============================================================================


class GSlidesClient:
    """Client wrapper for the Google Slides CLI binary (`gslides`).

    Supports all standard presentation management commands, batch payload
    execution, inspection, and thumbnail rendering with automatic JSON
    serialization and error handling.
    """

    def __init__(
        self,
        binary_path: Optional[Union[str, Path]] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        dry_run: bool = False,
        runner: Optional[
            Callable[[list[str], Optional[str]], subprocess.CompletedProcess[str]]
        ] = None,
    ) -> None:
        """Initializes the GSlidesClient.

        Args:
            binary_path: Absolute path to `gslides` binary. Defaults to
                $GSLIDES_PATH environment variable or `DEFAULT_GSLIDES_BINARY`.
            timeout: Subprocess execution timeout in seconds.
            dry_run: If True, simulates CLI executions hermetically without
                invoking external binaries or making network calls.
            runner: Optional custom runner callback for testing and mocking.
        """
        env_path = os.environ.get("GSLIDES_PATH")
        self.binary_path = str(binary_path or env_path or DEFAULT_GSLIDES_BINARY)
        self.timeout = timeout
        self.dry_run = dry_run
        self.runner = runner

    def is_binary_available(self) -> bool:
        """Checks whether the gslides binary exists and is executable.

        Returns:
            True if the binary is accessible and executable, False otherwise.
        """
        if self.runner is not None:
            return True
        if os.path.isabs(self.binary_path):
            return os.path.isfile(self.binary_path) and os.access(
                self.binary_path, os.X_OK
            )
        return shutil.which(self.binary_path) is not None

    def _run_command(
        self,
        args: list[str],
        input_text: Optional[str] = None,
        check_binary: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Executes a gslides CLI command with argument list and error checking.

        Args:
            args: Subcommand arguments to pass to the gslides binary.
            input_text: Optional text to pipe to process stdin.
            check_binary: Whether to verify binary existence before running.

        Returns:
            CompletedProcess instance containing stdout and stderr.

        Raises:
            GSlidesNotFoundError: If binary is missing and no runner is set.
            GSlidesTimeoutError: If execution exceeds configured timeout.
            GSlidesCLIError: If command exits with a non-zero status.
        """
        cmd = [self.binary_path] + args

        if self.runner is not None:
            result = self.runner(cmd, input_text)
            if result.returncode != 0:
                raise GSlidesCLIError(
                    cmd=cmd,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            return result

        if check_binary and not self.is_binary_available():
            raise GSlidesNotFoundError(
                f"gslides CLI binary not found at '{self.binary_path}'. "
                f"Ensure the binary is installed or specify binary_path."
            )

        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise GSlidesTimeoutError(cmd=cmd, timeout=self.timeout) from e
        except FileNotFoundError as e:
            raise GSlidesNotFoundError(
                f"gslides binary not found at '{self.binary_path}': {e}"
            ) from e

        if result.returncode != 0:
            raise GSlidesCLIError(
                cmd=cmd,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return result

    def copy_presentation(
        self,
        template_id: str = DEFAULT_TEMPLATE_ID,
        title: str = "Blueprint Presentation",
    ) -> str:
        """Clones a master template deck and returns the new presentation ID.

        Args:
            template_id: Master template deck ID to copy.
            title: Title for the newly created presentation.

        Returns:
            The created presentation ID string.

        Raises:
            GSlidesError: If the cloning process fails.
        """
        if self.dry_run:
            # Deterministic simulated deck ID based on title and template
            seed = abs(hash(f"{template_id}:{title}")) % 0xFFFFFFFF
            return f"mock_deck_copy_{seed:08x}"

        args = ["copy", template_id, title, "--json"]
        result = self._run_command(args)
        output_str = result.stdout.strip()

        # Parse JSON output or extract ID
        try:
            data = json.loads(output_str)
            if isinstance(data, dict):
                return str(
                    data.get("presentationId")
                    or data.get("presentation_id")
                    or data.get("id")
                    or ""
                )
            elif isinstance(data, str):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback regex extraction for presentation ID
        match = re.search(r"([a-zA-Z0-9_-]{20,})", output_str)
        if match:
            return match.group(1)

        return output_str

    def create_presentation(
        self,
        title: str = "Untitled Presentation",
    ) -> str:
        """Creates a new blank presentation deck and returns its presentation ID.

        Args:
            title: Title for the new presentation.

        Returns:
            The created presentation ID string.

        Raises:
            GSlidesError: If presentation creation fails.
        """
        if self.dry_run:
            seed = abs(hash(f"create:{title}")) % 0xFFFFFFFF
            return f"mock_deck_new_{seed:08x}"

        args = ["create", "--title", title, "--json"]
        result = self._run_command(args)
        output_str = result.stdout.strip()

        try:
            data = json.loads(output_str)
            if isinstance(data, dict):
                return str(
                    data.get("presentationId")
                    or data.get("presentation_id")
                    or data.get("id")
                    or ""
                )
            elif isinstance(data, str):
                return data
        except json.JSONDecodeError:
            pass

        match = re.search(r"([a-zA-Z0-9_-]{20,})", output_str)
        if match:
            return match.group(1)

        return output_str

    def execute_batch(
        self,
        presentation_id: str,
        operations: list[dict[str, Any]],
        dry_run: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Executes an array of operations in a single atomic batch update.

        Args:
            presentation_id: Target presentation ID.
            operations: List of operation dictionaries conforming to gslides
                batch schema.
            dry_run: Override client dry_run setting if specified.

        Returns:
            Dictionary summary of batch execution containing `operations`,
            `api_requests`, `created_slides`, `created_tables`, and `resolved_ids`.

        Raises:
            GSlidesError: If batch execution fails or schema is invalid.
        """
        is_dry_run = self.dry_run if dry_run is None else dry_run

        if is_dry_run:
            # Simulate ID resolution and API response hermetically
            created_slides: list[str] = []
            created_tables: list[str] = []
            resolved_ids: dict[str, str] = {}

            for op in operations:
                op_name = op.get("op", "")
                placeholder_id = op.get("id")
                if placeholder_id:
                    simulated_real_id = f"res_{placeholder_id.lower()}"
                    resolved_ids[placeholder_id] = simulated_real_id
                    if op_name == "add-slide":
                        created_slides.append(simulated_real_id)
                    elif op_name == "add-table":
                        created_tables.append(simulated_real_id)

            simulated_response = {
                "presentation_id": presentation_id,
                "operations": len(operations),
                "api_requests": max(1, len(operations) // 2),
                "created_slides": created_slides,
                "created_tables": created_tables,
                "resolved_ids": resolved_ids,
                "dry_run": True,
            }
            return simulated_response

        # Write operations to a temporary JSON file for atomic execution
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="gslides_batch_",
            delete=False,
            encoding="utf-8",
        ) as tmp_file:
            json.dump(operations, tmp_file, indent=2)
            tmp_path = tmp_file.name

        try:
            args = ["batch", presentation_id, "-f", tmp_path, "--json"]
            result = self._run_command(args)
            output_str = result.stdout.strip()

            try:
                response_data = json.loads(output_str)
                if isinstance(response_data, dict):
                    response_data.setdefault("presentation_id", presentation_id)
                    return response_data
                return {
                    "presentation_id": presentation_id,
                    "operations": len(operations),
                    "response": response_data,
                }
            except json.JSONDecodeError:
                return {
                    "presentation_id": presentation_id,
                    "operations": len(operations),
                    "raw_output": output_str,
                }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def export_thumbnail(
        self,
        presentation_id: str,
        slide_id: str,
        output_path: Union[str, Path],
    ) -> Path:
        """Renders and exports a slide to a PNG image file.

        Args:
            presentation_id: Target presentation ID.
            slide_id: Slide object ID (e.g. `p` or resolved slide ID).
            output_path: Destination file path for the exported PNG image.

        Returns:
            Path object pointing to the exported thumbnail image.

        Raises:
            GSlidesError: If export fails.
        """
        dest_path = Path(output_path).resolve()
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            # Create a 1x1 dummy PNG if file doesn't exist for hermetic testing
            if not dest_path.exists():
                # Minimal valid 1x1 PNG header
                dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                dest_path.write_bytes(dummy_png)
            return dest_path

        args = ["export-thumbnail", presentation_id, str(dest_path), "--slide", slide_id]
        self._run_command(args)
        return dest_path

    def read_all(self, presentation_id: str) -> dict[str, Any]:
        """Reads all slides and text elements from a presentation.

        Args:
            presentation_id: Target presentation ID.

        Returns:
            Dictionary containing presentation tree and text content.

        Raises:
            GSlidesError: If read operation fails.
        """
        if self.dry_run:
            return {
                "presentation_id": presentation_id,
                "title": "Mock Presentation",
                "slides": [],
                "dry_run": True,
            }

        args = ["read-all", presentation_id, "--json"]
        result = self._run_command(args)
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {
                "presentation_id": presentation_id,
                "text": result.stdout.strip(),
            }

    def info(self, presentation_id: str) -> dict[str, Any]:
        """Extracts complete presentation metadata, page sizes, and elements.

        Args:
            presentation_id: Target presentation ID.

        Returns:
            Dictionary with full presentation metadata.

        Raises:
            GSlidesError: If info extraction fails.
        """
        if self.dry_run:
            return {
                "presentationId": presentation_id,
                "title": "Mock Presentation",
                "pageSize": {
                    "width": {"magnitude": 720, "unit": "PT"},
                    "height": {"magnitude": 405, "unit": "PT"},
                },
                "slides": [],
                "dry_run": True,
            }

        args = ["info", presentation_id, "--json"]
        result = self._run_command(args)
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {
                "presentationId": presentation_id,
                "raw_output": result.stdout.strip(),
            }

    def list_slides(self, presentation_id: str) -> list[dict[str, Any]]:
        """Lists all slide objects and layout IDs in presentation order.

        Args:
            presentation_id: Target presentation ID.

        Returns:
            List of slide metadata dictionaries.
        """
        if self.dry_run:
            return [{"objectId": "p", "index": 0, "layout": "BLANK"}]

        args = ["list-slides", presentation_id, "--json"]
        try:
            result = self._run_command(args)
            data = json.loads(result.stdout.strip())
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "slides" in data:
                return data["slides"]
            return [data]
        except Exception:
            info_data = self.info(presentation_id)
            if isinstance(info_data, dict) and isinstance(info_data.get("slides"), list):
                return info_data["slides"]
            return []

    def list_elements(
        self,
        presentation_id: str,
        slide_id_or_index: Union[str, int] = 0,
    ) -> list[dict[str, Any]]:
        """Lists all element IDs and coordinates for a given slide.

        Args:
            presentation_id: Target presentation ID.
            slide_id_or_index: Slide index (0-based) or slide object ID.

        Returns:
            List of element dictionaries.
        """
        if self.dry_run:
            return []

        args = ["list-elements", presentation_id, str(slide_id_or_index), "--json"]
        result = self._run_command(args)
        try:
            data = json.loads(result.stdout.strip())
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "elements" in data:
                return data["elements"]
            return [data]
        except json.JSONDecodeError:
            return []

    def delete_slide(self, presentation_id: str, slide_id: str) -> bool:
        """Deletes a slide from a presentation.

        Args:
            presentation_id: Target presentation ID.
            slide_id: Slide object ID to delete.

        Returns:
            True if deletion succeeded.
        """
        if self.dry_run:
            return True

        args = ["delete-slide", presentation_id, slide_id]
        self._run_command(args)
        return True

    def insert_image_from_file(
        self,
        presentation_id: str,
        slide_id: str,
        file_path: Union[str, Path],
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> bool:
        """Uploads a local image and places it inside the given box (points).

        Batch `add-image` only accepts URLs, so local diagrams/screenshots are
        inserted after the batch runs. The Slides API preserves the image's
        aspect ratio within the requested box.
        """
        src = Path(file_path).expanduser().resolve()
        if not src.exists():
            raise GSlidesError(f"Image file not found: {src}")
        if self.dry_run:
            return True

        args = [
            "mutate", "insert-image-from-file", presentation_id,
            "--slide", slide_id,
            "--file", str(src),
            "--x", f"{x:.1f}",
            "--y", f"{y:.1f}",
            "--width", f"{width:.1f}",
            "--height", f"{height:.1f}",
        ]
        self._run_command(args)
        return True
