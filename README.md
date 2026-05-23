# 🏔 Canajagua 30K Tracker

Streamlit app para registrar el plan de entrenamiento Canajagua 30K (18 mayo → 16 agosto 2026).
Guarda los checks en Google Sheets automáticamente.

---

## Estructura del proyecto

```
canajagua_app/
├── app.py                          # App principal Streamlit
├── requirements.txt
├── .gitignore
├── data/
│   ├── __init__.py
│   └── plan.py                     # Las 13 semanas completas
├── services/
│   ├── __init__.py
│   └── sheets.py                   # Conexión con Google Sheets
└── .streamlit/
    ├── config.toml                 # Tema oscuro
    ├── secrets.toml                # TUS credenciales (NO subir a GitHub)
    └── secrets.toml.template       # Plantilla de ejemplo
```

---

## Setup paso a paso

### 1. Clonar y preparar el entorno

```bash
# En VS Code, abre la terminal (Ctrl+`)
cd canajagua_app
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Crear el Service Account en Google Cloud

1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un proyecto nuevo o usa uno existente
3. Activa las APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Ve a **IAM & Admin → Service Accounts**
5. Crea un nuevo Service Account (nombre: `canajagua-tracker`)
6. En el Service Account, ve a **Keys → Add Key → Create new key → JSON**
7. Descarga el archivo JSON

### 3. Configurar las credenciales localmente

```bash
# Copia la plantilla
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Abre `.streamlit/secrets.toml` y reemplaza con los valores del JSON descargado:
- `project_id` → `"project_id"` del JSON
- `private_key_id` → `"private_key_id"` del JSON
- `private_key` → `"private_key"` del JSON (incluye los `\n`)
- `client_email` → `"client_email"` del JSON
- `client_id` → `"client_id"` del JSON
- `client_x509_cert_url` → `"client_x509_cert_url"` del JSON

### 4. Crear y compartir el Google Sheet

1. Ve a [sheets.google.com](https://sheets.google.com) y crea un nuevo Sheet
2. Nómbralo exactamente: **`Canajagua_Tracker`**
3. Comparte el Sheet con el email del Service Account (el `client_email` del JSON)
   - Permisos: **Editor**

> **Alternativa:** La app puede crear el Sheet automáticamente la primera vez que se ejecuta si el Service Account tiene permisos de Drive.

### 5. Correr localmente

```bash
streamlit run app.py
```

Abre `http://localhost:8501` en el browser.

---

## Deploy en Streamlit Cloud

### 1. Subir a GitHub

```bash
git init
git add .
git commit -m "Initial commit - Canajagua Tracker"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/canajagua-tracker.git
git push -u origin main
```

> ⚠️ **Verifica que `.streamlit/secrets.toml` NO se subió** (está en `.gitignore`)

### 2. Deploy en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu cuenta de GitHub
3. **New app** → selecciona el repo `canajagua-tracker`
4. Main file path: `app.py`
5. En **Advanced settings → Secrets**, copia el contenido de tu `secrets.toml`
6. **Deploy**

En ~2 minutos tendrás una URL pública como:
`https://canajagua-tracker-esteban.streamlit.app`

### 3. Agregar al teléfono como acceso directo

**Android (Chrome):**
1. Abre la URL en Chrome
2. Menú (⋮) → **Agregar a pantalla de inicio**
3. Se instala como app en tu teléfono

**iPhone (Safari):**
1. Abre la URL en Safari
2. Botón de compartir → **Agregar a pantalla de inicio**

---

## Estructura del Google Sheet

La app crea automáticamente la hoja **`checks`** con estas columnas:

| key | value | week | day_idx | block_idx | ex_idx | updated_at |
|-----|-------|------|---------|-----------|--------|------------|
| w1_d0_day | 1 | 1 | 0 | | | 2026-05-18T... |
| w1_d0_b0_e2 | 1 | 1 | 0 | 0 | 2 | 2026-05-18T... |

- `key`: identificador único del check
- `value`: `1` = completado, `0` = no completado
- `block_idx` y `ex_idx` vacíos = check de día completo

---

## Modo offline

Si no hay credenciales configuradas (o falla la conexión), la app funciona en **modo offline**: los checks se guardan en memoria de sesión. Si cierras el browser se pierden. Ideal para probar localmente antes de configurar Sheets.

---

## Notas

- El plan corre del **18 mayo al 16 agosto 2026** (13 semanas)
- Los datos en Sheets persisten entre sesiones y dispositivos
- Puedes abrir la misma URL desde el teléfono y la computadora
