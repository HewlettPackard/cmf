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

import React, { useState, useEffect } from "react";

const ResizableSplitPane = ({ leftContent, rightContent, initialSplitPercentage = 50 }) => {
  const [splitPercentage, setSplitPercentage] = useState(initialSplitPercentage);
  const [isDragging, setIsDragging] = useState(false);
  const [containerRef, setContainerRef] = useState(null);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !containerRef) return;

    const containerRect = containerRef.getBoundingClientRect();
    const newPercentage = ((e.clientX - containerRect.left) / containerRect.width) * 100;

    // Limit between 20% and 80%
    const clampedPercentage = Math.max(20, Math.min(80, newPercentage));
    setSplitPercentage(clampedPercentage);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);

  return (
    <div ref={setContainerRef} className="flex h-full w-full">
      {/* Left Pane */}
      <div style={{ width: `${splitPercentage}%` }} className="overflow-auto">
        {leftContent}
      </div>

      {/* Resizer */}
      <div
        className={`w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex-shrink-0 ${
          isDragging ? 'bg-gray-400' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-0.5 h-8 bg-gray-500"></div>
        </div>
      </div>

      {/* Right Pane */}
      <div style={{ width: `${100 - splitPercentage}%` }} className="overflow-auto">
        {rightContent}
      </div>
    </div>
  );
};

export default ResizableSplitPane;
