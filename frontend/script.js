const API_URL = "http://127.0.0.1:8000";

let allApplications = [];
let statusChart = null;
let companyChart = null;


// ===============================
// LOAD APPLICATIONS
// ===============================

async function loadApplications() {

    try {

        const response = await fetch(
            `${API_URL}/applications`
        );

        if (!response.ok) {
            throw new Error(
                `Server error: ${response.status}`
            );
        }

        const data = await response.json();

        allApplications = Array.isArray(data)
            ? data
            : (data.applications || []);

        console.log(
            "Applications loaded:",
            allApplications
        );

        updateDashboard(allApplications);

        updateCharts(allApplications);

        populateLocationFilter(allApplications);

        applyFilters();

    } catch (error) {

        console.error(
            "Application loading error:",
            error
        );

        const table =
            document.getElementById(
                "applicationsTable"
            );

        if (table) {

            table.innerHTML = `
                <tr>
                    <td colspan="7">
                        Unable to load applications.
                    </td>
                </tr>
            `;
        }
    }
}


// ===============================
// DASHBOARD
// ===============================

function updateDashboard(applications) {

    const total =
        applications.length;

    const applied =
        applications.filter(
            a => a.status === "Applied"
        ).length;

    const underReview =
        applications.filter(
            a => a.status === "Under Review"
        ).length;

    const assessment =
        applications.filter(
            a => a.status === "Assessment"
        ).length;

    const interview =
        applications.filter(
            a => a.status === "Interview"
        ).length;

    const selected =
        applications.filter(
            a =>
                a.status === "Selected" ||
                a.status === "Offer"
        ).length;

    const rejected =
        applications.filter(
            a => a.status === "Rejected"
        ).length;


    setText("totalCount", total);
    setText("appliedCount", applied);
    setText("underReviewCount", underReview);
    setText("assessmentCount", assessment);
    setText("interviewCount", interview);
    setText("selectedCount", selected);
    setText("rejectedCount", rejected);
}


function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


// ===============================
// TABLE
// ===============================

function renderApplications(applications) {

    const table =
        document.getElementById(
            "applicationsTable"
        );

    if (!table) return;


    if (!applications.length) {

        table.innerHTML = `
            <tr>
                <td colspan="7">
                    No applications found.
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML =
        applications.map(application => {

            const applicationData =
                encodeURIComponent(
                    JSON.stringify(application)
                );

            return `
                <tr>

                    <td>
                        ${escapeHtml(
                            application.company || "Unknown"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            application.job_role || "Unknown"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            application.job_id || "-"
                        )}
                    </td>

                    <td>
                        <span class="status-badge">
                            ${escapeHtml(
                                application.status || "Unknown"
                            )}
                        </span>
                    </td>

                    <td>
                        ${escapeHtml(
                            application.location || "-"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            application.application_date || "-"
                        )}
                    </td>

                    <td>

                        <button
                            class="row-btn edit-btn"
                            onclick="editApplicationFromButton('${applicationData}')"
                        >
                            Edit
                        </button>

                        <button
                            class="row-btn delete-btn"
                            onclick="deleteApplication(${application.id})"
                        >
                            Delete
                        </button>

                    </td>

                </tr>
            `;

        }).join("");
}


// ===============================
// SEARCH + FILTER
// ===============================

function applyFilters() {

    const searchInput =
        document.getElementById("searchInput");

    const statusFilter =
        document.getElementById("statusFilter");

    const locationFilter =
        document.getElementById("locationFilter");


    const search =
        searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";

    const selectedStatus =
        statusFilter
            ? statusFilter.value
            : "All";

    const selectedLocation =
        locationFilter
            ? locationFilter.value
            : "All";


    const filtered =
        allApplications.filter(application => {

            const company =
                String(
                    application.company || ""
                ).toLowerCase();

            const role =
                String(
                    application.job_role || ""
                ).toLowerCase();

            const location =
                String(
                    application.location || ""
                );


            const matchesSearch =
                !search ||
                company.includes(search) ||
                role.includes(search);


            const matchesStatus =
                selectedStatus === "All" ||
                application.status === selectedStatus;


            const matchesLocation =
                selectedLocation === "All" ||
                location === selectedLocation;


            return (
                matchesSearch &&
                matchesStatus &&
                matchesLocation
            );

        });


    renderApplications(filtered);
}


// ===============================
// LOCATION FILTER
// ===============================

function populateLocationFilter(applications) {

    const filter =
        document.getElementById(
            "locationFilter"
        );

    if (!filter) return;


    const currentValue =
        filter.value;


    const locations = [
        ...new Set(
            applications
                .map(
                    application =>
                        application.location
                )
                .filter(Boolean)
        )
    ].sort();


    filter.innerHTML = `
        <option value="All">
            All Locations
        </option>
    `;


    locations.forEach(location => {

        const option =
            document.createElement("option");

        option.value = location;
        option.textContent = location;

        filter.appendChild(option);

    });


    if (
        locations.includes(currentValue)
    ) {
        filter.value = currentValue;
    }
}


// ===============================
// CLEAR FILTERS
// ===============================

function clearFilters() {

    const searchInput =
        document.getElementById("searchInput");

    const statusFilter =
        document.getElementById("statusFilter");

    const locationFilter =
        document.getElementById("locationFilter");


    if (searchInput) {
        searchInput.value = "";
    }

    if (statusFilter) {
        statusFilter.value = "All";
    }

    if (locationFilter) {
        locationFilter.value = "All";
    }


    applyFilters();
}


// ===============================
// CHARTS
// ===============================

function updateCharts(applications) {

    updateStatusChart(applications);

    updateCompanyChart(applications);
}


function updateStatusChart(applications) {

    const canvas =
        document.getElementById(
            "statusChart"
        );

    if (!canvas) return;


    const counts = {

        Applied: 0,

        "Under Review": 0,

        Assessment: 0,

        Interview: 0,

        Selected: 0,

        Rejected: 0

    };


    applications.forEach(application => {

        if (
            Object.prototype.hasOwnProperty.call(
                counts,
                application.status
            )
        ) {

            counts[
                application.status
            ]++;

        }

    });


    if (statusChart) {
        statusChart.destroy();
    }


    statusChart =
        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {

                    labels:
                        Object.keys(counts),

                    datasets: [

                        {
                            data:
                                Object.values(counts)
                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false

                }

            }
        );
}


function updateCompanyChart(applications) {

    const canvas =
        document.getElementById(
            "companyChart"
        );

    if (!canvas) return;


    const companyCounts = {};


    applications.forEach(application => {

        const company =
            application.company ||
            "Unknown";


        companyCounts[company] =
            (companyCounts[company] || 0) + 1;

    });


    if (companyChart) {
        companyChart.destroy();
    }


    companyChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels:
                        Object.keys(companyCounts),

                    datasets: [

                        {
                            label:
                                "Applications",

                            data:
                                Object.values(companyCounts)
                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                precision: 0

                            }

                        }

                    }

                }

            }
        );
}


// ===============================
// MANUAL DETECTION
// ===============================

async function detectApplication() {

    const emailText =
        document.getElementById(
            "emailText"
        );

    const loading =
        document.getElementById(
            "loading"
        );


    if (!emailText) return;


    const text =
        emailText.value.trim();


    if (!text) {

        if (loading) {
            loading.textContent =
                "Please paste an email first.";
        }

        return;
    }


    if (loading) {
        loading.textContent =
            "Analyzing email...";
    }


    try {

        const response =
            await fetch(
                `${API_URL}/detect`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email: text
                    })

                }
            );


        if (!response.ok) {

            throw new Error(
                `Server error: ${response.status}`
            );

        }


        const data =
            await response.json();


        displayDetectionResult(data);


        if (loading) {
            loading.textContent =
                "Analysis complete.";
        }


        await loadApplications();

    } catch (error) {

        console.error(
            "Detection error:",
            error
        );

        if (loading) {

            loading.textContent =
                "Unable to analyze the email.";

        }

    }
}


// ===============================
// DISPLAY DETECTION RESULT
// ===============================

function displayDetectionResult(data) {

    setText(
        "company",
        data.company || "-"
    );

    setText(
        "jobRole",
        data.job_role || "-"
    );

    setText(
        "jobId",
        data.job_id || "-"
    );

    setText(
        "status",
        data.status || "-"
    );

    setText(
        "location",
        data.location || "-"
    );

    setText(
        "applicationDate",
        data.application_date || "-"
    );
}


// ===============================
// GMAIL SYNC
// ===============================

async function syncGmail() {

    const button =
        document.getElementById(
            "syncGmailBtn"
        );

    const message =
        document.getElementById(
            "syncMessage"
        );


    if (button) {
        button.disabled = true;
        button.textContent =
            "🔄 Syncing...";
    }


    if (message) {
        message.textContent =
            "Syncing Gmail...";
    }


    try {

        const response =
            await fetch(
                `${API_URL}/sync-gmail`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                `Server error: ${response.status}`
            );

        }


        if (message) {

            message.textContent =
                `Sync completed. Saved: ${
                    data.saved || 0
                }, Duplicates: ${
                    data.duplicates || 0
                }, Status updates: ${
                    data.status_updates || 0
                }`;

        }


        await loadApplications();

    } catch (error) {

        console.error(
            "Gmail sync error:",
            error
        );

        if (message) {

            message.textContent =
                `Gmail sync failed: ${error.message}`;

        }

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "🔄 Sync Gmail";

        }

    }
}


// ===============================
// EDIT APPLICATION
// ===============================

function editApplicationFromButton(encodedData) {

    try {

        const application =
            JSON.parse(
                decodeURIComponent(
                    encodedData
                )
            );


        document.getElementById(
            "editId"
        ).value =
            application.id || "";


        document.getElementById(
            "editCompany"
        ).value =
            application.company || "";


        document.getElementById(
            "editJobRole"
        ).value =
            application.job_role || "";


        document.getElementById(
            "editJobId"
        ).value =
            application.job_id || "";


        document.getElementById(
            "editStatus"
        ).value =
            application.status || "Applied";


        document.getElementById(
            "editLocation"
        ).value =
            application.location || "";


        document.getElementById(
            "editDate"
        ).value =
            application.application_date || "";


        const modal =
            document.getElementById(
                "editModal"
            );


        if (modal) {
            modal.style.display = "block";
        }

    } catch (error) {

        console.error(
            "Edit modal error:",
            error
        );

    }
}


function closeEditModal() {

    const modal =
        document.getElementById(
            "editModal"
        );

    if (modal) {
        modal.style.display = "none";
    }
}


// ===============================
// SAVE EDITED APPLICATION
// ===============================

async function saveEditedApplication(event) {

    if (event) {
        event.preventDefault();
    }


    const id =
        document.getElementById(
            "editId"
        ).value;


    const application = {

        company:
            document.getElementById(
                "editCompany"
            ).value,

        job_role:
            document.getElementById(
                "editJobRole"
            ).value,

        job_id:
            document.getElementById(
                "editJobId"
            ).value,

        status:
            document.getElementById(
                "editStatus"
            ).value,

        location:
            document.getElementById(
                "editLocation"
            ).value,

        application_date:
            document.getElementById(
                "editDate"
            ).value

    };


    try {

        const response =
            await fetch(
                `${API_URL}/applications/${id}`,
                {

                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(application)

                }
            );


        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.detail ||
                `Server error: ${response.status}`
            );

        }


        closeEditModal();

        await loadApplications();

    } catch (error) {

        console.error(
            "Update error:",
            error
        );

        alert(
            `Unable to update application: ${error.message}`
        );

    }
}


// ===============================
// DELETE APPLICATION
// ===============================

async function deleteApplication(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this application?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/applications/${id}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.detail ||
                `Server error: ${response.status}`
            );

        }


        await loadApplications();

    } catch (error) {

        console.error(
            "Delete error:",
            error
        );

        alert(
            `Unable to delete application: ${error.message}`
        );

    }
}


// ===============================
// MODAL OUTSIDE CLICK
// ===============================

window.addEventListener(
    "click",
    function(event) {

        const modal =
            document.getElementById(
                "editModal"
            );

        if (
            modal &&
            event.target === modal
        ) {
            closeEditModal();
        }

    }
);


// ===============================
// INITIAL LOAD
// ===============================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadApplications();

    }
);


// ===============================
// HTML ESCAPE
// ===============================

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
document.getElementById("statusFilter").addEventListener("change", applyFilters);
document.getElementById("locationFilter").addEventListener("change", applyFilters);
document.getElementById("searchInput").addEventListener("input", applyFilters);