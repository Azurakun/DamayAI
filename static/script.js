// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const sendBtn = document.getElementById("send-btn");

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userMessage = userInput.value.trim();
        if (!userMessage) return;

        // Display user's message
        appendMessage(userMessage, "user");
        userInput.value = "";

        // Show loading indicator
        const loadingIndicator = showLoadingIndicator();

        try {
            // Send message to the backend
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: userMessage }),
            });

            // Remove loading indicator
            loadingIndicator.remove();

            if (!response.ok) {
                throw new Error("Network response was not ok.");
            }

            const data = await response.json();
            appendMessage(data.reply || "Maaf, terjadi kesalahan.", "bot");

        } catch (error) {
            console.error("Error:", error);
            // Ensure loading indicator is removed on error
            if (document.body.contains(loadingIndicator)) {
                loadingIndicator.remove();
            }
            appendMessage("Maaf, sepertinya ada masalah dengan koneksi. Silakan coba lagi.", "bot");
        }
    });

    function appendMessage(message, sender) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.textContent = message;
        chatBox.appendChild(messageElement);
        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
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