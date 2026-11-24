import os
import unittest
from unittest.mock import patch

from utils.enable_multilib import enabled_config
from utils.terminal import terminal_launch_command


class MultilibConfigTests(unittest.TestCase):
    def test_enables_commented_section_without_touching_testing(self):
        config = (
            "#[multilib-testing]\n#Include = /etc/pacman.d/mirrorlist\n"
            "#[multilib]\n#Include = /etc/pacman.d/mirrorlist\n"
        )
        enabled = enabled_config(config)
        self.assertIn("[multilib]\nInclude = /etc/pacman.d/mirrorlist", enabled)
        self.assertIn("#[multilib-testing]", enabled)
        self.assertEqual(enabled_config(enabled), enabled)

    def test_appends_missing_section(self):
        self.assertIn("[multilib]\nInclude = /etc/pacman.d/mirrorlist", enabled_config("[core]\n"))

    def test_rejects_incomplete_section(self):
        with self.assertRaises(ValueError):
            enabled_config("[multilib]\nSigLevel = PackageRequired\n")


class PreferredTerminalTests(unittest.TestCase):
    def test_terminal_environment_takes_priority(self):
        with patch.dict(os.environ, {"TERMINAL": "kitty", "XDG_CURRENT_DESKTOP": "KDE"}), \
             patch("utils.terminal.shutil.which", return_value="/usr/bin/kitty"):
            self.assertEqual(
                terminal_launch_command(["bash", "-lc", "echo hello"]),
                ["kitty", "--", "bash", "-lc", "echo hello"],
            )

    def test_kde_setting_takes_priority_over_installed_alacritty(self):
        class Result:
            returncode = 0
            stdout = "konsole\n"

        with patch.dict(os.environ, {"TERMINAL": "", "XDG_CURRENT_DESKTOP": "KDE"}), \
             patch("utils.terminal.shutil.which", return_value="/usr/bin/konsole"), \
             patch("utils.terminal.subprocess.run", return_value=Result()):
            self.assertEqual(
                terminal_launch_command(["bash", "-lc", "echo hello"]),
                ["konsole", "-e", "bash", "-lc", "echo hello"],
            )


if __name__ == "__main__":
    unittest.main()
