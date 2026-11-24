import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from utils.enable_multilib import enabled_config
from utils.gaming_packages import graphics_packages
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


class GraphicsPackageTests(unittest.TestCase):
    @staticmethod
    def add_device(root, name, vendor, device_class="0x030000"):
        device = Path(root) / name
        device.mkdir()
        (device / "class").write_text(device_class)
        (device / "vendor").write_text(vendor)

    def test_hybrid_amd_intel_gets_matching_32_bit_vulkan_libraries(self):
        with tempfile.TemporaryDirectory() as root:
            self.add_device(root, "amd", "0x1002")
            self.add_device(root, "intel", "0x8086")
            packages = graphics_packages(set(), root)
        self.assertEqual(packages.count("lib32-mesa"), 1)
        self.assertIn("lib32-vulkan-radeon", packages)
        self.assertIn("lib32-vulkan-intel", packages)

    def test_nvidia_requires_installed_driver(self):
        with tempfile.TemporaryDirectory() as root:
            self.add_device(root, "nvidia", "0x10de")
            self.assertEqual(graphics_packages(set(), root), [])
            self.assertEqual(
                graphics_packages({"nvidia-utils"}, root), ["lib32-nvidia-utils"]
            )

    def test_non_display_device_is_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            self.add_device(root, "network", "0x1002", "0x020000")
            self.assertEqual(graphics_packages(set(), root), [])


if __name__ == "__main__":
    unittest.main()
