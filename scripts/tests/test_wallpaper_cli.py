import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REFINE = SCRIPTS_DIR / "refine_ai_wallpaper.py"
ANALYZE = SCRIPTS_DIR / "analyze_loop.py"
WRAPPER = SCRIPTS_DIR / "convert_ai_wallpaper.sh"


class WallpaperCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.source = Path(cls.tempdir.name) / "source.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=24:duration=1",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(cls.source),
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_dry_run_reports_frame_quantized_filter_and_duration(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(REFINE),
                str(self.source),
                str(Path(self.tempdir.name) / "unused.mp4"),
                "--slowdown",
                "2",
                "--crossfade",
                "0.5",
                "--width",
                "320",
                "--height",
                "200",
                "--mode",
                "preview",
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["timing"]["processed_frames"], 48)
        self.assertEqual(report["timing"]["crossfade_frames"], 12)
        self.assertEqual(report["timing"]["output_frames"], 36)
        self.assertEqual(report["timing"]["output_duration"], 1.5)
        self.assertIn("trim=start_frame=12:end_frame=48", report["filter_graph"])

    def test_preview_encode_has_expected_frames_and_no_audio(self):
        output = Path(self.tempdir.name) / "preview.mp4"
        subprocess.run(
            [
                sys.executable,
                str(REFINE),
                str(self.source),
                str(output),
                "--slowdown",
                "2",
                "--crossfade",
                "0.5",
                "--width",
                "320",
                "--height",
                "200",
                "--mode",
                "preview",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        metadata = json.loads(
            subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-count_frames",
                    "-show_streams",
                    "-show_format",
                    "-of",
                    "json",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        videos = [stream for stream in metadata["streams"] if stream["codec_type"] == "video"]
        audios = [stream for stream in metadata["streams"] if stream["codec_type"] == "audio"]

        self.assertEqual(int(videos[0]["nb_read_frames"]), 36)
        self.assertEqual(audios, [])
        self.assertAlmostEqual(float(metadata["format"]["duration"]), 1.5, places=3)

    def test_legacy_converter_forwards_to_the_duration_aware_cli(self):
        completed = subprocess.run(
            [
                "bash",
                str(WRAPPER),
                str(self.source),
                str(Path(self.tempdir.name) / "wrapper-unused.mp4"),
                "--crossfade",
                "0.5",
                "--width",
                "320",
                "--height",
                "200",
                "--mode",
                "preview",
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["timing"]["output_frames"], 36)

    def test_legacy_converter_preserves_crossfade_environment_variable(self):
        environment = {**os.environ, "CROSSFADE_SECONDS": "0.25"}
        completed = subprocess.run(
            [
                "bash",
                str(WRAPPER),
                str(self.source),
                str(Path(self.tempdir.name) / "wrapper-env-unused.mp4"),
                "--width",
                "320",
                "--height",
                "200",
                "--mode",
                "preview",
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["timing"]["crossfade_frames"], 6)
        self.assertEqual(report["timing"]["output_frames"], 42)

    def test_analyzer_writes_json_and_rejects_a_discontinuous_loop(self):
        report_path = Path(self.tempdir.name) / "analysis.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(ANALYZE),
                str(self.source),
                "--json-out",
                str(report_path),
                "--require-seam",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 2)
        report = json.loads(report_path.read_text())
        self.assertFalse(report["motion"]["seam_pass"])
        self.assertEqual(report["media"]["codec"], "h264")
        self.assertEqual(report["media"]["audio_streams"], 0)
        self.assertIn("seam", completed.stdout.lower())


if __name__ == "__main__":
    unittest.main()
