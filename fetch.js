fetch("http://localhost:5000/process-data")
  .then(response => response.json())
  .then(data => {
    const svg = d3.select("body").append("svg").attr("width", 800).attr("height", 600);
    
    // Example: render basic nodes
    svg.selectAll("circle")
      .data(data.steps)  // Adjust based on actual response structure
      .enter()
      .append("circle")
      .attr("cx", (d, i) => i * 100 + 50)
      .attr("cy", 100)
      .attr("r", 20)
      .attr("fill", "blue");
  });
