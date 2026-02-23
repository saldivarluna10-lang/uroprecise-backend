from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

# ==========================================
# 1. CONFIGURACIÓN DE LA API
# ==========================================
API_KEY = "AIzaSyC15k5n-6eqqvFOaAkElQCc_7E9FOkvyS0" # <--- ¡PEGA TU CLAVE QUE TERMINA EN vyS0 AQUÍ!
genai.configure(api_key=API_KEY)

app = FastAPI(title="UroPrecise Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

INSTRUCCION_SISTEMA = """
Eres el motor clínico avanzado de Inteligencia Artificial "UroPrecise", diseñado para asistir a especialistas en Uro-Oncología. 
Tu función es sugerir el Inhibidor de la Vía del Receptor de Andrógenos (ARPI) óptimo para cáncer de próstata avanzado.

Fase 1: DECISIÓN ONCOLÓGICA Y COMORBILIDADES
1. nmCRPC: Darolutamida (si hay riesgo/fragilidad). Apalutamida/Enzalutamida (si fit). NUNCA Abiraterona.
2. mHSPC: EVITAR Abiraterona si hay diabetes mal controlada. EVITAR Enzalutamida si hay convulsiones. Sugerir Triple Terapia o Doble.
3. mCRPC: Falla a Abiraterona -> NO dar Enzalutamida. 

Fase 2: INTERACCIONES MEDICAMENTOSAS
- ENZALUTAMIDA/APALUTAMIDA: ALERTA ROJA con Anticoagulantes (Apixabán, Rivaroxabán), Estatinas, Amlodipino por inducción CYP3A4.
- ABIRATERONA: ALERTA ROJA con Metoprolol/Antidepresivos por inhibición CYP2D6.

RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA, SIN NINGÚN TEXTO ADICIONAL ANTES NI DESPUÉS:
{
  "farmaco_recomendado": "Nombre genérico",
  "justificacion_clinica": "Explicación detallada",
  "alertas_interacciones": [{"medicamento_ingresado": "Fármaco", "riesgo_detectado": "Riesgo"}],
  "evidencia_guias_2026": "Cita de estudio pivote"
}
"""

# Usamos el modelo clásico universal de Google
modelo_gemini = genai.GenerativeModel("gemini-pro")

@app.post("/api/analizar-paciente")
async def analizar_paciente(perfil: PerfilPaciente):
    try:
        print(f"🏥 Procesando paciente: {perfil.paciente_id}")
        datos_json = perfil.model_dump_json()
        
        # Combinamos la instrucción y los datos en una sola inyección
        prompt_final = f"{INSTRUCCION_SISTEMA}\n\nDATOS DEL PACIENTE:\n{datos_json}"
        
        # Enviar a Gemini
        respuesta = modelo_gemini.generate_content(prompt_final)
        texto_respuesta = respuesta.text
        print(f"🧠 Respuesta cruda de Gemini: {texto_respuesta}")
        
        # Limpieza brutal de Markdown por si Gemini añade formato
        texto_limpio = texto_respuesta.replace("```json", "").replace("```", "").strip()
            
        resultado_ia = json.loads(texto_limpio)
        print("✅ Análisis JSON exitoso.")
        return resultado_ia
        
    except Exception as e:
        print(f"🚨 ERROR FATAL EN EL SERVIDOR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
