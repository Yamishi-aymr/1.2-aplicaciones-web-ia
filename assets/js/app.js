const API_URL =
    "https://1-2-aplicaciones-web-ia-git-main-alice-70fd.vercel.app/api/chat";


const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("sendButton");


/* ==================================================
   HISTORIAL DE CONVERSACIÓN
================================================== */

const conversationHistory = [];

function addMessage(text, type) {

    const container = document.createElement("div");

    container.classList.add("message", type);


    const label = document.createElement("div");

    label.classList.add("message-label");

    label.textContent =
        type === "user"
            ? "Tú"
            : "IA";


    const content = document.createElement("div");

    content.classList.add("message-content");


    /*
        Las respuestas del asistente pueden
        contener Markdown.
    */

    if (type === "assistant") {

        content.innerHTML =
            marked.parse(text);

    } else {

        content.textContent = text;

    }


    container.appendChild(label);

    container.appendChild(content);

    messages.appendChild(container);


    messages.scrollTop =
        messages.scrollHeight;


    return container;
}


/* ==================================================
   GUARDAR MENSAJE EN EL HISTORIAL
================================================== */

function saveToHistory(role, content) {

    conversationHistory.push({
        role: role,
        content: content
    });


    /*
        Esto es opcional.
        Sirve para revisar el historial
        desde la consola del navegador.
    */

    console.log(
        "Historial:",
        conversationHistory
    );
}


/* ==================================================
   ENVIAR MENSAJE
================================================== */

form.addEventListener(
    "submit",

    async (event) => {

        event.preventDefault();


        const message =
            input.value.trim();


        if (!message) {
            return;
        }


        /* ==========================================
           MOSTRAR MENSAJE DEL USUARIO
        ========================================== */

        addMessage(
            message,
            "user"
        );


        /* ==========================================
           GUARDAR MENSAJE DEL USUARIO
        ========================================== */

        saveToHistory(
            "user",
            message
        );


        input.value = "";

        input.disabled = true;

        sendButton.disabled = true;


        /* ==========================================
           MENSAJE DE CARGA
        ========================================== */

        const loading =
            addMessage(
                "Pensando...",
                "loading"
            );


        try {

            /* ======================================
               PETICIÓN AL BACKEND
            ====================================== */

            const response =
                await fetch(
                    API_URL,
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },


                        body: JSON.stringify({

                            /*
                                Mensaje actual
                            */

                            message: message,


                            /*
                                Conversación completa
                            */

                            history:
                                conversationHistory

                        })

                    }
                );


            const data =
                await response.json();


            loading.remove();


            /* ======================================
               VALIDAR RESPUESTA
            ====================================== */

            if (!response.ok) {

                throw new Error(

                    data.error ||
                    "Error del servidor"

                );

            }


            /* ======================================
               MOSTRAR RESPUESTA
            ====================================== */

            addMessage(
                data.reply,
                "assistant"
            );


            /* ======================================
               GUARDAR RESPUESTA DE LA IA
            ====================================== */

            saveToHistory(
                "assistant",
                data.reply
            );

        }


        catch (error) {

            loading.remove();


            addMessage(

                "Error: " +
                error.message,

                "assistant"

            );

        }


        finally {

            input.disabled = false;

            sendButton.disabled = false;

            input.focus();

        }

    }
);