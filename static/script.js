// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const newChatBtn = document.getElementById("new-chat-btn");
    const recommendedContainer = document.getElementById("recommended-questions-container");

    // Variabel untuk menyimpan riwayat obrolan sesi ini
    let chatHistory = [];

    // Fungsi untuk memuat riwayat dari sessionStorage saat halaman dimuat
    function loadChatHistory() {
        const savedHistory = sessionStorage.getItem("chatHistory");
        if (savedHistory) {
            chatHistory = JSON.parse(savedHistory);
            chatBox.innerHTML = ''; // Kosongkan chat box sebelum memuat
            chatHistory.forEach(message => {
                // Jangan tampilkan pesan 'loading' dari sesi sebelumnya
                if (message.content !== 'loading') {
                    appendMessage(message.content, message.role, false);
                }
            });
        } else {
             // Jika tidak ada riwayat, tampilkan pesan selamat datang
            chatBox.innerHTML = `
            <div class="message-wrapper bot">
                <div class="message bot">
                    Halo! Saya Damay, asisten AI dari SMKN 2 Indramayu. Ada yang bisa saya bantu?
                </div>
            </div>`;
        }
    }

    // Fungsi untuk menyimpan riwayat ke sessionStorage
    function saveChatHistory() {
        // Filter pesan 'loading' sebelum menyimpan
        const historyToSave = chatHistory.filter(msg => msg.content !== 'loading');
        sessionStorage.setItem("chatHistory", JSON.stringify(historyToSave));
    }

    // Panggil fungsi muat riwayat saat halaman pertama kali dibuka
    loadChatHistory();

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        sendMessage(userMessage);
    });

    newChatBtn.addEventListener("click", () => {
        chatHistory = []; // Hapus riwayat di memori
        sessionStorage.removeItem("chatHistory"); // Hapus dari sessionStorage
        loadChatHistory(); // Muat ulang tampilan awal
        recommendedContainer.innerHTML = "";
    });

    async function sendMessage(message) {
        // Tambahkan pesan pengguna ke riwayat
        chatHistory.push({ role: "user", content: message });
        appendMessage(message, "user");
        userInput.value = "";
        recommendedContainer.innerHTML = "";

        const loadingIndicator = showLoadingIndicator();
        chatHistory.push({ role: "bot", content: "loading" });

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // Kirim riwayat (tanpa pesan terakhir dari bot) ke backend
                body: JSON.stringify({
                    message: message,
                    history: chatHistory.slice(0, -1)
                }),
            });

            loadingIndicator.remove();
            chatHistory.pop(); // Hapus pesan 'loading' dari riwayat

            if (!response.ok) throw new Error("Respons jaringan tidak baik.");

            const data = await response.json();
            const botReply = data.reply || "Maaf, terjadi kesalahan.";
            
            chatHistory.push({ role: "bot", content: botReply });
            appendMessage(botReply, "bot");
            
            if (data.recommended_questions && data.recommended_questions.length > 0) {
                displayRecommendedQuestions(data.recommended_questions);
            }

        } catch (error) {
            console.error("Error:", error);
            if (chatBox.contains(loadingIndicator)) loadingIndicator.remove();
            chatHistory.pop(); // Hapus pesan 'loading' jika terjadi error
            
            const errorMessage = "Maaf, sepertinya ada masalah dengan koneksi. Silakan coba lagi.";
            appendMessage(errorMessage, "bot");
            chatHistory.push({ role: "bot", content: errorMessage });
        } finally {
            saveChatHistory(); // Simpan riwayat setelah setiap interaksi
        }
    }
    
    // Parameter 'save' ditambahkan untuk mencegah penyimpanan ganda saat memuat riwayat
    function appendMessage(message, sender, animate = true) {
        // Hapus tombol reroll yang ada jika ada pesan bot baru
        if (sender === 'bot') {
            document.querySelectorAll('.reroll-btn').forEach(btn => btn.remove());
        }

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
        rerollBtn.title = "Coba jawaban lain";
        rerollBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M15.312 11.424a5.5 5.5 0 01-9.201-4.46 3.5 3.5 0 115.743-4.432l.068.068a.75.75 0 01-1.06 1.06l-.067-.068a2 2 0 10-3.274 2.535 4 4 0 106.69 3.327.75.75 0 011.026-1.093z" clip-rule="evenodd" />
            </svg>`;
        rerollBtn.addEventListener("click", handleReroll);
        return rerollBtn;
    }

    function handleReroll() {
        // Hapus pesan terakhir dari bot di UI dan riwayat
        const lastBotMessageWrapper = chatBox.querySelector(".message-wrapper.bot:last-child");
        if (lastBotMessageWrapper) {
            lastBotMessageWrapper.remove();
        }
        
        // Hapus pesan pengguna terakhir dan pesan bot terakhir dari riwayat
        let lastUserMessage = null;
        if (chatHistory.length > 0) {
            // Hapus pesan bot
            chatHistory.pop(); 
            // Ambil pesan user terakhir
            const lastUserEntry = chatHistory[chatHistory.length - 1];
            if (lastUserEntry && lastUserEntry.role === 'user') {
                 lastUserMessage = lastUserEntry.content;
                 // Hapus pesan user agar tidak terduplikasi saat sendMessage dipanggil
                 chatHistory.pop();
            }
        }
        
        if (lastUserMessage) {
            sendMessage(lastUserMessage);
        }
    }

    function displayRecommendedQuestions(questions) {
        recommendedContainer.innerHTML = ''; // Pastikan kontainer bersih
        questions.forEach(question => {
            const button = document.createElement("button");
            button.classList.add("recommended-question");
            button.textContent = question.endsWith('?') ? question : question + '?';
            button.addEventListener("click", () => {
                sendMessage(button.textContent);
            });
            recommendedContainer.appendChild(button);
        });
    }

    function showLoadingIndicator() {
        const loadingWrapper = document.createElement("div");
        loadingWrapper.classList.add("message-wrapper", "bot", "loading-wrapper");
        const loadingElement = document.createElement("div");
        loadingElement.classList.add("message", "bot", "loading");
        loadingElement.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        loadingWrapper.appendChild(loadingElement)
        chatBox.appendChild(loadingWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
        return loadingWrapper;
    }
});