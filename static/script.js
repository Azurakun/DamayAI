// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const newChatBtn = document.getElementById("new-chat-btn");
    const recommendedContainer = document.getElementById("recommended-questions-container");

    let lastUserMessage = "";

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        sendMessage(userMessage);
    });

    newChatBtn.addEventListener("click", () => {
        chatBox.innerHTML = `
            <div class="message bot">
                Halo! Saya asisten AI SMKN 2 Indramayu. Ada yang bisa saya bantu?
            </div>`;
        lastUserMessage = "";
        recommendedContainer.innerHTML = "";
    });

    async function sendMessage(message) {
        lastUserMessage = message;
        appendMessage(message, "user");
        userInput.value = "";
        recommendedContainer.innerHTML = ""; // Clear old recommendations

        const loadingIndicator = showLoadingIndicator();

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message }),
            });

            loadingIndicator.remove();

            if (!response.ok) throw new Error("Network response was not ok.");

            const data = await response.json();
            appendMessage(data.reply || "Maaf, terjadi kesalahan.", "bot");

            if (data.recommended_questions && data.recommended_questions.length > 0) {
                displayRecommendedQuestions(data.recommended_questions);
            }

        } catch (error) {
            console.error("Error:", error);
            if (document.body.contains(loadingIndicator)) loadingIndicator.remove();
            appendMessage("Maaf, sepertinya ada masalah dengan koneksi. Silakan coba lagi.", "bot");
        }
    }

    function appendMessage(message, sender) {
        // Remove existing reroll buttons
        document.querySelectorAll('.reroll-btn').forEach(btn => btn.remove());

        const messageWrapper = document.createElement("div");
        messageWrapper.classList.add("message-wrapper", sender);

        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.textContent = message;

        messageWrapper.appendChild(messageElement);

        if (sender === "bot") {
            const rerollBtn = createRerollButton();
            messageWrapper.appendChild(rerollBtn);
        }

        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function createRerollButton() {
        const rerollBtn = document.createElement("button");
        rerollBtn.classList.add("reroll-btn");
        rerollBtn.title = "Reroll response";
        rerollBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M15.312 11.424a5.5 5.5 0 01-9.201-4.46 3.5 3.5 0 115.743-4.432l.068.068a.75.75 0 01-1.06 1.06l-.067-.068a2 2 0 10-3.274 2.535 4 4 0 106.69 3.327.75.75 0 011.026-1.093z" clip-rule="evenodd" />
            </svg>`;
        rerollBtn.addEventListener("click", handleReroll);
        return rerollBtn;
    }

    function handleReroll() {
        if (!lastUserMessage) return;

        // Remove the last bot message and its wrapper
        const lastBotMessage = chatBox.querySelector(".message-wrapper.bot:last-child");
        if (lastBotMessage) {
            lastBotMessage.remove();
        }

        sendMessage(lastUserMessage);
    }

    function displayRecommendedQuestions(questions) {
        questions.forEach(question => {
            const button = document.createElement("button");
            button.classList.add("recommended-question");
            button.textContent = question;
            button.addEventListener("click", () => {
                sendMessage(question);
            });
            recommendedContainer.appendChild(button);
        });
    }

    function showLoadingIndicator() {
        const loadingElement = document.createElement("div");
        loadingElement.classList.add("message", "bot", "loading");
        loadingElement.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        chatBox.appendChild(loadingElement);
        chatBox.scrollTop = chatBox.scrollHeight;
        return loadingElement;
    }
});