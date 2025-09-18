# Custom ROM Tool

A Python-based tool to manage and flash ROMs and recoveries for multiple Android devices. This tool provides a simple GUI interface using **CustomTkinter** for selecting devices, browsing ROMs/recoveries, and performing fastboot/ADB operations.

---

## Features

* Detect connected devices via **ADB**.
* Flash ROMs and recoveries to multiple devices.
* Custom commands execution.
* Interactive GUI for easy navigation.
* Logging of all operations.

---

## Folder Structure

```
CustomRoms/                <- Main directory
│
├─ Poco F1/                <- Device folder example
│  ├─ Roms/                <- ROM files
│  └─ Recoverys/           <- Recovery files
│     └─ Boot/             <- Boot files
│
├─ Poco F6/                <- Another device folder example
│  ├─ Roms/
│  └─ Recoverys/
│     └─ Boot/
│
└─ RomTool.py              <- Your main script
```

> **Note:** Add your devices as separate folders inside `CustomRoms/`. Place ROMs in the `Roms/` folder and recovery and super_empty files in `Recoverys` and Boot imgs in `Boot` .

---

## Dependencies

### Python Libraries

Install the required Python packages using pip:

```bash
pip install customtkinter
```

### External Tools

This tool depends on **ADB** and **Fastboot**. You must install them separately:

1. **Download Platform Tools:**
   [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)

2. **Extract and Add to PATH:**

   * **Windows:** Add the `platform-tools` folder to your system PATH.
   * **Linux/macOS:** Add the folder to your PATH in `~/.bashrc` or `~/.zshrc`.

3. **Verify Installation:**

```bash
adb --version
fastboot --version
```

Both commands should return version information.

---

## Usage

1. **Open the Script:**
   Run the main script:

```bash
python RomTool.py
```

2. **Select a Device Folder:**
   The GUI will prompt you to select a device folder (e.g., `Poco F1`). This folder must contain the `Roms` and `Recoverys` subfolders.

3. **Perform Operations:**

   * View available ROMs and recovery files.
   * Flash ROMs, recoveries, or boot images using ADB/Fastboot.
   * Execute custom commands.

4. **Logging:**
   All operations are logged in `Logs/Tool.log` for reference.

---

## Notes

* Ensure **USB Debugging** is enabled on your Android device.
* Device drivers must be installed on your PC for proper ADB/Fastboot detection.
* Recommended to back up your device before flashing any ROMs or recovery files.

---

## License

This project is open-source. You are free to use, modify, and distribute under the terms of the MIT License.
