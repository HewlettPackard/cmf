/***
 * Copyright (2025) Hewlett Packard Enterprise Development LP
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

import React, { useState, useEffect, useRef, useCallback } from "react";

const ResizableSplitPane = ({ 
  leftContent, 
  rightContent, 
  initialSplitPercentage = 50,
  minPercentage = 20,
  maxPercentage = 80,
  onResize = null
}) => {
  const [splitPercentage, setSplitPercentage] = useState(initialSplitPercentage);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const rafRef = useRef(null);

  // Helper to calculate percentage from client position
  const calculatePercentage = useCallback((clientX) => {
    if (!containerRef.current) return splitPercentage;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const newPercentage = ((clientX - containerRect.left) / containerRect.width) * 100;
    return Math.max(minPercentage, Math.min(maxPercentage, newPercentage));
  }, [minPercentage, maxPercentage, splitPercentage]);

  // Update split percentage with requestAnimationFrame for smooth performance
  const updateSplitPercentage = useCallback((newPercentage) => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    
    rafRef.current = requestAnimationFrame(() => {
      setSplitPercentage(newPercentage);
      if (onResize) {
        onResize(newPercentage);
      }
    });
  }, [onResize]);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    const newPercentage = calculatePercentage(e.clientX);
    updateSplitPercentage(newPercentage);
  }, [isDragging, calculatePercentage, updateSplitPercentage]);

  const handleTouchMove = useCallback((e) => {
    if (!isDragging || !e.touches.length) return;
    const touch = e.touches[0];
    const newPercentage = calculatePercentage(touch.clientX);
    updateSplitPercentage(newPercentage);
  }, [isDragging, calculatePercentage, updateSplitPercentage]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    e.preventDefault();
  };

  const handleTouchStart = (e) => {
    setIsDragging(true);
    e.preventDefault();
  };

  const handleKeyDown = (e) => {
    const step = e.shiftKey ? 5 : 1; // Hold shift for larger steps
    
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const newPercentage = Math.max(minPercentage, splitPercentage - step);
      setSplitPercentage(newPercentage);
      if (onResize) {
        onResize(newPercentage);
      }
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      const newPercentage = Math.min(maxPercentage, splitPercentage + step);
      setSplitPercentage(newPercentage);
      if (onResize) {
        onResize(newPercentage);
      }
    } else if (e.key === 'Home') {
      e.preventDefault();
      setSplitPercentage(minPercentage);
      if (onResize) {
        onResize(minPercentage);
      }
    } else if (e.key === 'End') {
      e.preventDefault();
      setSplitPercentage(maxPercentage);
      if (onResize) {
        onResize(maxPercentage);
      }
    }
  };

  useEffect(() => {
    if (!isDragging) return;

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleMouseUp);
      
      // Cancel any pending animation frames
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isDragging, handleMouseMove, handleTouchMove, handleMouseUp]);

  return (
    <div ref={containerRef} className="flex h-full w-full">
      {/* Left Pane */}
      <div 
        style={{ width: `${splitPercentage}%` }} 
        className="overflow-auto"
        aria-label="Left panel"
      >
        {leftContent}
      </div>

      {/* Resizer */}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-valuenow={Math.round(splitPercentage)}
        aria-valuemin={minPercentage}
        aria-valuemax={maxPercentage}
        aria-label="Resize panels. Use arrow keys to adjust, Shift+Arrow for larger steps, Home/End for min/max"
        tabIndex={0}
        className={`w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex-shrink-0 transition-colors ${
          isDragging ? 'bg-gray-400' : ''
        }`}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onKeyDown={handleKeyDown}
      >
        <div className="w-full h-full flex items-center justify-center pointer-events-none">
          <div className="w-0.5 h-8 bg-gray-500"></div>
        </div>
      </div>

      {/* Right Pane */}
      <div 
        style={{ width: `${100 - splitPercentage}%` }} 
        className="overflow-auto"
        aria-label="Right panel"
      >
        {rightContent}
      </div>
    </div>
  );
};

export default ResizableSplitPane;
