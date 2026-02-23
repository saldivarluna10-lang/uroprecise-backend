from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

# 1. Configuración de la API
# ¡AQUÍ PON TU CLAVE REAL DE GEMINI!
API_KEY = "TU_API_KEY_AQUI"
genai.configure(api_key=API_KEY)

# 2. Inicializar la app
app = FastAPI(title="UroPrecise Backend", version="2.0")

# 3. Configurar CORS (Permite que GitHub hable con tu Mac)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Estructura de datos
class DatosClinicos(BaseModel):
    edad: int
    estadio_clinico: str
    volumen_enfermedad: str
    estado_funcional_ECOG: int
    tratamientos_previos: list[str]

class PerfilPaciente(BaseModel):
    paciente_id: str
    datos_clinicos: DatosClinicos
    comorbilidades: list[str]
    medicamentos_concomitantes: list[str]

# 5. El Prompt Maestro
INSTRUCCION_SISTEMA = """
Eres el motor clínico avanzado de Inteligencia Artificial "UroPrecise", diseñado para asistir a especialistas en Uro-Oncología. 
Tu función es sugerir el Inhibidor de la Vía del Receptor de Andrógenos (ARPI) óptimo para cáncer de próstata avanzado, basándote estrictamente en las guías NCCN, AUA y EAU (actualizadas a 2026).

Fase 1: DECISIÓN ONCOLÓGICA Y COMORBILIDADES
1. nmCRPC: Darolutamida (si hay riesgo/fragilidad). Apalutamida/Enzalutamida (si fit). NUNCA Abiraterona.
2. mHSPC: EVITAR Abiraterona si hay diabetes mal controlada. EVITAR Enzalutamida si hay convulsiones. Sugerir Triple Terapia (ARASENS) o Doble (ARANOTE/TITAN).
3. mCRPC: Falla a Abiraterona -> NO dar Enzalutamida. 

Fase 2: INTERACCIONES MEDICAMENTOSAS
- ENZALUTAMIDA/APALUTAMIDA: ALERTA ROJA con Anticoagulantes (Apixabán, Rivaroxabán), Estatinas, Amlodipino por inducción CYP3A4.
- ABIRATERONA: ALERTA ROJA con Metoprolol/Antidepresivos por inhibición CYP2D6.

RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA:
{
  "farmaco_recomendado": "Nombre genérico",
  "justificacion_clinica": "Explicación detallada",
  "alertas_interacciones": [{"medicamento_ingresado": "Fármaco", "riesgo_detectado": "Riesgo"}],
  "evidencia_guias_2026": "Cita de estudio pivote"
}
"""

modelo_gemini = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=INSTRUCCION_SISTEMA,
    generation_config={"response_mime_type": "application/json"}
)

# 6. La Ruta Segura
@app.post("/api/analizar-paciente")
async def analizar_paciente(perfil: PerfilPaciente):
    try:
        datos_json = perfil.model_dump_json()
        respuesta = modelo_gemini.generate_content(datos_json)
        resultado_ia = json.loads(respuesta.text)
        return resultado_ia
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA: {str(e)}")

