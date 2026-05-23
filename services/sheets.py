"""
Google Sheets service for Canajagua Tracker.
Guarda y carga checks de entrenamiento en un Google Sheet.

Sheet "checks" tiene columnas:
  key | value | week | day_idx | block_idx | ex_idx | updated_at
"""

import streamlit as st
from datetime import datetime
import json


class SheetsService:
    """
    Conecta con Google Sheets via gspread usando las credenciales
    almacenadas en st.secrets["gcp_service_account"].
    
    Si no hay credenciales configuradas (dev local sin secrets),
    cae gracefully a modo offline (solo memoria).
    """

    SHEET_NAME  = "Canajagua_Tracker"
    TAB_CHECKS  = "checks"

    def __init__(self):
        self._client  = None
        self._sheet   = None
        self._online  = False
        self._cache   = {}          # key → bool
        self._dirty   = set()       # keys pendientes de flush
        self._connect()

    # ── CONEXIÓN ────────────────────────────────────────────
    def _connect(self):
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)

            try:
                sh = client.open(self.SHEET_NAME)
            except gspread.SpreadsheetNotFound:
                sh = client.create(self.SHEET_NAME)
                sh.share(creds_dict["client_email"], perm_type="user", role="writer")

            # Crear tab "checks" si no existe
            try:
                ws = sh.worksheet(self.TAB_CHECKS)
            except gspread.WorksheetNotFound:
                ws = sh.add_worksheet(title=self.TAB_CHECKS, rows=5000, cols=8)
                ws.append_row(["key","value","week","day_idx","block_idx","ex_idx","updated_at"])

            self._client = client
            self._sheet  = ws
            self._online = True

        except Exception as e:
            # Sin credenciales o error de red → modo offline
            self._online = False

    @property
    def is_online(self):
        return self._online

    # ── LOAD ALL ────────────────────────────────────────────
    def load_all_checks(self) -> dict:
        """Carga todos los checks del sheet y retorna dict {key: bool}."""
        if not self._online:
            return {}
        try:
            records = self._sheet.get_all_records()
            result  = {}
            for row in records:
                key = str(row.get("key", "")).strip()
                val = str(row.get("value", "0")).strip()
                if key:
                    result[key] = val == "1"
            self._cache = result
            return result
        except Exception:
            return {}

    # ── SAVE CHECK ──────────────────────────────────────────
    def save_check(self, key: str, value: bool,
                   week=None, day_idx=None,
                   block_idx=None, ex_idx=None):
        """
        Guarda o actualiza un check en el sheet.
        Busca la fila por key; si existe la actualiza, si no la agrega.
        """
        self._cache[key] = value

        if not self._online:
            return

        try:
            cell = self._sheet.find(key, in_column=1)
            if cell:
                self._sheet.update_cell(cell.row, 2, "1" if value else "0")
                self._sheet.update_cell(cell.row, 7, datetime.now().isoformat())
            else:
                self._sheet.append_row([
                    key,
                    "1" if value else "0",
                    week if week is not None else "",
                    day_idx if day_idx is not None else "",
                    block_idx if block_idx is not None else "",
                    ex_idx if ex_idx is not None else "",
                    datetime.now().isoformat(),
                ])
        except Exception:
            # Si falla el sheet, al menos está en cache de sesión
            pass

    # ── BULK SAVE ───────────────────────────────────────────
    def bulk_save(self, checks: dict):
        """Guarda todos los checks de una vez (para migración o sync inicial)."""
        if not self._online:
            return
        try:
            existing = self._sheet.get_all_records()
            existing_keys = {r["key"]: i + 2 for i, r in enumerate(existing)}  # row numbers (1-indexed + header)

            rows_to_append = []
            now = datetime.now().isoformat()
            for key, value in checks.items():
                if key in existing_keys:
                    row_num = existing_keys[key]
                    self._sheet.update_cell(row_num, 2, "1" if value else "0")
                    self._sheet.update_cell(row_num, 7, now)
                else:
                    rows_to_append.append([key, "1" if value else "0", "", "", "", "", now])

            if rows_to_append:
                self._sheet.append_rows(rows_to_append)
        except Exception:
            pass

    # ── CLEAR ALL ───────────────────────────────────────────
    def clear_all(self):
        """Borra todos los checks (útil para reset)."""
        self._cache = {}
        if not self._online:
            return
        try:
            self._sheet.clear()
            self._sheet.append_row(["key","value","week","day_idx","block_idx","ex_idx","updated_at"])
        except Exception:
            pass
