document.addEventListener('DOMContentLoaded', function() {
    const uploadSection = document.getElementById('uploadSection');
    const applyRadios = document.getElementsByName('applyDirectly');

    // Handle radio button changes
    applyRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            uploadSection.style.display = this.value === 'Yes' ? 'block' : 'none';
        });
    });

    // Handle form submission
    const uploadForm = document.querySelector('form');
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Failed to upload file');
            }
            
            if (result.success) {
                showAnalysisResults(result.data);
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'An error occurred while uploading the resume');
        }
    });
});

function showAnalysisResults(data) {
    const resultsSection = document.createElement('div');
    resultsSection.className = 'mt-4';
    resultsSection.innerHTML = `
        <h2>Resume Analysis Results</h2>
        <div class="card">
            <div class="card-body">
                <h3>Skills</h3>
                <div class="mb-3">
                    ${data.skills ? data.skills.map(skill => `<span class="badge bg-secondary me-2 mb-2">${skill}</span>`).join('') : ''}
                </div>
                
                <h3>Projects</h3>
                ${data.projects ? data.projects.map(project => `
                    <div class="mb-3">
                        <strong>${project.title || ''}</strong><br>
                        ${project.technologies ? `<span class="text-muted">Technologies: ${project.technologies}</span><br>` : ''}
                        ${project.duration ? `<span class="text-muted">Duration: ${project.duration}</span><br>` : ''}
                        ${project.description ? project.description.map(desc => `<p class="mb-1">• ${desc}</p>`).join('') : ''}
                    </div>
                `).join('') : ''}
                
                <h3>Experience</h3>
                ${data.experience ? data.experience.map(exp => `
                    <div class="mb-3">
                        <strong>${exp.title || ''}</strong>
                        ${exp.duration ? `<br><span class="text-muted">Duration: ${exp.duration}</span>` : ''}
                        ${exp.description ? exp.description.map(desc => `<p class="mb-1">• ${desc}</p>`).join('') : ''}
                    </div>
                `).join('') : ''}
                
                <div class="text-center mt-4">
                    <button class="btn btn-success me-3" onclick="saveResumeData()">
                        <i class="fas fa-save me-2"></i>Save Info
                    </button>
                    <button class="btn btn-primary btn-lg" onclick="findJobs()">
                        <i class="fas fa-search me-2"></i>Find Relevant Jobs
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing results
    const existingResults = document.querySelector('.container > div:last-child');
    if (existingResults && existingResults.querySelector('h2')?.textContent === 'Resume Analysis Results') {
        existingResults.remove();
    }
    
    document.querySelector('.container').appendChild(resultsSection);
}

async function findJobs() {
    try {
        const loadingButton = document.querySelector('button.btn-primary');
        if (loadingButton) {
            loadingButton.disabled = true;
            loadingButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Finding Jobs...';
        }

        const response = await fetch('/suggest_jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to fetch job suggestions');
        }
        
        if (result.success) {
            showJobResults(result.jobs);
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'An error occurred while finding jobs');
    } finally {
        const loadingButton = document.querySelector('button.btn-primary');
        if (loadingButton) {
            loadingButton.disabled = false;
            loadingButton.innerHTML = '<i class="fas fa-search me-2"></i>Find Relevant Jobs';
        }
    }
}

// Add this when showing job results
function showJobResults(jobs) {
    const jobsSection = document.createElement('div');
    jobsSection.className = 'mt-4';
    jobsSection.innerHTML = `
        <h2>Recommended Easy Apply Jobs</h2>
        <div class="list-group">
            ${jobs.map(job => `
                <a href="${job.url}" target="_blank" 
                   class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-1">${job.title}</h5>
                        <small class="text-muted">LinkedIn Easy Apply</small>
                    </div>
                    <span class="badge bg-success rounded-pill">Easy Apply</span>
                </a>
            `).join('')}
        </div>
    `;
    
    // Store job URLs in a hidden input
    const jobUrlsInput = document.createElement('input');
    jobUrlsInput.type = 'hidden';
    jobUrlsInput.id = 'jobUrls';
    jobUrlsInput.value = JSON.stringify(jobs.map(job => job.url));
    jobsSection.appendChild(jobUrlsInput);
    
    // Store resume data in a hidden input if it exists in session storage
    const resumeData = sessionStorage.getItem('resumeData');
    if (resumeData) {
        const resumeDataInput = document.createElement('input');
        resumeDataInput.type = 'hidden';
        resumeDataInput.id = 'resumeData';
        resumeDataInput.value = resumeData;
        jobsSection.appendChild(resumeDataInput);
    }
    
    // Show LinkedIn login section
    const loginSection = document.getElementById('linkedinLoginSection');
    if (loginSection) {
        loginSection.style.display = 'block';
    }
    
    // Remove existing job results if any
    const existingJobsSection = document.querySelector('#jobResults');
    if (existingJobsSection) {
        existingJobsSection.innerHTML = '';
    }
    
    document.querySelector('#jobResults').appendChild(jobsSection);
}

// Update showAnalysisResults to store resume data
function showAnalysisResults(data) {
    // Store resume data in session storage
    sessionStorage.setItem('resumeData', JSON.stringify(data));
    
    const resultsSection = document.createElement('div');
    resultsSection.className = 'mt-4';
    resultsSection.innerHTML = `
        <h2>Resume Analysis Results</h2>
        <div class="card">
            <div class="card-body">
                <h3>Skills</h3>
                <div class="mb-3">
                    ${data.skills ? data.skills.map(skill => `<span class="badge bg-secondary me-2 mb-2">${skill}</span>`).join('') : ''}
                </div>
                
                <h3>Projects</h3>
                ${data.projects ? data.projects.map(project => `
                    <div class="mb-3">
                        <strong>${project.title || ''}</strong><br>
                        ${project.technologies ? `<span class="text-muted">Technologies: ${project.technologies}</span><br>` : ''}
                        ${project.duration ? `<span class="text-muted">Duration: ${project.duration}</span><br>` : ''}
                        ${project.description ? project.description.map(desc => `<p class="mb-1">• ${desc}</p>`).join('') : ''}
                    </div>
                `).join('') : ''}
                
                <h3>Experience</h3>
                ${data.experience ? data.experience.map(exp => `
                    <div class="mb-3">
                        <strong>${exp.title || ''}</strong>
                        ${exp.duration ? `<br><span class="text-muted">Duration: ${exp.duration}</span>` : ''}
                        ${exp.description ? exp.description.map(desc => `<p class="mb-1">• ${desc}</p>`).join('') : ''}
                    </div>
                `).join('') : ''}
                
                <div class="text-center mt-4">
                    <button class="btn btn-success me-3" onclick="saveResumeData()">
                        <i class="fas fa-save me-2"></i>Save Info
                    </button>
                    <button class="btn btn-primary btn-lg" onclick="findJobs()">
                        <i class="fas fa-search me-2"></i>Find Relevant Jobs
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing results
    const existingResults = document.querySelector('.container > div:last-child');
    if (existingResults && existingResults.querySelector('h2')?.textContent === 'Resume Analysis Results') {
        existingResults.remove();
    }
    
    document.querySelector('.container').appendChild(resultsSection);
}

// Remove the extra closing brace and incorrect example function
function example() {
    console.log('Hello world');
}

document.getElementById('linkedinLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('linkedinEmail').value;
    const password = document.getElementById('linkedinPassword').value;
    const jobUrls = JSON.parse(document.getElementById('jobUrls').value);
    const resumeData = JSON.parse(document.getElementById('resumeData').value);

    try {
        const response = await fetch('/start_automation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password,
                jobUrls: jobUrls,
                resumeData: resumeData
            })
        });
        
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Failed to start automation');
        }
        
        // Show detailed results
        const resultsSection = document.createElement('div');
        resultsSection.className = 'mt-4';
        resultsSection.innerHTML = `
            <h3>Automation Results</h3>
            <div class="list-group">
                ${result.results.map(job => `
                    <div class="list-group-item ${job.success ? 'list-group-item-success' : 'list-group-item-danger'}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="mb-1">${job.url}</h5>
                                ${job.error ? `<small class="text-muted">Error: ${job.error}</small>` : ''}
                            </div>
                            <span class="badge ${job.success ? 'bg-success' : 'bg-danger'} rounded-pill">
                                ${job.success ? 'Success' : 'Failed'}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        document.querySelector('.container').appendChild(resultsSection);
        
    } catch (error) {
        console.error('Error:', error);
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger mt-3';
        errorMessage.textContent = error.message || 'An error occurred while starting the automation';
        document.querySelector('.container').appendChild(errorMessage);
    }
});

// Add this to your existing JavaScript code
function displayPersonalInfo(data) {
    // Get references to the elements
    const personalInfoSection = document.getElementById('personalInfo');
    const personName = document.getElementById('personName');
    const personPhone = document.getElementById('personPhone');
    const personCountry = document.getElementById('personCountry');
    const personEmail = document.getElementById('personEmail');

    // Check if we have data
    if (!data) {
        console.error('No personal information data provided');
        return;
    }

    // Update the elements with data
    if (personName) personName.textContent = data.name || 'N/A';
    if (personPhone) personPhone.textContent = data.phone || 'N/A';
    if (personCountry) personCountry.textContent = data.country || 'N/A';
    if (personEmail) personEmail.textContent = data.email || 'N/A';

    // Show the personal info section
    if (personalInfoSection) {
        personalInfoSection.style.display = 'block';
    }
}

// Modify your existing form submission handler to include this
// Replace the problematic form submission handler with this corrected version
document.querySelector('form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target); // Use e.target instead of this
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Failed to upload file');
        }
        
        if (result.success) {
            showAnalysisResults(result.data);
            displayPersonalInfo(result.data.personal_information); // Fix: access personal_information from result.data
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'An error occurred while uploading the resume');
    }
});


async function saveResumeData() {
    try {
        const saveButton = document.querySelector('button.btn-success');
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
        }

        const response = await fetch('/save_resume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to save resume data');
        }
        
        if (result.success) {
            alert('Resume data saved successfully!');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'An error occurred while saving resume data');
    } finally {
        const saveButton = document.querySelector('button.btn-success');
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = '<i class="fas fa-save me-2"></i>Save Info';
        }
    }
}