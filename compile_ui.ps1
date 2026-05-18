# compile_ui.ps1
$uic = ".\.venv\Scripts\pyside6-uic.exe"
$components = "nav_bar", "channel_list_panel", "user_status_bar", "chat_view", "main_window"

New-Item -ItemType Directory -Force -Path src/build/components/ui/compiled | Out-Null

foreach ($name in $components) {
    & $uic "src/components/$name.ui" -o "src/build/components/ui/compiled/${name}_ui.py"
    Write-Host "Compiled $name.ui"
}