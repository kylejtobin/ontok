import os
from unittest import TestCase
from unittest.mock import patch

from platformdirs import user_data_dir

from ontok.ex import DataDirectory, ExecutionConfig


class TestExecutionConfig(TestCase):
    def test_data_directory_has_cross_platform_default(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("ONTOK_EX_DATA_DIRECTORY", None)
            config = ExecutionConfig()

        self.assertEqual(
            config.data_directory,
            DataDirectory(user_data_dir("ontok-ex", appauthor=False)),
        )

    def test_data_directory_accepts_configured_path(self) -> None:
        configured = DataDirectory("configured/data")

        config = ExecutionConfig(data_directory=configured)

        self.assertEqual(config.data_directory, configured)

    def test_data_directory_accepts_environment_path(self) -> None:
        configured = DataDirectory("environment/data")

        with patch.dict(
            os.environ,
            {"ONTOK_EX_DATA_DIRECTORY": configured.root},
        ):
            config = ExecutionConfig()

        self.assertEqual(config.data_directory, configured)
