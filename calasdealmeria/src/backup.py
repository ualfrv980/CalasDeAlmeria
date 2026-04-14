import os
import shutil
import winreg
from datetime import date


BACKUP_FOLDER_NAME = "CalasDeAlmeria"
MAX_BACKUPS = 7


def _find_google_drive_path() -> str | None:
    """Intenta encontrar la carpeta de Google Drive en Windows."""

    # 1. Buscar en el registro (Google Drive for Desktop moderno)
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Google\DriveFS", "RootPath"),
        (winreg.HKEY_CURRENT_USER, r"Software\Google\Drive", "Path"),
    ]
    for hive, key_path, value_name in registry_paths:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                path, _ = winreg.QueryValueEx(key, value_name)
                if path and os.path.isdir(path):
                    return path
        except (FileNotFoundError, OSError):
            pass

    # 2. Buscar rutas comunes
    home = os.path.expanduser("~")
    common_paths = [
        os.path.join(home, "Google Drive"),
        os.path.join(home, "My Drive"),
        os.path.join(home, "GoogleDrive"),
        os.path.join(home, "Google Drive (Stream)"),
        "C:\\Google Drive",
        "D:\\Google Drive",
    ]
    for path in common_paths:
        if os.path.isdir(path):
            return path

    # 3. Buscar drives mapeados (G:, H:, etc.)
    for letter in "GHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:\\"
        if os.path.isdir(drive):
            marker = os.path.join(drive, ".shortcut-targets-by-id")
            if os.path.exists(marker):
                return drive

    return None


def _clean_old_backups(backup_dir: str):
    """Elimina backups antiguos, conserva solo los ultimos MAX_BACKUPS."""
    try:
        files = [
            f for f in os.listdir(backup_dir)
            if f.startswith("calasdealmeria_") and f.endswith(".db")
        ]
        files.sort(reverse=True)
        for old_file in files[MAX_BACKUPS:]:
            os.remove(os.path.join(backup_dir, old_file))
    except Exception:
        pass


def make_backup(db_path: str) -> tuple[bool, str]:
    """
    Copia la base de datos a Google Drive.
    Devuelve (exito, mensaje).
    """
    if not os.path.isfile(db_path):
        return False, "No se encontro la base de datos."

    drive_root = _find_google_drive_path()
    if not drive_root:
        return False, "Google Drive no encontrado."

    backup_dir = os.path.join(drive_root, BACKUP_FOLDER_NAME)
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except Exception as e:
        return False, f"No se pudo crear la carpeta de backup: {e}"

    today = date.today().strftime("%Y-%m-%d")
    dest = os.path.join(backup_dir, f"calasdealmeria_{today}.db")

    try:
        shutil.copy2(db_path, dest)
        _clean_old_backups(backup_dir)
        return True, f"Copia guardada en Google Drive ({today})"
    except Exception as e:
        return False, f"Error al copiar: {e}"
