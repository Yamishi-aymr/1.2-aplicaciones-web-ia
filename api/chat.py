import json
import os

from http.server import BaseHTTPRequestHandler
from openai import OpenAI


ALLOWED_ORIGIN = os.environ.get(
    "ALLOWED_ORIGIN",
    ""
).rstrip("/")


class handler(BaseHTTPRequestHandler):

    def add_cors_headers(self):

        origin = self.headers.get("Origin", "")

        if ALLOWED_ORIGIN and origin == ALLOWED_ORIGIN:

            self.send_header(
                "Access-Control-Allow-Origin",
                origin
            )

            self.send_header(
                "Vary",
                "Origin"
            )


    def send_json(self, status_code, data):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.add_cors_headers()

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)


    def do_OPTIONS(self):

        origin = self.headers.get("Origin", "")

        if ALLOWED_ORIGIN and origin != ALLOWED_ORIGIN:

            self.send_response(403)

            self.end_headers()

            return

        self.send_response(204)

        self.add_cors_headers()

        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Access-Control-Max-Age",
            "86400"
        )

        self.end_headers()


    def do_GET(self):

        self.send_json(
            405,
            {
                "error":
                    "Este endpoint solamente acepta POST."
            }
        )


    def do_POST(self):

        try:

            # ==================================================
            # VALIDAR ORIGEN
            # ==================================================

            origin = self.headers.get(
                "Origin",
                ""
            )

            if ALLOWED_ORIGIN and origin != ALLOWED_ORIGIN:

                self.send_json(
                    403,
                    {
                        "error":
                            "Origen no autorizado."
                    }
                )

                return


            # ==================================================
            # VALIDAR TAMAÑO DE LA PETICIÓN
            # ==================================================

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )


            if (
                content_length <= 0
                or content_length > 50000
            ):

                self.send_json(
                    413,
                    {
                        "error":
                            "Petición no válida o demasiado grande."
                    }
                )

                return


            # ==================================================
            # LEER JSON
            # ==================================================

            body = self.rfile.read(
                content_length
            )

            data = json.loads(
                body.decode("utf-8")
            )


            # ==================================================
            # OBTENER HISTORIAL
            # ==================================================

            messages = data.get(
                "messages",
                []
            )


            if not isinstance(messages, list):

                self.send_json(
                    400,
                    {
                        "error":
                            "El historial de mensajes no es válido."
                    }
                )

                return


            if len(messages) == 0:

                self.send_json(
                    400,
                    {
                        "error":
                            "Es necesario enviar al menos un mensaje."
                    }
                )

                return


            # ==================================================
            # VALIDAR Y LIMPIAR MENSAJES
            # ==================================================

            clean_messages = []


            for item in messages:

                if not isinstance(item, dict):

                    continue


                role = item.get(
                    "role"
                )

                content = str(
                    item.get(
                        "content",
                        ""
                    )
                ).strip()


                if role not in [
                    "user",
                    "assistant"
                ]:

                    continue


                if not content:

                    continue


                if len(content) > 4000:

                    content = content[:4000]


                clean_messages.append(
                    {
                        "role": role,
                        "content": content
                    }
                )


            if len(clean_messages) == 0:

                self.send_json(
                    400,
                    {
                        "error":
                            "No se encontraron mensajes válidos."
                    }
                )

                return


            # ==================================================
            # LIMITAR HISTORIAL
            # ==================================================

            clean_messages = clean_messages[-12:]


            # ==================================================
            # API KEY
            # ==================================================

            api_key = os.environ.get(
                "OPENAI_API_KEY"
            )


            if not api_key:

                self.send_json(
                    500,
                    {
                        "error":
                            "OPENAI_API_KEY no está configurada."
                    }
                )

                return


            # ==================================================
            # CLIENTE OPENAI
            # ==================================================

            client = OpenAI(
                api_key=api_key
            )


            # ==================================================
            # CONSULTAR MODELO
            # ==================================================

            response = client.responses.create(

                model="gpt-5.6-luna",

                instructions="""
                Eres un asistente educativo especializado
                en Tecnologías de Información y Comunicaciones.

                Responde siempre en español, de manera clara,
                breve y didáctica.

                Usa el historial de conversación para mantener
                el contexto.

                Si el usuario utiliza expresiones como:
                "esto", "eso", "lo anterior", "las", "ellos",
                "con base en lo anterior" o referencias similares,
                interpreta esas expresiones usando los mensajes
                anteriores de la conversación.

                No pidas nuevamente información que ya aparezca
                claramente en el historial.

                Incluye ejemplos cuando ayuden
                a comprender el concepto.
                """,

                input=clean_messages,

                reasoning={
                    "effort": "none"
                },

                max_output_tokens=500
            )


            # ==================================================
            # RESPUESTA
            # ==================================================

            self.send_json(
                200,
                {
                    "reply":
                        response.output_text
                }
            )


        except json.JSONDecodeError:

            self.send_json(
                400,
                {
                    "error":
                        "El cuerpo no contiene JSON válido."
                }
            )


        except Exception as error:

            print(
                f"Error en /api/chat: "
                f"{type(error).__name__}: {error}"
            )

            self.send_json(
                500,
                {
                    "error":
                        "No fue posible consultar el modelo de IA."
                }
            )