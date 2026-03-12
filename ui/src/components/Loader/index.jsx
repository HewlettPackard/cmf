/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

import React from "react";

const Loader = () => (
  <div className="flex flex-col items-center justify-center gap-4 py-8">
    {/* Spinner rings */}
    <div className="relative w-16 h-16">
      {/* Outer ring */}
      <div className="absolute inset-0 rounded-full border-4 border-teal-100"></div>
      {/* Spinning ring */}
      <div
        className="absolute inset-0 rounded-full border-4 border-transparent border-t-teal-500 border-r-teal-400"
        style={{ animation: "cmf-spin 0.9s linear infinite" }}
      ></div>
      {/* Inner spinning ring (opposite direction) */}
      <div
        className="absolute inset-2 rounded-full border-4 border-transparent border-b-teal-300"
        style={{ animation: "cmf-spin-reverse 1.2s linear infinite" }}
      ></div>
      {/* Center dot */}
      <div className="absolute inset-[22px] rounded-full bg-teal-500"
        style={{ animation: "cmf-pulse 1s ease-in-out infinite" }}
      ></div>
    </div>
    {/* Label */}
    <p className="text-sm font-medium text-teal-600 tracking-wide">Loading…</p>
    <style>{`
      @keyframes cmf-spin { to { transform: rotate(360deg); } }
      @keyframes cmf-spin-reverse { to { transform: rotate(-360deg); } }
      @keyframes cmf-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.7); }
      }
    `}</style>
  </div>
);

export default Loader;
