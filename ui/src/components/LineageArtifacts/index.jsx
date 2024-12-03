import React, { useEffect, useState } from "react";
import * as d3 from "d3";
import "./index.css"; // Adjust the path if needed

const LineageArtifacts = ({ data }) => {
  // eslint-disable-next-line no-unused-vars
  const [jsondata, setJsonData] = useState(null);

  function darkenColor(color, factor) {
    // Convert color to d3 color
    let d3Color = d3.color(color);
    // Darken the color
    d3Color = d3Color.darker(factor);
    // Return the color string
    return d3Color.toString();
  }

  useEffect(() => {
    setJsonData(data);
    if (!jsondata) {
      // Data is not yet available
      return;
    }
    jsondata.nodes.forEach((node) => {
      const hasIncomingLinks = jsondata.links.some(
        (link) => link.target === node.id,
      );
      if (!hasIncomingLinks) {
        // Set initial x position for nodes with no parents
        node.x = 100; // Adjust the value based on your preference
      }
    });

    var width = window.innerWidth;
    var height = window.innerHeight;
    const links = jsondata.links.map((d) => ({ ...d }));
    const nodes = jsondata.nodes.map((d) => ({ ...d }));

    var svg = d3
      .select("#chart-container")
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    const g = svg.append("g");

    var simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(350),
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(50));

    g.append("defs")
      .selectAll("marker")
      .data(["arrow"])
      .enter()
      .append("marker")
      .attr("id", (d) => d)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 50)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "gray");

    var link = g
      .selectAll(".link")
      .data(links)
      .enter()
      .append("line")
      .attr("marker-end", "url(#arrow)")
      .style("stroke", "gray")
      .style("stroke-width", 1);

    var node = g
      .selectAll(".node")
      .data(nodes)
      .attr("class", "node")
      .enter()
      .append("g")
      // Set the stroke color as a slightly darker version of the fill color

      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended),
      );

    node
      .append("rect")
      .attr("width", 60)
      .attr("height", 30)
      .attr("rx", 10)
      .attr("ry", 10)
      .attr("fill", (d) => d.color || "gray")
      .style("stroke", (d) => darkenColor(d.color || "gray", 0.4)) // Adjust 0.3 to control darkness
      .style("stroke-width", 1.5);

    node
      .append("g")
      .attr("class", "text-group")
      .on("mouseover", handleMouseOver)
      .on("mouseout", handleMouseOut)
      .append("text")
      .attr("x", 15) // Set x position to the center of the rectangle
      .attr("y", 15)
      .attr("class", "truncated-text")
      .text((d) => d.name.substring(0, 5) + "...");

    node
      .select(".text-group")
      .append("text")
      .attr("class", "full-text")
      .text((d) => d.name)
      .attr("x", 50) // Set x position to the center of the rectangle
      .attr("y", -5)
      .style("visibility", "hidden");

    function handleMouseOver(event, d) {
      d3.select(this).select(".full-text").style("visibility", "visible");
    }

    function handleMouseOut(event, d) {
      d3.select(this).select(".full-text").style("visibility", "hidden");
    }

    svg.call(
      d3
        .zoom()
        .extent([
          [0, 0],
          [width, height],
        ])
        .scaleExtent([1, 8])
        .on("zoom", zoomed),
    );

    simulation.on("tick", function () {
      link
        .attr("x1", (d) => d.source.x + 25)
        .attr("y1", (d) => d.source.y + 15)
        .attr("x2", (d) => d.target.x + 25)
        .attr("y2", (d) => d.target.y + 15);
      node.attr("transform", (d) => `translate(${d.x - 25},${d.y - 15})`);
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
      d.fx = d.x;
      d.fy = d.y;
    }

    function zoomed({ transform }) {
      g.attr("transform", transform);
    }

    return () => {
      svg.remove(); // Remove the SVG when the component is unmounted
    };
  }, [jsondata]);

  return <div id="chart-container"></div>;
};

export default LineageArtifacts;
