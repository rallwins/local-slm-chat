const messagesContainer =
    document.getElementById("messages");

const input =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendButton");

const modelSelect =
    document.getElementById("modelSelect");

const newChatButton =
    document.getElementById("newChat");


let conversation = [];


/* -----------------------------------
   Load models
----------------------------------- */

async function loadModels() {

    const response =
        await fetch("/api/models");

    const data =
        await response.json();

    modelSelect.innerHTML = "";

    data.models.forEach(model => {

        const option =
            document.createElement("option");

        option.value = model;

        option.textContent = model;

        modelSelect.appendChild(option);

    });
}


/* -----------------------------------
   Add message to UI
----------------------------------- */

function addMessage(role, content = "") {

    const message =
        document.createElement("div");

    message.className =
        "message";

    const roleElement =
        document.createElement("div");

    roleElement.className =
        "message-role " +
        (role === "user"
            ? "user-role"
            : "assistant-role");

    roleElement.textContent =
        role === "user"
            ? "You"
            : "AI";


    const contentElement =
        document.createElement("div");

    contentElement.className =
        "message-content";

    contentElement.textContent =
        content;


    message.appendChild(roleElement);

    message.appendChild(contentElement);

    messagesContainer.appendChild(message);

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;


    return contentElement;
}


/* -----------------------------------
   Send message
----------------------------------- */

async function sendMessage() {

    const message =
        input.value.trim();

    if (!message) {
        return;
    }


    const model =
        modelSelect.value;


    input.value = "";

    sendButton.disabled = true;


    /* Remove welcome screen */

    const welcome =
        document.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }


    /* Add user message */

    addMessage(
        "user",
        message
    );


    conversation.push({
        role: "user",
        content: message
    });


    /* Create assistant message */

    const assistantContent =
        addMessage(
            "assistant",
            ""
        );


    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        model: model,
                        messages: conversation
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Chat request failed"
            );

        }


        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder();


        let assistantMessage = "";


        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {
                break;
            }


            const chunk =
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            assistantMessage += chunk;


            assistantContent.textContent =
                assistantMessage;


            messagesContainer.scrollTop =
                messagesContainer.scrollHeight;
        }


        /* Save assistant response */

        conversation.push({
            role: "assistant",
            content: assistantMessage
        });


    } catch (error) {

        assistantContent.textContent =
            "Error: " + error.message;

    } finally {

        sendButton.disabled = false;

        input.focus();
    }
}


/* -----------------------------------
   Enter key
----------------------------------- */

input.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }

    }
);


/* -----------------------------------
   Send button
----------------------------------- */

sendButton.addEventListener(
    "click",
    sendMessage
);


/* -----------------------------------
   New chat
----------------------------------- */

newChatButton.addEventListener(
    "click",
    () => {

        conversation = [];

        messagesContainer.innerHTML = `
            <div class="welcome">
                <h1>Local SLM Chat</h1>
                <p>
                    Ask anything. Your conversation
                    stays on your machine.
                </p>
            </div>
        `;

        input.focus();
    }
);


/* -----------------------------------
   Start application
----------------------------------- */

loadModels();

input.focus();