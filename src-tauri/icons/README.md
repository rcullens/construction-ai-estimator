# App Icons

Tauri expects icons in this folder (32x32.png, 128x128.png, 128x128@2x.png, icon.icns, icon.ico).

Generate a full set from a single 1024×1024 PNG:

```bash
cargo tauri icon path/to/your-icon.png
```

Until you add a real icon, Tauri uses its default during development.
