// Add this at the beginning of fetch.js
document.addEventListener('DOMContentLoaded', function() {
    // File input and upload button elements
    const fileInput = document.getElementById('fileUpload');
    const uploadButton = document.getElementById('uploadButton');
    const fileLabel = document.querySelector('.file-label');

    // Update label text when file is selected
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const fileType = file.name.split('.').pop().toLowerCase();
            if (fileType !== 'csv' && fileType !== 'txt') {
                alert('Please select a .csv or .txt file');
                this.value = ''; // Clear the file input
                fileLabel.textContent = 'Choose File';
                return;
            }
            fileLabel.textContent = file.name;
            console.log('File selected:', file.name); // Debug log
        } else {
            fileLabel.textContent = 'Choose File';
        }
    });

    // Handle file upload
    uploadButton.addEventListener('click', function() {
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        const fileType = file.name.split('.').pop().toLowerCase();
        if (fileType !== 'csv' && fileType !== 'txt') {
            alert('Please select a .csv or .txt file');
            return;
        }

        console.log('Preparing to upload file:', file.name); // Debug log

        const formData = new FormData();
        formData.append('file', file);

        // Show loading state
        uploadButton.disabled = true;
        uploadButton.textContent = 'Uploading...';

        fetch('http://localhost:5000/process-data', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Response status:', response.status); // Debug log
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data); // Debug log
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            createProcessFlow(data);
            displayAnalysis(data);
            
            // Reset upload button
            uploadButton.disabled = false;
            uploadButton.textContent = 'Upload';
            
            // Show success message
            alert('File processed successfully!');
        })
        .catch(error => {
            console.error('Error details:', error);
            
            // Reset upload button
            uploadButton.disabled = false;
            uploadButton.textContent = 'Upload';
            
            // Show detailed error message
            alert(`Error processing file: ${error.message || 'Unknown error'}`);
        });
    });
});

// Function to create process flow visualization
function createProcessFlow(data) {
    const width = 800;
    const height = 600;
    
    // Clear any existing SVG
    d3.select("#visualization").html("");
    
    const svg = d3.select("#visualization")
        .append("svg")
        .attr("width", width)
        .attr("height", height);
    
    // Create force simulation
    const simulation = d3.forceSimulation(data.statistics.user_journey_visualization.nodes)
        .force("link", d3.forceLink(data.statistics.user_journey_visualization.links)
            .id(d => d.id)
            .distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));
    
    // Create links
    const links = svg.append("g")
        .selectAll("line")
        .data(data.statistics.user_journey_visualization.links)
        .enter()
        .append("line")
        .attr("stroke-width", d => Math.sqrt(d.value))
        .attr("stroke", "#999");
    
    // Create nodes
    const nodes = svg.append("g")
        .selectAll("circle")
        .data(data.statistics.user_journey_visualization.nodes)
        .enter()
        .append("circle")
        .attr("r", d => Math.sqrt(d.count) * 3)
        .attr("fill", "#3474F3")
        .call(drag(simulation));
    
    // Add labels
    const labels = svg.append("g")
        .selectAll("text")
        .data(data.statistics.user_journey_visualization.nodes)
        .enter()
        .append("text")
        .text(d => d.id)
        .attr("font-size", "12px")
        .attr("dx", 15)
        .attr("dy", 4);
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
        links
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        nodes
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
        
        labels
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    });
}

// Drag functionality for nodes
function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}

// Fetch and visualize data
fetch("http://localhost:5000/process-data")
    .then(response => response.json())
    .then(data => {
        createProcessFlow(data);
        displayAnalysis(data);
    })
    .catch(error => {
        console.error("Error fetching or processing data:", error);
        logError(error);
    });

// Display analysis results
function displayAnalysis(data) {
    const analysisDiv = d3.select("#analysis")
        .html("")
        .append("div")
        .attr("class", "analysis-container");
    
    // Display bottlenecks
    analysisDiv.append("h3").text("Identified Bottlenecks");
    const bottlenecksList = analysisDiv.append("ul");
    data.bottlenecks.forEach(bottleneck => {
        bottlenecksList.append("li").text(bottleneck);
    });
    
    // Display process variants
    analysisDiv.append("h3").text("Process Variants");
    const variantsList = analysisDiv.append("ul");
    data.variants.forEach(variant => {
        variantsList.append("li").text(variant);
    });
    
    // Display statistics
    analysisDiv.append("h3").text("Process Statistics");
    const statsList = analysisDiv.append("ul");
    Object.entries(data.statistics.event_counts).forEach(([event, count]) => {
        statsList.append("li").text(`${event}: ${count} occurrences`);
    });
}

// Test cases for fetch.js
if (process.env.NODE_ENV === 'test') {
  describe('Data Fetching and Visualization Tests', () => {
    beforeEach(() => {
      localStorage.clear();
      // Clean up any SVG elements from previous tests
      d3.selectAll('svg').remove();
    });

    test('successful data fetch and visualization', async () => {
      const mockData = {
        steps: [1, 2, 3]
      };
      global.fetch = jest.fn(() =>
        Promise.resolve({
          json: () => Promise.resolve(mockData)
        })
      );

      // Execute fetch
      await fetchAndVisualize();
      
      // Verify SVG elements
      const circles = d3.selectAll('circle');
      expect(circles.size()).toBe(3);
    });

    test('error handling', async () => {
      global.fetch = jest.fn(() =>
        Promise.reject(new Error('Network error'))
      );

      await fetchAndVisualize();
      
      // Verify error logging
      const logs = JSON.parse(localStorage.getItem('fetchErrors'));
      expect(logs.length).toBe(1);
      expect(logs[0].error).toContain('Network error');
    });
  });
}

// Helper function for error logging
function logError(error) {
  const errorLog = {
    timestamp: new Date().toISOString(),
    error: error.toString(),
    endpoint: "http://localhost:5000/process-data"
  };
  
  const existingLogs = JSON.parse(localStorage.getItem('fetchErrors') || '[]');
  existingLogs.push(errorLog);
  localStorage.setItem('fetchErrors', JSON.stringify(existingLogs));
  
  // Display error message to user
  d3.select("body")
    .append("div")
    .attr("class", "error-message")
    .text("Error loading visualization. Check console for details.");
}

// Create a new file: changelog.md
const fs = require('fs');

function updateChangelog() {
    const changelogEntry = `
# Changelog

## [${new Date().toISOString()}]
### Added
- Initial setup of process mining application
- Flask backend with event log processing
- Frontend with D3.js visualization
- File upload and API connection interface
- Real-time data processing capabilities

### Changed
- Updated index.html with visualization sections
- Added new styles for visualization containers
- Implemented process flow visualization
- Added error handling and data processing

### Files Modified
- process.py: Added Flask backend with Llama integration
- index.html: Added visualization and analysis sections
- styles.css: Added styles for new components
- fetch.js: Added D3.js visualization and data handling
- event_log.csv: Added sample event log data
`;

    try {
        // Check if file exists, if not create it
        if (!fs.existsSync('changelog.md')) {
            fs.writeFileSync('changelog.md', '');
        }
        
        // Append new entry to changelog
        fs.appendFileSync('changelog.md', changelogEntry);
        console.log('Changelog updated successfully');
    } catch (error) {
        console.error('Error updating changelog:', error);
    }
}

// Call the function to update changelog
updateChangelog();

