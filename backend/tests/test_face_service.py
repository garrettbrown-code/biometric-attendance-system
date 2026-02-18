from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

from app.services.face_service import verify_face_match


class FakeFR:
    def __init__(self):
        self._load_side_effect = []
        self._enc_side_effect = []
        self._compare_return = [True]
        self.compare_called = False

    def load_image_file(self, *_args, **_kwargs):
        if self._load_side_effect:
            return self._load_side_effect.pop(0)
        return "img_arr"

    def face_encodings(self, *_args, **_kwargs):
        if self._enc_side_effect:
            return self._enc_side_effect.pop(0)
        return [object()]

    def compare_faces(self, *_args, **_kwargs):
        self.compare_called = True
        return self._compare_return


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def test_reference_image_missing(tmp_path: Path) -> None:
    result = verify_face_match(
        submitted_photo_b64=_b64(b"fake"),
        reference_image_path=tmp_path / "missing.jpg",
    )
    assert result.status == "error"
    assert result.error == "Reference image not found"


@patch("app.services.face_service.Image.open")
@patch("app.services.face_service._fr")
def test_successful_match(mock_fr, mock_image_open, tmp_path: Path) -> None:
    ref_path = tmp_path / "reference.jpg"
    ref_path.write_bytes(b"dummy")

    mock_image_open.return_value = _FakePILImage()

    fake_fr = FakeFR()
    fake_fr._load_side_effect = ["ref_arr", "sub_arr"]
    fake_fr._enc_side_effect = [[object()], [object()]]
    fake_fr._compare_return = [True]
    mock_fr.return_value = fake_fr

    result = verify_face_match(
        submitted_photo_b64=_b64(b"submitted-image-bytes"),
        reference_image_path=ref_path,
    )
    assert result.status == "success"
    assert result.error is None


@patch("app.services.face_service.Image.open")
@patch("app.services.face_service._fr")
def test_no_face_in_reference(mock_fr, mock_image_open, tmp_path: Path) -> None:
    ref_path = tmp_path / "reference.jpg"
    ref_path.write_bytes(b"dummy")

    mock_image_open.return_value = _FakePILImage()

    fake_fr = FakeFR()
    fake_fr._load_side_effect = ["ref_arr", "sub_arr"]
    fake_fr._enc_side_effect = [[], [object()]]  # reference has no face
    mock_fr.return_value = fake_fr

    result = verify_face_match(
        submitted_photo_b64=_b64(b"submitted-image-bytes"),
        reference_image_path=ref_path,
    )
    assert result.status == "error"
    assert result.error == "No face detected in reference image"
    assert fake_fr.compare_called is False


@patch("app.services.face_service.Image.open")
@patch("app.services.face_service._fr")
def test_no_face_in_submitted(mock_fr, mock_image_open, tmp_path: Path) -> None:
    ref_path = tmp_path / "reference.jpg"
    ref_path.write_bytes(b"dummy")

    mock_image_open.return_value = _FakePILImage()

    fake_fr = FakeFR()
    fake_fr._load_side_effect = ["ref_arr", "sub_arr"]
    fake_fr._enc_side_effect = [[object()], []]  # submitted has no face
    mock_fr.return_value = fake_fr

    result = verify_face_match(
        submitted_photo_b64=_b64(b"submitted-image-bytes"),
        reference_image_path=ref_path,
    )
    assert result.status == "error"
    assert result.error == "No face detected in submitted image"
    assert fake_fr.compare_called is False


def test_invalid_base64_rejected(tmp_path: Path) -> None:
    ref_path = tmp_path / "reference.jpg"
    ref_path.write_bytes(b"dummy")

    result = verify_face_match(
        submitted_photo_b64="!!!notbase64!!!",
        reference_image_path=ref_path,
    )
    assert result.status == "error"
    assert "base64" in (result.error or "").lower()


class _FakePILImage:
    def convert(self, mode: str):
        return self

    def save(self, buf, format: str = "JPEG", quality: int = 95):
        buf.write(b"fake-jpeg")
