import React, { useEffect, useState } from 'react';
import * as d3 from 'd3';
import "./index.css"; // Adjust the path if needed
import runtimeEnv from "@mars/heroku-js-runtime-env";

const LineageArtifacts = ({data}) => {
  console.log(data,"lineagedata");
  // eslint-disable-next-line no-unused-vars
  const [jsondata, setJsonData] = useState(null);

  useEffect(() => {
    setJsonData(data);
    if (!jsondata) {
      // Data is not yet available
      return;
    }
    console.log(jsondata,"jsondata");
    jsondata.nodes.forEach(node => {
        const hasIncomingLinks = jsondata.links.some(link => link.target === node.id);
        if (!hasIncomingLinks) {
       // Set initial x position for nodes with no parents
            node.x = 100; // Adjust the value based on your preference
        }
    });

    var width = 1000;
    var height = 600;

    var svg = d3.select("#chart-container")
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    svg.append("defs").selectAll("marker")
      .data(["arrow"])
      .enter().append("marker")
      .attr("id", d => d)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 35)
      .attr("refY", 1)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "black");

    var simulation = d3.forceSimulation(jsondata.nodes)
      .force("link", d3.forceLink(jsondata.links).id(d => d.id).distance(250))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(50));

    var link = svg.selectAll(".link")
      .data(jsondata.links)
      .enter().append("line")
      .attr("class", "link")
      .attr("marker-end", "url(#arrow)")
      .style("stroke", "black")
      .style("stroke-width", 2);

    var node = svg.selectAll(".node")
      .data(jsondata.nodes)
      .enter().append("g")
      .attr("class", "node")
      .attr('fill', d => d.color || 'gray')
      .style("stroke", "black ") // border color
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    node.append("rect")
      .attr("width", 100)
      .attr("height", 30)
      .attr("rx", 10)
      .attr("ry", 10);

    // Commented out the code for the text inside the rectangle
    // node.append("text")
    //   .text(d => d.name)
    //   .attr("dx", 25)
    //   .attr("dy", 15)
    //   .attr("text-anchor", "middle");

    node.append("g")
      .attr("class", "text-group")
      .on("mouseover", handleMouseOver)
      .on("mouseout", handleMouseOut)
      .append("text")
      .attr("x", 40)  // Set x position to the center of the rectangle
      .attr("y", 15)
      .attr("class", "truncated-text")
      .text(d => d.name.substring(0, 5) + '...');

    node.select(".text-group")
      .append("text")
      .attr("class", "full-text")
      .text(d => d.name)
      .attr("x", 50)  // Set x position to the center of the rectangle
      .attr("y", -5)
      .style("visibility", "hidden");

    function handleMouseOver(event, d) {
      d3.select(this).select(".full-text").style("visibility", "visible");
    
    }

    function handleMouseOut(event, d) {
      d3.select(this).select(".full-text").style("visibility", "hidden");
    }

    simulation.on("tick", function () {
      link.attr("x1", d => d.source.x + 25)
        .attr("y1", d => d.source.y + 15)
        .attr("x2", d => d.target.x + 25)
        .attr("y2", d => d.target.y + 15);
      node.attr("transform", d => `translate(${d.x - 25},${d.y - 15})`);
    });

    node.transition().duration(500).attr("opacity", 1);
    link.transition().duration(500).attr("opacity", 1);

    simulation.restart();

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx =d.x;
      d.fy = d.y;
    }

    return () => {
      console.log("svg remove")
      svg.remove(); // Remove the SVG when the component is unmounted
    };

  }, [jsondata]);

  return (
    <div id="chart-container">
    </div>
  );
};

export default LineageArtifacts;
