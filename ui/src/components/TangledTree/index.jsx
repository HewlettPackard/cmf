// Old code not using anymore, but keeping it here for 
// reference in case we want to use it in the future. 

// import React, { useEffect, useRef, useState } from "react";
// import * as d3 from "d3";
// import _ from "lodash";

// let tangled_width;
// let tangled_height;

// const constructTangleLayout = (levels, options = {}) => {
//   // The layout calculation logic remains the same
//   levels.forEach((l, i) => l.forEach((n) => (n.level = i)));
//   var nodes = levels.reduce((a, x) => a.concat(x), []);
//   var nodes_index = {};
//   nodes.forEach((d) => (nodes_index[d.id] = d));

//   nodes.forEach((d) => {
//     d.parents = (d.parents === undefined ? [] : d.parents).map(
//       (p) => nodes_index[p],
//     );
//   });

//   levels.forEach((l, i) => {
//     var index = {};
//     l.forEach((n) => {
//       if (n.parents.length === 0) {
//         return;
//       }

//       var id = n.parents
//         .map((d) => d.id)
//         .sort()
//         .join("-X-");
//       if (id in index) {
//         index[id].parents = index[id].parents.concat(n.parents);
//       } else {
//         index[id] = {
//           id: id,
//           parents: n.parents.slice(),
//           level: i,
//           span: i - d3.min(n.parents, (p) => p.level),
//         };
//       }
//       n.bundle = index[id];
//     });
//     l.bundles = Object.keys(index).map((k) => index[k]);
//     l.bundles.forEach((b, i) => (b.i = i));
//   });

//   var links = [];
//   nodes.forEach((d) => {
//     d.parents.forEach((p) =>
//       links.push({ source: d, bundle: d.bundle, target: p }),
//     );
//   });

//   var bundles = levels.reduce((a, x) => a.concat(x.bundles), []);

//   bundles.forEach((b) =>
//     b.parents.forEach((p) => {
//       if (p.bundles_index === undefined) {
//         p.bundles_index = {};
//       }
//       if (!(b.id in p.bundles_index)) {
//         p.bundles_index[b.id] = [];
//       }
//       p.bundles_index[b.id].push(b);
//     }),
//   );

//   nodes.forEach((n) => {
//     if (n.bundles_index !== undefined) {
//       n.bundles = Object.keys(n.bundles_index).map((k) => n.bundles_index[k]);
//     } else {
//       n.bundles_index = {};
//       n.bundles = [];
//     }
//     n.bundles.sort((a, b) =>
//       d3.descending(
//         d3.max(a, (d) => d.span),
//         d3.max(b, (d) => d.span),
//       ),
//     );
//     n.bundles.forEach((b, i) => (b.i = i));
//   });

//   links.forEach((l) => {
//     if (l.bundle.links === undefined) {
//       l.bundle.links = [];
//     }
//     l.bundle.links.push(l);
//   });

//   const padding = 8;
//   const node_height = 22;
//   const node_width = 70;
//   const bundle_width = 14;
//   const level_y_padding = 16;
//   const metro_d = 4;
//   const min_family_height = 22;

//   options.c ||= 16;
//   const c = options.c;
//   options.bigc ||= node_width + c;

//   nodes.forEach(
//     (n) => (n.height = (Math.max(1, n.bundles.length) - 1) * metro_d),
//   );

//   var x_offset = padding;
//   var y_offset = padding;
//   levels.forEach((l) => {
//     x_offset += l.bundles.length * bundle_width;
//     y_offset += level_y_padding;
//     l.forEach((n, i) => {
//       n.x = n.level * node_width + x_offset;
//       n.y = node_height + y_offset + n.height / 2;

//       y_offset += node_height + n.height;
//     });
//   });

//   var i = 0;
//   levels.forEach((l) => {
//     l.bundles.forEach((b) => {
//       b.x =
//         d3.max(b.parents, (d) => d.x) +
//         node_width +
//         (l.bundles.length - 1 - b.i) * bundle_width;
//       b.y = i * node_height;
//     });
//     i += l.length;
//   });

//   // establish the basic structure and position
//   links.forEach((l) => {
//     l.xt = l.target.x;
//     l.yt =
//       l.target.y +
//       l.target.bundles_index[l.bundle.id].i * metro_d -
//       (l.target.bundles.length * metro_d) / 2 +
//       metro_d / 2;
//     l.xb = l.bundle.x;
//     l.xs = l.source.x;
//   });

//   var y_negative_offset = 0;
//   levels.forEach((l) => {
//     y_negative_offset +=
//       -min_family_height +
//       (d3.min(l.bundles, (b) =>
//         d3.min(b.links, (link) => link.ys - 2 * c - (link.yt + c)),
//       ) || 0);
//     l.forEach((n) => (n.y -= y_negative_offset));
//   });

//   // Fine tune the visual appearance of link (how the links need to display in svg)
//   links.forEach((l) => {
//     l.yt =
//       l.target.y +
//       l.target.bundles_index[l.bundle.id].i * metro_d -
//       (l.target.bundles.length * metro_d) / 2 +
//       metro_d / 2;
//     l.ys = l.source.y;
//     l.c1 = c;
//     l.c2 = c;
//   });

//   var layout = {
//     width: d3.max(nodes, (n) => n.x) + node_width + 2 * padding,
//     height: d3.max(nodes, (n) => n.y) + node_height / 2 + 2 * padding,
//     node_height,
//     node_width,
//     bundle_width,
//     level_y_padding,
//     metro_d,
//   };
//   return { levels, nodes, nodes_index, links, bundles, layout };
// };

// const renderChart = (data, options = {}) => {
//   options.color ||= (d, i) => options.color(i); // Default color function
//   options.background_color ||= "white"; // Default background color

//   const tangleLayout = constructTangleLayout(_.cloneDeep(data), options);

//   tangled_width = tangleLayout.layout.width;
//   tangled_height = tangleLayout.layout.height;
//   const textPadding = 12;
//   const labelOffset = 4;
//   const svg_width =
//     tangled_width + textPadding * 10 < 1000
//       ? `${tangled_width + textPadding * 50}`
//       : `${tangled_width + textPadding * 10}`;
//   return (
//     <>
//       <style>
//         {`
//           text {
//             font-family: sans-serif;
//             font-size: 10px;
//           }
//           .node {
//             stroke-linecap: round;
//           }
//           .link {
//             fill: none;
//           }
//         `}
//       </style>
//       <svg width={svg_width} height={tangled_height + textPadding * 10}>
//         {tangleLayout.bundles.map((b, i) => {
//           let d = b.links
//             .map(
//               (l) => `
//               M${l.xt + textPadding} ${l.yt + textPadding}
//               L${l.xb - l.c1 + textPadding} ${l.yt + textPadding}
//               A${l.c1} ${l.c1} 90 0 1 ${l.xb + textPadding} ${l.yt + l.c1 + textPadding}
//               L${l.xb + textPadding} ${l.ys - l.c2 + textPadding}
//               A${l.c2} ${l.c2} 90 0 0 ${l.xb + l.c2 + textPadding} ${l.ys + textPadding}
//               L${l.xs + textPadding} ${l.ys + textPadding}`,
//             )
//             .join("");
//           return (
//             <React.Fragment key={b.id}>
//               <path
//                 className="link"
//                 d={d}
//                 stroke={options.background_color}
//                 strokeWidth="5"
//               />
//               <path
//                 className="link"
//                 d={d}
//                 stroke={options.color(b, i)}
//                 strokeWidth="2"
//               />
//             </React.Fragment>
//           );
//         })}
//         {tangleLayout.nodes.map((n) => (
//           <React.Fragment key={n.id}>
//             <path
//               className="selectable node"
//               data-id={n.id}
//               stroke="black"
//               strokeWidth="8"
//               d={`M${n.x + textPadding} ${n.y - n.height / 2 + textPadding} L${n.x + textPadding} ${n.y + n.height / 2 + textPadding}`}
//             />
//             <path
//               className="node"
//               stroke="white"
//               strokeWidth="4"
//               d={`M${n.x + textPadding} ${n.y - n.height / 2 + textPadding} L${n.x + textPadding} ${n.y + n.height / 2 + textPadding}`}
//             />
//             <text
//               className="selectable"
//               data-id={n.id}
//               x={n.x + labelOffset + textPadding}
//               y={n.y - n.height / 2 - labelOffset + textPadding}
//               stroke={options.background_color}
//               strokeWidth="2"
//             >
//               {n.id}
//             </text>

//             <text
//               x={n.x + labelOffset + textPadding}
//               y={n.y - n.height / 2 - labelOffset + textPadding}
//               style={{ pointerEvents: "none" }}
//             >
//               {n.id}
//             </text>
//           </React.Fragment>
//         ))}
//       </svg>
//     </>
//   );
// };

// const TangledTree = ({ data }) => {
//   const chartContainerRef = useRef(null);
//   const [chart, setChart] = useState(null);
//   useEffect(() => {
//     if (!data) {
//       // Data is not yet available
//       return;
//     }
//     const options = {
//       color: d3.scaleOrdinal(d3.schemeDark2), // Use provided color scale
//       background_color: "white", // Provided background color
//     };
//     const renderedChart = renderChart(data, options);
//     setChart(renderedChart);
//   }, [data]);

//   return (
//     <div
//       ref={chartContainerRef}
//       style={{
//         justifyContent: "center",
//         alignItems: "center",
//         overflow: "auto",
//       }}
//     >
//       {chart}
//     </div>
//   );
// };

// export default TangledTree;
