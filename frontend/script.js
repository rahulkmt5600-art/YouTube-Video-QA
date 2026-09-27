
const API_URL = "http://127.0.0.1:8000";


let videoProcessed = false;



// ELEMENTS


const youtubeUrl =
    document.getElementById("youtubeUrl");

const processBtn =
    document.getElementById("processBtn");

const question =
    document.getElementById("question");

const askBtn =
    document.getElementById("askBtn");

const status =
    document.getElementById("status");

const videoStatus =
    document.getElementById("videoStatus");

const videoPreview =
    document.getElementById("videoPreview");

const chatMessages =
    document.getElementById("chatMessages");

const clearBtn =
    document.getElementById("clearBtn");



// EXTRACT VIDEO ID


function extractVideoId(url) {

    const patterns = [

        /[?&]v=([^&#]+)/,

        /youtu\.be\/([^?#]+)/,

        /youtube\.com\/shorts\/([^?#]+)/,

        /youtube\.com\/embed\/([^?#]+)/

    ];


    for (const pattern of patterns) {

        const match = url.match(pattern);

        if (match) {

            return match[1].substring(0, 11);

        }

    }


    return null;
}



// SHOW VIDEO


function showVideo(url) {

    const videoId =
        extractVideoId(url);


    if (!videoId) {

        return;

    }


    videoPreview.innerHTML = `

        <iframe

            src="https://www.youtube.com/embed/${videoId}"

            title="YouTube video"

            allow="accelerometer; autoplay; clipboard-write;
            encrypted-media; gyroscope; picture-in-picture"

            allowfullscreen>

        </iframe>

    `;
}



// ADD USER MESSAGE


function addUserMessage(message) {

    const div =
        document.createElement("div");

    div.className =
        "user-message";


    div.innerHTML = `

        <div class="user-icon">
            You
        </div>

        <div class="message-content">
            ${escapeHtml(message)}
        </div>

    `;


    chatMessages.appendChild(div);

    scrollChat();
}



//  ADD AI MESSAGE


function addAIMessage(message) {

    const div =
        document.createElement("div");

    div.className =
        "ai-message";


    div.innerHTML = `

        <div class="bot-icon">
            AI
        </div>

        <div class="message-content">
            ${escapeHtml(message)}
        </div>

    `;


    chatMessages.appendChild(div);

    scrollChat();
}



//  LOADING MESSAGE


function addLoadingMessage() {

    const div =
        document.createElement("div");

    div.className =
        "ai-message";

    div.id =
        "loadingMessage";


    div.innerHTML = `

        <div class="bot-icon">
            AI
        </div>

        <div class="message-content">

            <div class="loading">

                <span></span>
                <span></span>
                <span></span>

            </div>

        </div>

    `;


    chatMessages.appendChild(div);

    scrollChat();
}



// REMOVE LOADING


function removeLoadingMessage() {

    const loading =
        document.getElementById(
            "loadingMessage"
        );


    if (loading) {

        loading.remove();

    }
}



// SCROLL CHAT


function scrollChat() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}



// ESCAPE HTML


function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;
}



// PROCESS VIDEO


processBtn.addEventListener(
    "click",
    async () => {

        const url =
            youtubeUrl.value.trim();


        if (!url) {

            status.textContent =
                "Please enter a YouTube URL.";

            return;

        }


        const videoId =
            extractVideoId(url);


        if (!videoId) {

            status.textContent =
                "Please enter a valid YouTube URL.";

            return;

        }


        processBtn.disabled =
            true;

        processBtn.textContent =
            "Processing...";


        status.textContent =
            "Fetching transcript and creating vector database...";


        videoStatus.textContent =
            "Processing";


        try {

            const response =
                await fetch(
                    `${API_URL}/process-video`,
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                youtube_url:
                                    url

                            })

                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Failed to process video."
                );

            }


            if (data.success) {

                videoProcessed =
                    true;


                showVideo(url);


                videoStatus.textContent =
                    "Ready";


                status.textContent =
                    `Video processed successfully. ${data.chunks} chunks created.`;


                question.disabled =
                    false;

                askBtn.disabled =
                    false;


                question.focus();

            }

        }

        catch (error) {

            console.error(error);


            videoProcessed =
                false;


            videoStatus.textContent =
                "Failed";


            status.textContent =
                error.message ||
                "Could not connect to backend.";

        }

        finally {

            processBtn.disabled =
                false;

            processBtn.textContent =
                "Process Video";

        }

    }
);



//  ASK QUESTION


async function askQuestion() {

    if (!videoProcessed) {

        addAIMessage(
            "Please process a YouTube video first."
        );

        return;

    }


    const userQuestion =
        question.value.trim();


    if (!userQuestion) {

        return;

    }


    addUserMessage(
        userQuestion
    );


    question.value =
        "";


    question.disabled =
        true;

    askBtn.disabled =
        true;


    addLoadingMessage();


    try {

        const response =
            await fetch(
                `${API_URL}/ask`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            question:
                                userQuestion

                        })

                }
            );


        const data =
            await response.json();


        removeLoadingMessage();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to get answer."
            );

        }


        if (data.success) {

            addAIMessage(
                data.answer
            );

        }

        else {

            addAIMessage(
                data.message ||
                "Unable to generate an answer."
            );

        }

    }

    catch (error) {

        console.error(error);


        removeLoadingMessage();


        addAIMessage(
            error.message ||
            "Could not connect to backend."
        );

    }

    finally {

        question.disabled =
            false;

        askBtn.disabled =
            false;

        question.focus();

    }

}



// ASK BUTTON


askBtn.addEventListener(
    "click",
    askQuestion
);



// ENTER KEY


question.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            askQuestion();

        }

    }
);



// CLEAR CHAT


clearBtn.addEventListener(
    "click",
    () => {

        chatMessages.innerHTML = `

            <div class="welcome-message">

                <div class="bot-icon">
                    AI
                </div>

                <div>

                    <strong>
                        YouTube RAG Assistant
                    </strong>

                    <p>
                        Chat cleared. Ask a new question
                        about your video.
                    </p>

                </div>

            </div>

        `;

    }
);