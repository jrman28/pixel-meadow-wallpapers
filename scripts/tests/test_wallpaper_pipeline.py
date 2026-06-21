import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from wallpaper_pipeline import (  # noqa: E402
    PipelineError,
    analyze_frame_deltas,
    build_filter_graph,
    calculate_crop,
    calculate_timing,
    decode_analysis_frames,
    summarize_metadata,
    validate_delivery_metadata,
)
from switch_wallpaper import solar_window  # noqa: E402


class TimingTests(unittest.TestCase):
    def test_ten_second_night_source_becomes_eighteen_point_five_second_loop(self):
        timing = calculate_timing(10.0, slowdown=2.0, crossfade=1.5, fps=24)

        self.assertEqual(timing.processed_frames, 480)
        self.assertEqual(timing.crossfade_frames, 36)
        self.assertEqual(timing.output_frames, 444)
        self.assertEqual(timing.output_duration, 18.5)
        self.assertEqual(timing.xfade_offset, 17.0)

    def test_six_point_five_second_day_source_becomes_eleven_point_five_second_loop(self):
        timing = calculate_timing(6.5, slowdown=2.0, crossfade=1.5, fps=24)

        self.assertEqual(timing.processed_frames, 312)
        self.assertEqual(timing.output_frames, 276)
        self.assertEqual(timing.output_duration, 11.5)
        self.assertEqual(timing.xfade_offset, 10.0)

    def test_rejects_non_positive_or_overlong_crossfade(self):
        with self.assertRaises(PipelineError):
            calculate_timing(10.0, slowdown=2.0, crossfade=0, fps=24)
        with self.assertRaises(PipelineError):
            calculate_timing(0.5, slowdown=2.0, crossfade=1.0, fps=24)

    def test_huntsville_solar_window_handles_utc_date_rollover(self):
        sunrise, sunset = solar_window(dt.date(2026, 6, 20))

        self.assertLess(sunrise, sunset)
        self.assertEqual(sunrise.date().isoformat(), "2026-06-20")
        self.assertEqual(sunset.date().isoformat(), "2026-06-21")


class FilterTests(unittest.TestCase):
    def test_center_crop_converts_16_by_9_to_16_by_10(self):
        crop = calculate_crop(2560, 1440)

        self.assertEqual((crop.width, crop.height, crop.x, crop.y), (2304, 1440, 128, 0))

    def test_rejects_input_narrower_than_16_by_10(self):
        with self.assertRaises(PipelineError):
            calculate_crop(1200, 1000)

    def test_filter_rotates_the_head_instead_of_blending_to_the_wrong_restart_frame(self):
        timing = calculate_timing(10.0, slowdown=2.0, crossfade=1.5, fps=24)
        crop = calculate_crop(2560, 1440)

        graph = build_filter_graph(timing, crop, target_width=2560, target_height=1600)

        self.assertIn("trim=start_frame=36:end_frame=480", graph)
        self.assertIn("trim=start_frame=1:end_frame=37", graph)
        self.assertIn("duration=1.500000:offset=17.000000", graph)
        self.assertNotIn("offset=18.500000", graph)


class AnalysisTests(unittest.TestCase):
    @patch("wallpaper_pipeline.subprocess.run")
    def test_decoder_low_passes_codec_noise_before_motion_scoring(self, run):
        run.return_value.stdout = bytes(320 * 200 * 3)

        decode_analysis_frames("loop.mp4")

        command = run.call_args.args[0]
        filter_graph = command[command.index("-vf") + 1]
        self.assertEqual(
            filter_graph,
            "scale=320:200:flags=area,boxblur=1:1,format=gray",
        )

    def test_duplicate_frame_cadence_does_not_hide_a_good_seam(self):
        frames = [bytes([value]) * 4 for value in (0, 0, 10, 10, 20, 20, 10, 10)]

        report = analyze_frame_deltas(frames, moving_threshold=1.0, seam_limit=1.25)

        self.assertEqual(report.moving_frame_count, 3)
        self.assertLessEqual(report.seam_ratio, 1.25)
        self.assertTrue(report.seam_pass)

    def test_large_restart_change_fails_seam_gate(self):
        frames = [bytes([value]) * 4 for value in (0, 0, 5, 5, 10, 10, 100)]

        report = analyze_frame_deltas(frames, moving_threshold=1.0, seam_limit=1.25)

        self.assertFalse(report.seam_pass)
        self.assertGreater(report.seam_ratio, 1.25)

    def test_delivery_metadata_requires_exact_video_only_main10_hvc1_output(self):
        valid = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "hevc",
                    "codec_tag_string": "hvc1",
                    "width": 2560,
                    "height": 1600,
                    "pix_fmt": "yuv420p10le",
                    "r_frame_rate": "24/1",
                    "nb_frames": "444",
                }
            ],
            "format": {"duration": "18.500000"},
        }

        self.assertEqual(validate_delivery_metadata(valid, expected_frames=444), [])

        invalid = {
            **valid,
            "streams": valid["streams"] + [{"codec_type": "audio", "codec_name": "aac"}],
        }
        self.assertIn("expected zero audio streams", validate_delivery_metadata(invalid, 444))

        summary = summarize_metadata(valid)
        self.assertEqual(summary["codec"], "hevc")
        self.assertEqual(summary["width"], 2560)
        self.assertEqual(summary["frame_count"], 444)
        self.assertEqual(summary["duration"], 18.5)
        self.assertEqual(summary["audio_streams"], 0)


if __name__ == "__main__":
    unittest.main()
