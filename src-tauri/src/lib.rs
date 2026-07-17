use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use std::sync::Mutex;

struct SidecarState {
    port: u16,
}

#[tauri::command]
fn get_sidecar_port(state: tauri::State<Mutex<SidecarState>>) -> u16 {
    state.lock().unwrap().port
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port: u16 = 17865;

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(Mutex::new(SidecarState { port }))
        .invoke_handler(tauri::generate_handler![get_sidecar_port])
        .setup(move |app| {
            // Start the Python sidecar
            let sidecar = app.shell().sidecar("python-sidecar")
                .expect("failed to create python-sidecar command")
                .env("SIDECAR_PORT", port.to_string());

            let (mut rx, _child) = sidecar.spawn().expect("Failed to spawn Python sidecar");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Stdout(line) = event {
                        println!("[sidecar] {}", String::from_utf8_lossy(&line));
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
