// -----------------------------------------------------
// GLOBAL AUTH STATE & SESSION CHECK
// -----------------------------------------------------
let isLoginMode = true;
const BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://hirematch-ai-backend.onrender.com";
// Basic Session Guard
if (window.location.pathname.includes("dashboard.html")) {
    if (localStorage.getItem("isLoggedIn") !== "true") {
        window.location.href = "index.html";
    }
}
window.toggleAuthMode = function() {
    const mainTitle = document.querySelector('.main-title');
    const submitBtn = document.getElementById('submitBtn');
    const toggleBtn = document.getElementById('toggleBtn');
    const toggleText = document.getElementById('toggleText');
    if (!mainTitle || !submitBtn || !toggleBtn || !toggleText) return;
    isLoginMode = !isLoginMode;
    if (isLoginMode) {
        mainTitle.innerText = "AI Resume Analyzer";
        submitBtn.innerText = "Log In";
        toggleBtn.innerText = "Create account";
        toggleText.innerHTML = `<span class="dot">••</span> Don't have an account? <span class="dot">••</span>`;
    } else {
        mainTitle.innerText = "Create Account";
        submitBtn.innerText = "Sign Up";
        toggleBtn.innerText = "Back to Log In";
        toggleText.innerHTML = `<span class="dot">••</span> Already have an account? <span class="dot">••</span>`;
    }
};
window.submitAuthForm = async function() {
    const submitBtn = document.getElementById('submitBtn');
    const username = document.getElementById('username').value;
    const passwordInput = document.getElementById('password');
    if (!submitBtn || !passwordInput) return;
    const originalText = submitBtn.innerText;
    submitBtn.innerText = "Connecting...";
    submitBtn.disabled = true;
    // Define dynamic endpoint
    const endpoint = isLoginMode 
        ? `${BASE_URL}/login`
        : `${BASE_URL}/signup`;
    
    const payload = isLoginMode 
        ? { username: username, password: passwordInput.value }
        : { username: username, email: `${username}@mail.com`, password: passwordInput.value };
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.status === "success") {
            // Save Session State
            localStorage.setItem("isLoggedIn", "true");
            localStorage.setItem("username", username);
            window.location.href = "dashboard.html";
        } else {
            alert(data.message || "Authentication failed!");
            submitBtn.innerText = originalText;
            submitBtn.disabled = false;
        }
    } catch (error) {
        console.error("API Error:", error);
        alert("Server connection failed. Backend may be waking up. Please retry.");
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
    }
};
document.addEventListener("DOMContentLoaded", () => {
    // Utility function to format AI report (Markdown to HTML)
    function formatReport(text) {
        if (!text) return "";
        return text
            .replace(/^###\s*(.*)$/gm, "<h3>$1</h3>")
            .replace(/^####\s*(.*)$/gm, "<h4>$1</h4>")
            .replace(/^##\s*(.*)$/gm, "<h3>$1</h3>")
            .replace(/^#\s*(.*)$/gm, "<h2>$1</h2>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");
    }
    // -----------------------------------------------------
    // SESSION UI & LOGOUT LOGIC
    // -----------------------------------------------------
    const usernameDisplay = document.querySelector('.user-profile .username');
    const signOutBtn = document.querySelector('.sign-out');
    const storedUsername = localStorage.getItem("username");
    if (usernameDisplay && storedUsername) {
        usernameDisplay.textContent = storedUsername + "!";
    }
    if (signOutBtn) {
        signOutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem("isLoggedIn");
            localStorage.removeItem("username");
            window.location.href = "index.html";
        });
    }
    // -----------------------------------------------------
    // DASHBOARD & LOGIN GLOW LOGIC
    // -----------------------------------------------------
    const dashboardCard = document.getElementById('mainCard') || document.querySelector('.dashboard-grid');
    const loginCard = document.querySelector('.login-card');
    let glowOverlay = document.getElementById('dashboardOverlay') || document.querySelector('.card-glow-overlay');
    if (dashboardCard && glowOverlay) {
        dashboardCard.addEventListener('mousemove', (e) => {
            const rect = dashboardCard.getBoundingClientRect();
            glowOverlay.style.setProperty('--x', `${e.clientX - rect.left}px`);
            glowOverlay.style.setProperty('--y', `${e.clientY - rect.top}px`);
        });
    }
    if (loginCard && glowOverlay) {
        loginCard.addEventListener('mousemove', (e) => {
            const rect = loginCard.getBoundingClientRect();
            glowOverlay.style.setProperty('--x', `${e.clientX - rect.left}px`);
            glowOverlay.style.setProperty('--y', `${e.clientY - rect.top}px`);
        });
    }
    // -----------------------------------------------------
    // PASSWORD TOGGLE
    // -----------------------------------------------------
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            if (type === 'text') {
                togglePassword.querySelector('svg').style.stroke = "#2BE25F";
            } else {
                togglePassword.querySelector('svg').style.stroke = "#666";
            }
        });
    }
    // -----------------------------------------------------
    // DASHBOARD APPLICATION LOGIC
    // -----------------------------------------------------
    const fileInput = document.getElementById('fileInput');
    const dropText = document.querySelector('.drop-text');
    // Selected Filename View Logic 
    const fileNameDisplay = document.getElementById("selectedFileName");
    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener("change", function(e) {
            if (e.target.files.length > 0) {
                fileNameDisplay.textContent = "Selected: " + e.target.files[0].name;
            } else {
                fileNameDisplay.textContent = "";
            }
        });
    }
    const analyzeBtn = document.querySelector('.analyze-btn');
    const jobDescInput = document.querySelector('.textarea-wrapper textarea');
    const analysisContent = document.querySelector('.analysis-content p');
    // Execute REST API Analysis Hook
    if (analyzeBtn && fileInput && jobDescInput && analysisContent) {
        analyzeBtn.addEventListener('click', async () => {
            if (fileInput.files.length === 0) {
                alert("Please attach a resume document first!");
                return;
            }
            if (!jobDescInput.value.trim()) {
                alert("Please paste a target Job Description to compare against!");
                return;
            }
            const atsNode = document.getElementById("atsScore");
            const aiNode = document.getElementById("aiScore");
            const originalBtnText = analyzeBtn.innerText;
            analyzeBtn.innerText = "Connecting to AI Engine (first run may take 15–20s)...";
            analyzeBtn.disabled = true;
            
            if (atsNode) atsNode.innerHTML = `...<span class="percent">%</span>`;
            if (aiNode) aiNode.innerHTML = `...<span class="percent">/5</span>`;
            analysisContent.innerText = "Analyzing resume... AI engine is processing. This may take 5–15 seconds.";
            const formData = new FormData();
            formData.append("resume", fileInput.files[0]);
            formData.append("job_desc", jobDescInput.value.trim());

            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                alert("Backend is waking up. Please wait 10 seconds and click Analyze again.");
                controller.abort();
            }, 10000);

            try {
                const response = await fetch(`${BASE_URL}/analyze`, {
                    method: "POST",
                    body: formData,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error("Backend not reachable");
                }
                const json = await response.json();
                if (json.status === "success") {
                    const data = json.data;
                    
                    if (atsNode) atsNode.innerHTML = `${(data.ats_score * 100).toFixed(1)}<span class="percent">%</span>`;
                    if (aiNode) aiNode.innerHTML = `${(data.ai_score * 5).toFixed(1)}<span class="percent">/5</span>`;
                    
                    const reportText = data.ai_score === 0.0 && !data.report ? 
                        "AI Evaluation failed to parse response." : (data.report || data.ai_analysis || "");
                    
                    analysisContent.innerHTML = formatReport(reportText);
                    // Expose download functionality mapping report to Blob object securely
                    const downloadBtn = document.getElementById('downloadBtn');
                    if (downloadBtn) {
                        downloadBtn.onclick = () => {
                            const formattedReport = formatReport(data.report || data.ai_analysis);
                            const cleanText = formattedReport
                                .replace(/<br>/g, "\n")
                                .replace(/<[^>]*>/g, "");
                            const blob = new Blob([cleanText], { type: "text/plain" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = "ai_resume_report.txt";
                            a.click();
                            URL.revokeObjectURL(url);
                        };
                    }
                } else {
                    alert(json.detail || "Analysis failed. Verify Groq API Key.");
                    if (atsNode) atsNode.innerHTML = `0<span class="percent">%</span>`;
                    if (aiNode) aiNode.innerHTML = `0<span class="percent">/5</span>`;
                    analysisContent.innerText = "AI-generated detailed analysis of the resume will be shown here.";
                }
            } catch (error) {
                clearTimeout(timeoutId);
                console.error("Analysis Error:", error);
                if (error.name !== "AbortError") {
                    alert("Backend is waking up. Please wait 10 seconds and click Analyze again.");
                }
                if (atsNode) atsNode.innerHTML = `0<span class="percent">%</span>`;
                if (aiNode) aiNode.innerHTML = `0<span class="percent">/5</span>`;
                analysisContent.innerText = "AI-generated detailed analysis of the resume will be shown here.";
            } finally {
                analyzeBtn.innerText = originalBtnText;
                analyzeBtn.disabled = false;
            }
        });
    }
});
