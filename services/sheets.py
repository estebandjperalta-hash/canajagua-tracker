"""
Google Sheets service para Canajagua Tracker.

Hoja "checks": key | value | week | day_idx | block_idx | ex_idx | updated_at
Hoja "notes":  key | note  | week | day_idx | updated_at
"""

import streamlit as st
from datetime import datetime


class SheetsService:

    SHEET_NAME = "Canajagua_Tracker"
    TAB_CHECKS = "checks"
    TAB_NOTES  = "notes"

    def __init__(self):
        self._client       = None
        self._ws_checks    = None
        self._ws_notes     = None
        self._online       = False
        self._cache_checks = {}
        self._cache_notes  = {}
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

            # Tab checks
            try:
                ws_checks = sh.worksheet(self.TAB_CHECKS)
            except gspread.WorksheetNotFound:
                ws_checks = sh.add_worksheet(title=self.TAB_CHECKS, rows=5000, cols=8)
                ws_checks.append_row(["key","value","week","day_idx","block_idx","ex_idx","updated_at"])

            # Tab notes
            try:
                ws_notes = sh.worksheet(self.TAB_NOTES)
            except gspread.WorksheetNotFound:
                ws_notes = sh.add_worksheet(title=self.TAB_NOTES, rows=2000, cols=5)
                ws_notes.append_row(["key","note","week","day_idx","updated_at"])

            self._client    = client
            self._ws_checks = ws_checks
            self._ws_notes  = ws_notes
            self._online    = True

        except Exception:
            self._online = False

    @property
    def is_online(self):
        return self._online

    # ── CHECKS ──────────────────────────────────────────────
    def load_all_checks(self) -> dict:
        if not self._online:
            return {}
        try:
            records = self._ws_checks.get_all_records()
            result  = {}
            for row in records:
                key = str(row.get("key", "")).strip()
                val = str(row.get("value", "0")).strip()
                if key:
                    result[key] = val == "1"
            self._cache_checks = result
            return result
        except Exception:
            return {}

    def save_check(self, key: str, value: bool,
                   week=None, day_idx=None,
                   block_idx=None, ex_idx=None):
        self._cache_checks[key] = value
        if not self._online:
            return
        try:
            cell = self._ws_checks.find(key, in_column=1)
            if cell:
                self._ws_checks.update_cell(cell.row, 2, "1" if value else "0")
                self._ws_checks.update_cell(cell.row, 7, datetime.now().isoformat())
            else:
                self._ws_checks.append_row([
                    key,
                    "1" if value else "0",
                    week if week is not None else "",
                    day_idx if day_idx is not None else "",
                    block_idx if block_idx is not None else "",
                    ex_idx if ex_idx is not None else "",
                    datetime.now().isoformat(),
                ])
        except Exception:
            pass

    # ── NOTES ───────────────────────────────────────────────
    def load_all_notes(self) -> dict:
        """Retorna dict {key: str}"""
        if not self._online:
            return {}
        try:
            records = self._ws_notes.get_all_records()
            result  = {}
            for row in records:
                key  = str(row.get("key", "")).strip()
                note = str(row.get("note", "")).strip()
                if key:
                    result[key] = note
            self._cache_notes = result
            return result
        except Exception:
            return {}

    def save_note(self, key: str, note: str, week=None, day_idx=None):
        """Guarda o actualiza una nota."""
        self._cache_notes[key] = note
        if not self._online:
            return
        try:
            cell = self._ws_notes.find(key, in_column=1)
            if cell:
                self._ws_notes.update_cell(cell.row, 2, note)
                self._ws_notes.update_cell(cell.row, 5, datetime.now().isoformat())
            else:
                self._ws_notes.append_row([
                    key,
                    note,
                    week if week is not None else "",
                    day_idx if day_idx is not None else "",
                    datetime.now().isoformat(),
                ])
        except Exception:
            pass

    # ── CLEAR ───────────────────────────────────────────────
    def clear_all(self):
        self._cache_checks = {}
        self._cache_notes  = {}
        if not self._online:
            return
        try:
            self._ws_checks.clear()
            self._ws_checks.append_row(["key","value","week","day_idx","block_idx","ex_idx","updated_at"])
            self._ws_notes.clear()
            self._ws_notes.append_row(["key","note","week","day_idx","updated_at"])
        except Exception:
            pass
