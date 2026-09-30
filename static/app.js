const promptSelect =
    document.getElementById(
        "promptSelect"
    );

const messagesContainer =
    document.getElementById("messages");

const input =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendButton");

const stopButton =
    document.getElementById("stopButton");

const modelSelect =
    document.getElementById("modelSelect");

const newChatButton =
    document.getElementById("newChat");

const observabilityButton =
    document.getElementById(
        "observabilityButton"
    );

const closeObservability =
    document.getElementById(
        "closeObservability"
    );

const observabilityPanel =
    document.getElementById(
        "observabilityPanel"
    );

const refreshLogsButton =
    document.getElementById(
        "refreshLogs"
    );

const statusDot =
    document.getElementById(
        "statusDot"
    );

const statusText =
    document.getElementById(
        "statusText"
    );


let conversation = [];

let currentController = null;


/* =========================================
   LOAD MODELS
========================================= */

async function loadModels() {

    try {

        const response =
            await fetch(
                "/api/models"
            );

        if (!response.ok) {
            throw new Error(
                "Unable to load models"
            );
        }

        const data =
            await response.json();


        modelSelect.innerHTML = "";


        if (
            !data.models ||
            data.models.length === 0
        ) {

            const option =
                document.createElement(
                    "option"
                );

            option.textContent =
                "No models installed";

            modelSelect.appendChild(
                option
            );

            return;
        }


        data.models.forEach(
            model => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value = model;

                option.textContent = model;

                modelSelect.appendChild(
                    option
                );

            }
        );

    } catch (error) {

        modelSelect.innerHTML = `
            <option>
                Ollama unavailable
            </option>
        `;

        setOfflineStatus();
    }
}


/* =========================================
   HEALTH CHECK
========================================= */

async function checkHealth() {

    try {

        const response =
            await fetch(
                "/api/health"
            );

        if (!response.ok) {
            throw new Error();
        }

        setOnlineStatus();

    } catch {

        setOfflineStatus();
    }
}


function setOnlineStatus() {

    statusDot.classList.add(
        "online"
    );

    statusText.textContent =
        "Ollama online";
}


function setOfflineStatus() {

    statusDot.classList.remove(
        "online"
    );

    statusText.textContent =
        "Ollama unavailable";
}


/* =========================================
   ADD MESSAGE
========================================= */

function addMessage(
    role,
    content = ""
) {

    const message =
        document.createElement(
            "div"
        );

    message.className =
        "message";


    const roleElement =
        document.createElement(
            "div"
        );

    roleElement.className =
        "message-role " +
        (
            role === "user"
                ? "user-role"
                : "assistant-role"
        );


    roleElement.textContent =
        role === "user"
            ? "You"
            : "AI";


    const body =
        document.createElement(
            "div"
        );

    body.className =
        "message-body";


    const contentElement =
        document.createElement(
            "div"
        );

    contentElement.className =
        "message-content";

    contentElement.textContent =
        content;


    body.appendChild(
        contentElement
    );


    message.appendChild(
        roleElement
    );

    message.appendChild(
        body
    );


    messagesContainer.appendChild(
        message
    );


    scrollToBottom();


    return {
        message,
        body,
        contentElement
    };
}


/* =========================================
   METRICS
========================================= */

function addMetrics(
    body,
    metrics
) {

    const metricsElement =
        document.createElement(
            "div"
        );

    metricsElement.className =
        "metrics";


    const latency =
        metrics.total_latency_ms != null
            ? (
                metrics.total_latency_ms /
                1000
            ).toFixed(2) + "s"
            : "-";


    const ttft =
        metrics.time_to_first_token_ms != null
            ? metrics.time_to_first_token_ms
                .toFixed(0) + "ms TTFT"
            : "-";


    const speed =
        metrics.tokens_per_second != null
            ? metrics.tokens_per_second
                .toFixed(1) + " tok/s"
            : "-";


    const outputTokens =
        metrics.output_tokens != null
            ? metrics.output_tokens +
              " tokens"
            : "-";


    metricsElement.innerHTML = `
        <span>⚙ ${escapeHtml(
            metrics.model
        )}</span>

        <span>🧠 ${escapeHtml(
            metrics.prompt_template || "general"
        )}</span>

        <span>⏱ ${latency}</span>

        <span>⚡ ${speed}</span>

        <span>🕐 ${ttft}</span>

        <span>▣ ${outputTokens}</span>
    `;


    body.appendChild(
        metricsElement
    );


    const detailsButton =
        document.createElement(
            "button"
        );

    detailsButton.className =
        "details-button";

    detailsButton.textContent =
        "Show details";


    const details =
        document.createElement(
            "div"
        );

    details.className =
        "metrics-details hidden";


    details.innerHTML = `
        Request ID:
        ${escapeHtml(
            metrics.request_id || "-"
        )}
        <br>

        Model:
        ${escapeHtml(
            metrics.model || "-"
        )}
        <br>

        Prompt tokens:
        ${metrics.prompt_tokens ?? "-"}
        <br>

        Output tokens:
        ${metrics.output_tokens ?? "-"}
        <br>

        TTFT:
        ${
            metrics.time_to_first_token_ms != null
                ? metrics.time_to_first_token_ms.toFixed(2)
                : "-"
        } ms
        <br>

        Prompt evaluation:
        ${
            metrics.prompt_eval_duration_ms != null
                ? metrics.prompt_eval_duration_ms.toFixed(2)
                : "-"
        } ms
        <br>

        Generation:
        ${
            metrics.generation_time_ms != null
                ? metrics.generation_time_ms.toFixed(2)
                : "-"
        } ms
        <br>

        Total:
        ${
            metrics.total_latency_ms != null
                ? metrics.total_latency_ms.toFixed(2)
                : "-"
        } ms
        <br>

        Generation speed:
        ${
            metrics.tokens_per_second != null
                ? metrics.tokens_per_second.toFixed(2)
                : "-"
        } tokens/sec
    `;


    detailsButton.addEventListener(
        "click",
        () => {

            details.classList.toggle(
                "hidden"
            );

            detailsButton.textContent =
                details.classList.contains(
                    "hidden"
                )
                    ? "Show details"
                    : "Hide details";
        }
    );


    body.appendChild(
        detailsButton
    );

    body.appendChild(
        details
    );
}


/* =========================================
   SEND MESSAGE
========================================= */

async function sendMessage() {

    const message =
        input.value.trim();


    if (!message) {
        return;
    }


    const model =
        modelSelect.value;


    if (
        !model ||
        model === "No models installed" ||
        model === "Ollama unavailable"
    ) {

        alert(
            "Please make sure Ollama is running and a model is installed."
        );

        return;
    }


    input.value = "";

    input.style.height = "auto";


    sendButton.disabled = true;

    stopButton.classList.remove(
        "hidden"
    );


    const welcome =
        document.querySelector(
            ".welcome"
        );

    if (welcome) {
        welcome.remove();
    }


    /* -------------------------------
       User message
    ------------------------------- */

    addMessage(
        "user",
        message
    );


    conversation.push({
        role: "user",
        content: message
    });


    /* -------------------------------
       Assistant message
    ------------------------------- */

    const assistant =
        addMessage(
            "assistant",
            ""
        );


    let assistantMessage = "";


    currentController =
        new AbortController();


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

                        prompt_template:
                            promptSelect.value,

                        messages:
                            conversation

                    }),

                    signal:
                        currentController.signal
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        if (!response.body) {

            throw new Error(
                "Streaming is not supported by this browser."
            );
        }


        const reader =
            response.body.getReader();


        const decoder =
            new TextDecoder();


        let buffer = "";


        while (true) {

            const {
                value,
                done
            } =
                await reader.read();


            if (done) {
                break;
            }


            buffer += decoder.decode(
                value,
                {
                    stream: true
                }
            );


            const events =
                buffer.split(
                    "\n\n"
                );


            buffer =
                events.pop() || "";


            for (
                const eventText
                of events
            ) {

                processSSEEvent(
                    eventText,
                    assistant,
                    value => {

                        assistantMessage +=
                            value;

                        assistant.contentElement
                            .textContent =
                            assistantMessage;

                        scrollToBottom();
                    }
                );
            }
        }


        /* --------------------------------
           Save assistant response
        -------------------------------- */

        if (assistantMessage) {

            conversation.push({
                role: "assistant",
                content:
                    assistantMessage
            });

        }


    } catch (error) {

        if (
            error.name ===
            "AbortError"
        ) {

            assistant.contentElement
                .textContent +=
                "\n\n[Generation stopped]";

        } else {

            assistant.contentElement
                .textContent =
                "Error: " +
                error.message;

        }

    } finally {

        currentController = null;

        sendButton.disabled = false;

        stopButton.classList.add(
            "hidden"
        );

        input.focus();

        refreshStats();

    }
}


/* =========================================
   SSE EVENT PARSER
========================================= */

function processSSEEvent(
    eventText,
    assistant,
    onToken
) {

    const lines =
        eventText.split(
            "\n"
        );


    let eventType =
        "message";

    let data =
        "";


    for (
        const line
        of lines
    ) {

        if (
            line.startsWith(
                "event:"
            )
        ) {

            eventType =
                line.substring(
                    6
                ).trim();

        }

        else if (
            line.startsWith(
                "data:"
            )
        ) {

            data +=
                line.substring(
                    5
                ).trim();

        }
    }


    if (!data) {
        return;
    }


    try {

        const parsed =
            JSON.parse(data);


        if (
            eventType ===
            "token"
        ) {

            onToken(parsed);

        }


        else if (
            eventType ===
            "metrics"
        ) {

            addMetrics(
                assistant.body,
                parsed
            );

        }


        else if (
            eventType ===
            "error"
        ) {

            assistant.contentElement
                .textContent =
                "Error: " +
                parsed.error;

        }

    } catch {

        console.error(
            "Unable to parse SSE event:",
            eventText
        );

    }
}


/* =========================================
   STOP GENERATION
========================================= */

stopButton.addEventListener(
    "click",
    () => {

        if (currentController) {

            currentController.abort();

            currentController = null;
        }

    }
);


/* =========================================
   NEW CHAT
========================================= */

newChatButton.addEventListener(
    "click",
    () => {

        conversation = [];


        messagesContainer.innerHTML = `
            <div class="welcome">

                <div class="welcome-icon">
                    AI
                </div>

                <h1>
                    How can I help you?
                </h1>

                <p>
                    This conversation runs
                    entirely on your machine.
                </p>

                <div class="suggestions">

                    <button
                        class="suggestion"
                        data-prompt="Explain Apache Spark in simple terms."
                    >
                        Explain Apache Spark
                    </button>

                    <button
                        class="suggestion"
                        data-prompt="Write a Python function to find duplicate values in a list."
                    >
                        Write Python code
                    </button>

                    <button
                        class="suggestion"
                        data-prompt="Explain the difference between a data lake and a data warehouse."
                    >
                        Explain data engineering
                    </button>

                </div>

            </div>
        `;


        attachSuggestionHandlers();

        input.focus();
    }
);


/* =========================================
   SUGGESTIONS
========================================= */

function attachSuggestionHandlers() {

    document
        .querySelectorAll(
            ".suggestion"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        input.value =
                            button.dataset
                                .prompt;

                        sendMessage();

                    }
                );

            }
        );
}


attachSuggestionHandlers();


/* =========================================
   OBSERVABILITY PANEL
========================================= */

observabilityButton.addEventListener(
    "click",
    async () => {

        observabilityPanel
            .classList.add(
                "open"
            );

        await refreshStats();

        await refreshLogs();
    }
);


closeObservability.addEventListener(
    "click",
    () => {

        observabilityPanel
            .classList.remove(
                "open"
            );

    }
);


/* =========================================
   REFRESH LOGS
========================================= */

refreshLogsButton.addEventListener(
    "click",
    async () => {

        await refreshStats();

        await refreshLogs();

    }
);


async function refreshStats() {

    try {

        const response =
            await fetch(
                "/api/stats"
            );


        const stats =
            await response.json();


        document.getElementById(
            "totalRequests"
        ).textContent =
            stats.total_requests;


        document.getElementById(
            "successRate"
        ).textContent =
            stats.success_rate != null
                ? stats.success_rate
                    .toFixed(1) + "%"
                : "-";


        document.getElementById(
            "avgLatency"
        ).textContent =
            stats.average_latency_ms != null
                ? (
                    stats.average_latency_ms /
                    1000
                ).toFixed(2) + "s"
                : "-";


        document.getElementById(
            "avgTTFT"
        ).textContent =
            stats.average_ttft_ms != null
                ? stats.average_ttft_ms
                    .toFixed(0) + "ms"
                : "-";


        document.getElementById(
            "avgSpeed"
        ).textContent =
            stats.average_tokens_per_second != null
                ? stats.average_tokens_per_second
                    .toFixed(1) + " tok/s"
                : "-";

    } catch (error) {

        console.error(
            "Unable to load statistics:",
            error
        );

    }
}


/* =========================================
   LOAD LOGS
========================================= */

async function refreshLogs() {

    const container =
        document.getElementById(
            "logsContainer"
        );


    try {

        const response =
            await fetch(
                "/api/logs?limit=50"
            );


        const data =
            await response.json();


        container.innerHTML = "";


        if (
            !data.logs ||
            data.logs.length === 0
        ) {

            container.textContent =
                "No requests yet.";

            return;
        }


        [...data.logs]
            .reverse()
            .forEach(
                log => {

                    const card =
                        document.createElement(
                            "div"
                        );

                    card.className =
                        "log-card";


                    const latency =
                        log.total_latency_ms != null
                            ? (
                                log.total_latency_ms /
                                1000
                            ).toFixed(2) +
                              "s"
                            : "-";


                    const speed =
                        log.tokens_per_second != null
                            ? log.tokens_per_second
                                .toFixed(1) +
                              " tok/s"
                            : "-";


                    const ttft =
                        log.time_to_first_token_ms != null
                            ? log.time_to_first_token_ms
                                .toFixed(0) +
                              "ms"
                            : "-";


                    card.innerHTML = `
                        <div class="log-model">
                            ${escapeHtml(
                                log.model || "-"
                            )}
                        </div>

                        <div class="log-row">
                            <span>
                                Latency
                            </span>

                            <span>
                                ${latency}
                            </span>
                        </div>

                        <div class="log-row">
                            <span>
                                TTFT
                            </span>

                            <span>
                                ${ttft}
                            </span>
                        </div>

                        <div class="log-row">
                            <span>
                                Speed
                            </span>

                            <span>
                                ${speed}
                            </span>
                        </div>

                        <div class="log-row">
                            <span>
                                Tokens
                            </span>

                            <span>
                                ${
                                    log.output_tokens
                                    ?? "-"
                                }
                            </span>
                        </div>

                        <div class="log-row">
                            <span>
                                Status
                            </span>

                            <span>
                                ${escapeHtml(
                                    log.status || "-"
                                )}
                            </span>
                        </div>
                    `;


                    container.appendChild(
                        card
                    );

                }
            );

    } catch (error) {

        container.textContent =
            "Unable to load logs.";

    }
}

/*=========================================
   LOAD PROMPTS
========================================= */

async function loadPrompts() {

    try {

        const response =
            await fetch(
                "/api/prompts"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load prompts"
            );

        }


        const data =
            await response.json();


        promptSelect.innerHTML = "";


        data.templates.forEach(
            template => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    template.id;


                option.textContent =
                    template.name;


                promptSelect.appendChild(
                    option
                );

            }
        );

    } catch (error) {

        promptSelect.innerHTML = `
            <option value="general">
                General Assistant
            </option>
        `;

        console.error(
            "Prompt loading failed:",
            error
        );
    }
}


/* =========================================
   TEXTAREA AUTO RESIZE
========================================= */

input.addEventListener(
    "input",
    () => {

        input.style.height =
            "auto";

        input.style.height =
            Math.min(
                input.scrollHeight,
                180
            ) + "px";

    }
);


/* =========================================
   ENTER TO SEND
========================================= */

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


/* =========================================
   SCROLL
========================================= */

function scrollToBottom() {

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


/* =========================================
   HTML ESCAPE
========================================= */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================
   START
========================================= */

async function initialize() {

    await loadModels();

    await loadPrompts();

    await checkHealth();

    input.focus();

}


initialize();