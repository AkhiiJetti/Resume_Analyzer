document.addEventListener('DOMContentLoaded', () => {
    // --- 1. SELECT HTML ELEMENTS ---
    const resumeForm = document.getElementById('resumeForm');
    const resumeInput = document.getElementById('resumeFile');
    const jobDescInput = document.getElementById('jobDesc');
    const resultDiv = document.getElementById('result');
    const submitButton = resumeForm.querySelector('button');

    // --- 2. LISTEN FOR FORM SUBMISSION ---
    resumeForm.addEventListener('submit', async (event) => {
        // Prevent the default browser action of reloading the page
        event.preventDefault();

        const resumeFile = resumeInput.files[0];
        const jobDescription = jobDescInput.value;

        // Simple validation to ensure fields are not empty
        if (!resumeFile || !jobDescription.trim()) {
            alert('Please upload a resume and paste a job description.');
            return;
        }

        // Use FormData to package the file and text for sending
        const formData = new FormData();
        formData.append('resume', resumeFile);
        formData.append('job_description', jobDescription);

        // --- 3. HANDLE LOADING STATE ---
        submitButton.disabled = true;
        submitButton.textContent = 'Analyzing...';
        // Clear previous results and show a loading message
        resultDiv.innerHTML = '<p class="loading">Analyzing your resume, please wait... 🤖</p>';
        resultDiv.style.background = '#f9f9f9'; // Restore default background during loading

        try {
            // --- 4. SEND DATA TO BACKEND API ---
            const response = await fetch('http://127.0.0.1:5000/analyze', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            // Handle errors returned from the server (e.g., PDF parsing failed)
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            // --- 5. DISPLAY THE RESULTS ---
            displayResults(data);

        } catch (error) {
            // Handle network errors or other issues with the fetch call
            console.error('Error:', error);
            resultDiv.innerHTML = `<div class="error-message"><strong>Error:</strong> ${error.message}</div>`;
        } finally {
            // --- 6. RESET THE BUTTON ---
            // This runs whether the request succeeded or failed
            submitButton.disabled = false;
            submitButton.textContent = 'Analyze Resume';
        }
    });

    /**
     * Takes the analysis data from the API and renders the formatted HTML result.
     * @param {object} data - The JSON data from the backend.
     */
    function displayResults(data) {
        // Clear the loading message
        resultDiv.innerHTML = '';

        // --- DYNAMICALLY CREATE THE HTML FOR THE RESULTS ---

        // Create a title for the results section
        const title = document.createElement('h2');
        title.textContent = 'Analysis Result';

        // Create the green match score bar
        const scoreBar = document.createElement('div');
        scoreBar.className = 'match-score-bar';
        scoreBar.textContent = `Match Score: ${data.matchScore}/100`;

        // Create the "Missing Skills" heading
        const missingSkillsHeader = document.createElement('h3');
        missingSkillsHeader.textContent = 'Missing Skills:';

        // Append the main elements to the result container
        resultDiv.appendChild(title);
        resultDiv.appendChild(scoreBar);

        // Only show the "Missing Skills" section if there are any
        if (data.missingSkills && data.missingSkills.length > 0) {
            resultDiv.appendChild(missingSkillsHeader);

            // Create a card for each missing skill
            data.missingSkills.forEach((skill, index) => {
                const skillCard = document.createElement('div');
                skillCard.className = 'skill-card';
                
                const cardParagraph = document.createElement('p');
                
                const skillTitle = document.createElement('strong');
                skillTitle.className = 'skill-title';
                skillTitle.textContent = skill.charAt(0).toUpperCase() + skill.slice(1).replace(/_/g, ' '); // Capitalize and format skill name

                // Use the suggestion from the API as the description
                const skillDescription = document.createTextNode(data.suggestions[index]);

                cardParagraph.appendChild(skillTitle);
                cardParagraph.appendChild(skillDescription);
                skillCard.appendChild(cardParagraph);
                resultDiv.appendChild(skillCard);
            });
        }
        
        // --- ADD THE AI FEEDBACK SECTION ---
        const aiFeedbackHeader = document.createElement('h3');
        aiFeedbackHeader.textContent = 'AI Feedback:';
        resultDiv.appendChild(aiFeedbackHeader);
        
        const aiFeedbackCard = document.createElement('div');
        aiFeedbackCard.className = 'skill-card'; // We can reuse the same card style
        
        // Format the AI feedback (which comes in a markdown-like style) into HTML
        const formattedFeedback = data.aiFeedback
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
            
        aiFeedbackCard.innerHTML = `<p>${formattedFeedback}</p>`;
        resultDiv.appendChild(aiFeedbackCard);


        // Finally, remove the default gray background from the #result container
        // to let the new white background and card colors show through.
        resultDiv.style.background = 'none';
        resultDiv.style.padding = '0';
    }
});